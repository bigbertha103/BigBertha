import json
import logging
import sqlite3
from datetime import datetime, timezone

import anyio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_STATUSES = {"PENDING", "APPROVED", "REJECTED"}


class ProposalAction(BaseModel):
    action: str  # "approve" | "reject"


# ── GET /api/learning-proposals ───────────────────────────────────

@router.get("/learning-proposals")
def list_proposals(status: str = "PENDING"):
    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Statut invalide. Valeurs acceptées : {', '.join(sorted(VALID_STATUSES))}",
        )
    db = get_connection()
    try:
        rows = db.execute(
            """SELECT lp.id, lp.sentinel_report_id, sr.created_at AS sentinel_report_date,
                      lp.proposal_type, lp.target, lp.content, lp.rationale,
                      lp.status, lp.previous_value, lp.reviewed_at, lp.created_at
               FROM learning_proposals lp
               LEFT JOIN sentinel_reports sr ON sr.id = lp.sentinel_report_id
               WHERE lp.status = ?
               ORDER BY lp.created_at DESC""",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


# ── PATCH /api/learning-proposals/{id} ───────────────────────────

@router.patch("/learning-proposals/{proposal_id}")
async def patch_proposal(proposal_id: int, body: ProposalAction):
    action = body.action
    if action not in ("approve", "reject"):
        raise HTTPException(
            status_code=400,
            detail="Action invalide. Valeurs acceptées : 'approve', 'reject'",
        )

    db = get_connection()
    try:
        row = db.execute(
            "SELECT * FROM learning_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Proposal introuvable")
        if row["status"] != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Proposal déjà traitée (statut : {row['status']})",
            )

        if action == "reject":
            db.execute(
                "UPDATE learning_proposals SET status='REJECTED', reviewed_at=datetime('now') WHERE id=?",
                (proposal_id,),
            )
            db.commit()
            return {"rejected": True}

        # ── APPROVE ───────────────────────────────────────────────
        ptype = row["proposal_type"]
        target = row["target"]
        content = row["content"]

        if ptype == "UPDATE_AGENT_PROMPT":
            agent_row = db.execute(
                "SELECT system_prompt FROM agents WHERE code = ?", (target,)
            ).fetchone()
            if agent_row is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent introuvable : {target}",
                )
            previous = agent_row["system_prompt"]
            db.execute(
                "UPDATE learning_proposals SET previous_value=? WHERE id=?",
                (previous, proposal_id),
            )
            db.execute(
                "UPDATE agents SET system_prompt=? WHERE code=?",
                (content, target),
            )
            logger.info("Proposal #%d APPROUVÉE — system_prompt agent %s mis à jour", proposal_id, target)

        elif ptype == "UPDATE_COMPANY_RULE":
            cp_row = db.execute(
                "SELECT business_rules FROM company_profile WHERE id = 1"
            ).fetchone()
            previous = cp_row["business_rules"] if cp_row else None
            db.execute(
                "UPDATE learning_proposals SET previous_value=? WHERE id=?",
                (previous, proposal_id),
            )
            db.execute(
                "UPDATE company_profile SET business_rules=? WHERE id=1",
                (content,),
            )
            logger.info("Proposal #%d APPROUVÉE — business_rules company_profile mis à jour", proposal_id)

        elif ptype == "ARCHIVE_DOCUMENT":
            try:
                target_int = int(target)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"target invalide pour ARCHIVE_DOCUMENT : {target!r} (attendu : id entier en string)",
                )

            doc_row = db.execute(
                "SELECT id, chroma_doc_ids FROM knowledge_documents WHERE id=? AND is_active=1",
                (target_int,),
            ).fetchone()
            if doc_row is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document #{target_int} introuvable ou déjà archivé",
                )

            chunk_ids: list[str] = json.loads(doc_row["chroma_doc_ids"] or "[]")
            if chunk_ids:
                from backend.services.rag_engine import get_rag
                rag = get_rag()
                if rag is None:
                    logger.warning(
                        "Proposal #%d ARCHIVE_DOCUMENT — RAG indisponible, soft-delete SQLite uniquement",
                        proposal_id,
                    )
                else:
                    try:
                        await anyio.to_thread.run_sync(lambda: rag.delete_document(chunk_ids))
                    except Exception as exc:
                        logger.warning(
                            "Proposal #%d — Erreur suppression ChromaDB (non bloquant) : %s",
                            proposal_id, exc,
                        )

            db.execute(
                "UPDATE knowledge_documents SET is_active=0 WHERE id=?",
                (target_int,),
            )
            now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            db.execute(
                "UPDATE learning_proposals SET previous_value=? WHERE id=?",
                (f"archivé le {now_str}", proposal_id),
            )
            logger.info("Proposal #%d APPROUVÉE — document #%d archivé", proposal_id, target_int)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"proposal_type non géré : {ptype}",
            )

        db.execute(
            "UPDATE learning_proposals SET status='APPROVED', reviewed_at=datetime('now') WHERE id=?",
            (proposal_id,),
        )
        db.commit()
        return {"applied": True, "proposal_type": ptype, "target": target}

    finally:
        db.close()
