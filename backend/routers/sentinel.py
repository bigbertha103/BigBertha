import json
import logging

from fastapi import APIRouter, HTTPException

from backend.database import get_connection
from backend.services import sentinel_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ── POST /api/sentinel/analyze ────────────────────────────────────

@router.post("/sentinel/analyze")
async def analyze(db=None):
    db = get_connection()
    try:
        report = await sentinel_service.run_analysis(db)
        return report
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error("Erreur analyse SENTINEL : %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur SENTINEL : {exc}")
    finally:
        db.close()


# ── GET /api/sentinel/reports ─────────────────────────────────────

@router.get("/sentinel/reports")
def list_reports():
    db = get_connection()
    try:
        rows = db.execute(
            "SELECT * FROM sentinel_reports ORDER BY created_at DESC"
        ).fetchall()

        result = []
        for r in rows:
            pending = db.execute(
                "SELECT COUNT(*) FROM learning_proposals "
                "WHERE sentinel_report_id = ? AND status = 'PENDING'",
                (r["id"],),
            ).fetchone()[0]

            try:
                metrics = json.loads(r["metrics"] or "{}")
            except (json.JSONDecodeError, TypeError):
                metrics = {}

            try:
                observations = json.loads(r["observations"] or "[]")
            except (json.JSONDecodeError, TypeError):
                observations = []

            result.append({
                "id": r["id"],
                "is_baseline": bool(r["is_baseline"]),
                "score": r["score"],
                "metrics": metrics,
                "observations": observations,
                "jobs_analyzed": r["jobs_analyzed"],
                "created_at": r["created_at"],
                "pending_proposals": pending,
            })

        return result
    finally:
        db.close()
