import logging

from fastapi import APIRouter, HTTPException, Response

from backend.database import get_connection
from backend.schemas.agent import CompanyProfileCreate, CompanyProfileOut
from backend.schemas.conversation import PinnedCreate, PinnedOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/company-profile", response_model=CompanyProfileOut)
def get_company_profile():
    db = get_connection()
    try:
        row = db.execute("SELECT * FROM company_profile WHERE id = 1").fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Profil entreprise non configuré")
        return dict(row)
    finally:
        db.close()


@router.put("/company-profile", response_model=CompanyProfileOut)
def upsert_company_profile(body: CompanyProfileCreate):
    db = get_connection()
    try:
        db.execute(
            """INSERT OR REPLACE INTO company_profile (id, name, sector, tone, business_rules, updated_at)
               VALUES (1, ?, ?, ?, ?, datetime('now'))""",
            (body.name, body.sector, body.tone, body.business_rules),
        )
        db.commit()
        row = db.execute("SELECT * FROM company_profile WHERE id = 1").fetchone()
        return dict(row)
    finally:
        db.close()


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
            """SELECT id, content, source, created_at FROM pinned_context
               WHERE conversation_id = ? AND is_active = 1
               ORDER BY created_at ASC""",
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
            """INSERT INTO pinned_context (conversation_id, content, source, is_active)
               VALUES (?, ?, 'user', 1)""",
            (conversation_id, content),
        )
        db.commit()
        row = db.execute(
            "SELECT id, content, source, created_at FROM pinned_context WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return dict(row)
    finally:
        db.close()


@router.delete("/pinned/{pinned_id}", status_code=204)
def delete_pinned(pinned_id: int):
    db = get_connection()
    try:
        existing = db.execute(
            "SELECT id FROM pinned_context WHERE id = ?", (pinned_id,)
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
