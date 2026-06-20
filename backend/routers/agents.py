import logging

from fastapi import APIRouter

from backend.database import get_connection
from backend.schemas.agent import AgentOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/agents", response_model=list[AgentOut])
def list_agents():
    db = get_connection()
    try:
        rows = db.execute(
            "SELECT id, code, name, description, is_active, created_at FROM agents WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()
