import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()

CONFIG_WHITELIST = {"model_id", "host", "port", "openrouter_api_key"}
LOG_FILE = Path(__file__).parent.parent / "data" / "bigbertha.log"


@router.get("/config")
def get_config():
    db = get_connection()
    try:
        rows = db.execute(
            "SELECT key, value FROM app_config WHERE key IN ('model_id', 'host', 'port')"
        ).fetchall()
        return {r["key"]: r["value"] for r in rows if r["value"] is not None}
    finally:
        db.close()


@router.put("/config")
def update_config(body: dict):
    if not body:
        raise HTTPException(status_code=422, detail="Le body ne peut pas être vide")

    invalid_keys = set(body.keys()) - CONFIG_WHITELIST
    if invalid_keys:
        raise HTTPException(
            status_code=422,
            detail=f"Clés non reconnues : {', '.join(sorted(invalid_keys))}",
        )

    db = get_connection()
    try:
        updated = {}
        for key, value in body.items():
            str_value = str(value) if value is not None else None
            db.execute(
                "INSERT OR REPLACE INTO app_config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                (key, str_value),
            )
            updated[key] = str_value
        db.commit()
        return updated
    finally:
        db.close()


@router.get("/logs")
def get_logs():
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return [line.rstrip("\n") for line in lines[-50:] if line.strip()]
    except Exception as exc:
        logger.error("Lecture log impossible : %s", exc)
        return []
