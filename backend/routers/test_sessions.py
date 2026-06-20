import json
import logging
from datetime import datetime, timezone

import anyio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import get_connection, get_config_value

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionCreate(BaseModel):
    name: str


def _session_row_to_dict(row, doc_count: int = 0) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "is_active": bool(row["is_active"]),
        "chroma_collection": row["chroma_collection"],
        "doc_count": doc_count,
        "created_at": row["created_at"],
        "ended_at": row["ended_at"],
    }


# ── POST /api/test-sessions ───────────────────────────────────────

@router.post("/test-sessions")
def create_session(body: SessionCreate):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Le nom de session ne peut pas être vide")

    ts = int(datetime.now(tz=timezone.utc).timestamp())
    collection = f"bigbertha_test_{ts}"

    db = get_connection()
    try:
        cur = db.execute(
            "INSERT INTO test_sessions (name, is_active, chroma_collection) VALUES (?, 0, ?)",
            (name, collection),
        )
        db.commit()
        session_id = cur.lastrowid
        row = db.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,)).fetchone()
        return _session_row_to_dict(row, doc_count=0)
    finally:
        db.close()


# ── GET /api/test-sessions ────────────────────────────────────────

@router.get("/test-sessions")
def list_sessions():
    db = get_connection()
    try:
        rows = db.execute(
            "SELECT * FROM test_sessions ORDER BY created_at DESC"
        ).fetchall()
        result = []
        for r in rows:
            doc_count = db.execute(
                "SELECT COUNT(*) FROM knowledge_documents WHERE test_session_id = ?",
                (r["id"],),
            ).fetchone()[0]
            result.append(_session_row_to_dict(r, doc_count))
        return result
    finally:
        db.close()


# ── GET /api/test-sessions/active ────────────────────────────────

@router.get("/test-sessions/active")
def get_active_session():
    session_id_str = get_config_value("active_test_session_id", "")
    if not session_id_str:
        return None
    try:
        session_id = int(session_id_str)
    except ValueError:
        return None

    db = get_connection()
    try:
        row = db.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return None
        doc_count = db.execute(
            "SELECT COUNT(*) FROM knowledge_documents WHERE test_session_id = ?",
            (session_id,),
        ).fetchone()[0]
        return _session_row_to_dict(row, doc_count)
    finally:
        db.close()


# ── POST /api/test-sessions/{id}/activate ────────────────────────

@router.post("/test-sessions/{session_id}/activate")
def activate_session(session_id: int):
    db = get_connection()
    try:
        row = db.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Session #{session_id} introuvable")

        active_str = get_config_value("active_test_session_id", "")
        if active_str and active_str != str(session_id):
            logger.info("Désactivation session %s avant activation session %d", active_str, session_id)

        db.execute("UPDATE test_sessions SET is_active=0")
        db.execute("UPDATE test_sessions SET is_active=1 WHERE id=?", (session_id,))
        db.execute(
            "UPDATE app_config SET value=?, updated_at=datetime('now') WHERE key='active_test_session_id'",
            (str(session_id),),
        )
        db.commit()
        logger.info("Session de test #%d activée — collection : %s", session_id, row["chroma_collection"])
        return {
            "activated": True,
            "session_id": session_id,
            "chroma_collection": row["chroma_collection"],
        }
    finally:
        db.close()


# ── POST /api/test-sessions/{id}/reset ───────────────────────────

@router.post("/test-sessions/{session_id}/reset")
async def reset_session(session_id: int):
    db = get_connection()
    try:
        row = db.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Session #{session_id} introuvable")

        doc_rows = db.execute(
            "SELECT id, chroma_doc_ids, chunk_count FROM knowledge_documents "
            "WHERE test_session_id = ? AND is_active = 1",
            (session_id,),
        ).fetchall()

        all_chunk_ids: list[str] = []
        total_chunks = 0
        for d in doc_rows:
            try:
                ids = json.loads(d["chroma_doc_ids"] or "[]")
                all_chunk_ids.extend(ids)
            except (json.JSONDecodeError, TypeError):
                pass
            total_chunks += d["chunk_count"] or 0

        chroma_collection = row["chroma_collection"]
        if chroma_collection:
            from backend.services.rag_engine import init_rag
            try:
                rag = await anyio.to_thread.run_sync(
                    lambda: init_rag(collection_name=chroma_collection)
                )
                await anyio.to_thread.run_sync(rag.delete_collection)
                logger.info("Collection ChromaDB '%s' supprimée", chroma_collection)
            except Exception as exc:
                logger.warning(
                    "Erreur suppression ChromaDB '%s' (non bloquant) : %s",
                    chroma_collection, exc,
                )

        db.execute(
            "DELETE FROM knowledge_documents WHERE test_session_id = ?",
            (session_id,),
        )
        db.execute(
            "UPDATE test_sessions SET is_active=0, ended_at=datetime('now') WHERE id=?",
            (session_id,),
        )
        db.execute(
            "UPDATE app_config SET value='', updated_at=datetime('now') "
            "WHERE key='active_test_session_id'"
        )
        db.commit()

        logger.info(
            "Session #%d réinitialisée — %d docs supprimés, %d chunks",
            session_id, len(doc_rows), total_chunks,
        )
        return {
            "reset": True,
            "docs_deleted": len(doc_rows),
            "chunks_deleted": total_chunks,
        }
    finally:
        db.close()
