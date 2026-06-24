import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path

import anyio
from fastapi import APIRouter, HTTPException, UploadFile

from backend.database import get_config_value, get_connection
from backend.services.rag_engine import RAGManager, get_rag, init_rag

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".doc", ".py"}


def _get_rag_for_session() -> RAGManager:
    session_id_str = get_config_value("active_test_session_id", "")
    if session_id_str:
        db = get_connection()
        try:
            row = db.execute(
                "SELECT chroma_collection FROM test_sessions WHERE id = ?",
                (int(session_id_str),),
            ).fetchone()
        finally:
            db.close()
        if row:
            persist_dir = os.getenv("RAG_PERSIST_DIR", "backend/data/chroma_db")
            model = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            return RAGManager(
                collection_name=row["chroma_collection"],
                persist_dir=persist_dir,
                embedding_model=model,
            )
    rag = get_rag()
    if rag is None:
        raise HTTPException(
            status_code=503,
            detail="Le moteur RAG n'est pas disponible. Redémarrez le serveur.",
        )
    return rag


# ── Route 1 — POST /api/knowledge/import ──────────────────────────

@router.post("/knowledge/import")
async def import_documents(files: list[UploadFile]):
    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    session_id_str = get_config_value("active_test_session_id", "")
    active_session_id = int(session_id_str) if session_id_str else None

    results = []

    for file in files:
        filename = file.filename or "unknown"
        suffix = Path(filename).suffix.lower()

        if suffix not in ALLOWED_EXTENSIONS:
            results.append({
                "filename": filename,
                "status": "ERROR",
                "chunk_count": 0,
                "error": f"Extension non supportée : {suffix}. Acceptées : {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            })
            continue

        content = await file.read()
        content_hash = hashlib.sha256(content).hexdigest()

        db = get_connection()
        try:
            existing = db.execute(
                "SELECT id, is_active FROM knowledge_documents WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
            if existing:
                if existing["is_active"] == 1:
                    results.append({
                        "filename": filename,
                        "status": "DUPLICATE",
                        "chunk_count": 0,
                        "error": None,
                    })
                    continue
                # Doc précédemment archivé (is_active=0) — supprimer l'entrée pour permettre la réinsertion
                db.execute("DELETE FROM knowledge_documents WHERE id = ?", (existing["id"],))
                db.commit()

            cur = db.execute(
                """INSERT INTO knowledge_documents
                   (filename, file_type, content_hash, status, test_session_id)
                   VALUES (?, ?, ?, 'PROCESSING', ?)""",
                (filename, suffix.lstrip("."), content_hash, active_session_id),
            )
            doc_id = cur.lastrowid
            db.commit()
        finally:
            db.close()

        tmp_path = None
        try:
            suffix_clean = suffix if suffix else ".tmp"
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix_clean, prefix="bb_rag_"
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            rag = _get_rag_for_session()

            metadata = {}
            if active_session_id:
                metadata["test_session_id"] = str(active_session_id)

            chunk_ids = await anyio.to_thread.run_sync(
                lambda: rag.add_document(tmp_path, metadata=metadata)
            )

            db = get_connection()
            try:
                db.execute(
                    """UPDATE knowledge_documents
                       SET status='INDEXED', chroma_doc_ids=?, chunk_count=?
                       WHERE id=?""",
                    (json.dumps(chunk_ids), len(chunk_ids), doc_id),
                )
                db.commit()
            finally:
                db.close()

            results.append({
                "filename": filename,
                "status": "INDEXED",
                "chunk_count": len(chunk_ids),
                "error": None,
            })
            logger.info("Import réussi : %s (%d chunks)", filename, len(chunk_ids))

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Erreur import %s : %s", filename, exc)
            db = get_connection()
            try:
                db.execute(
                    "UPDATE knowledge_documents SET status='ERROR', error_message=? WHERE id=?",
                    (str(exc), doc_id),
                )
                db.commit()
            finally:
                db.close()
            results.append({
                "filename": filename,
                "status": "ERROR",
                "chunk_count": 0,
                "error": str(exc),
            })
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()

    return results


# ── Route 2 — GET /api/knowledge/documents ────────────────────────

@router.get("/knowledge/documents")
def list_documents(session_id: int | None = None):
    db = get_connection()
    try:
        if session_id is not None:
            rows = db.execute(
                """SELECT id, filename, file_type, chunk_count, status, simulated_date, created_at
                   FROM knowledge_documents
                   WHERE is_active = 1 AND test_session_id = ?
                   ORDER BY created_at DESC""",
                (session_id,),
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT id, filename, file_type, chunk_count, status, simulated_date, created_at
                   FROM knowledge_documents
                   WHERE is_active = 1
                   ORDER BY created_at DESC""",
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


# ── Route 3 — DELETE /api/knowledge/documents/{id} ───────────────

@router.delete("/knowledge/documents/{doc_id}")
async def delete_document(doc_id: int):
    db = get_connection()
    try:
        row = db.execute(
            "SELECT chroma_doc_ids FROM knowledge_documents WHERE id = ? AND is_active = 1",
            (doc_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Document introuvable")

        chunk_ids: list[str] = json.loads(row["chroma_doc_ids"] or "[]")
    finally:
        db.close()

    if chunk_ids:
        try:
            rag = _get_rag_for_session()
            await anyio.to_thread.run_sync(lambda: rag.delete_document(chunk_ids))
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Erreur suppression ChromaDB doc %d : %s", doc_id, exc)

    db = get_connection()
    try:
        db.execute(
            "UPDATE knowledge_documents SET is_active = 0 WHERE id = ?", (doc_id,)
        )
        db.commit()
    finally:
        db.close()

    return {"deleted": True}


# ── Route 4 — GET /api/knowledge/search ──────────────────────────

@router.get("/knowledge/search")
async def search_documents(q: str, top_k: int = 3):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Paramètre q requis.")

    rag = _get_rag_for_session()
    results = await anyio.to_thread.run_sync(lambda: rag.search(q, top_k))
    return results


# ── Route 5 — GET /api/knowledge/stats ───────────────────────────

@router.get("/knowledge/stats")
def knowledge_stats():
    db = get_connection()
    try:
        doc_count = db.execute(
            "SELECT COUNT(*) FROM knowledge_documents WHERE is_active=1 AND status='INDEXED'"
        ).fetchone()[0]
        chunk_row = db.execute(
            "SELECT SUM(chunk_count) FROM knowledge_documents WHERE is_active=1"
        ).fetchone()
        chunk_count = chunk_row[0] or 0
        error_count = db.execute(
            "SELECT COUNT(*) FROM knowledge_documents WHERE is_active=1 AND status='ERROR'"
        ).fetchone()[0]
        return {
            "doc_count": doc_count,
            "chunk_count": chunk_count,
            "error_count": error_count,
        }
    finally:
        db.close()
