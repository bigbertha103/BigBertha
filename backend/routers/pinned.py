import logging

from fastapi import APIRouter, HTTPException, Response

from backend.database import get_connection
from backend.schemas.pinned import PinnedCreate, PinnedOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/conversations/{conversation_id}/pinned", response_model=list[PinnedOut])
def get_pinned(conversation_id: int):
    db = get_connection()
    try:
        conv = db.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        rows = db.execute(
            "SELECT * FROM pinned_context WHERE conversation_id = ? AND is_active = 1 ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


@router.post("/conversations/{conversation_id}/pinned", status_code=201, response_model=PinnedOut)
def create_pinned(conversation_id: int, body: PinnedCreate):
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Le contenu ne peut pas être vide")
    db = get_connection()
    try:
        conv = db.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        cur = db.execute(
            "INSERT INTO pinned_context (conversation_id, content, source, is_active) VALUES (?, ?, 'user', 1)",
            (conversation_id, content),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM pinned_context WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        db.close()


@router.delete("/pinned/{pinned_id}", status_code=204)
def delete_pinned(pinned_id: int):
    db = get_connection()
    try:
        existing = db.execute(
            "SELECT id FROM pinned_context WHERE id = ? AND is_active = 1", (pinned_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Élément épinglé introuvable")
        db.execute(
            "UPDATE pinned_context SET is_active = 0 WHERE id = ?", (pinned_id,)
        )
        db.commit()
        return Response(status_code=204)
    finally:
        db.close()
