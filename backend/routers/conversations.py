import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

from backend.database import get_connection
from backend.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationPatch,
    MessageCreate,
    MessageOut,
)
from backend.services.job_runner import process_job

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/conversations", status_code=201, response_model=ConversationOut)
def create_conversation(body: ConversationCreate):
    db = get_connection()
    try:
        cur = db.execute(
            "INSERT INTO conversations (title) VALUES (?)", (body.title,)
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM conversations WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        db.close()


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations():
    db = get_connection()
    try:
        rows = db.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int):
    db = get_connection()
    try:
        row = db.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        db.execute(
            "DELETE FROM model_decision_log WHERE conversation_id = ?", (conversation_id,)
        )
        db.execute(
            "DELETE FROM pinned_context WHERE conversation_id = ?", (conversation_id,)
        )
        db.execute(
            "UPDATE messages SET job_id = NULL WHERE conversation_id = ?", (conversation_id,)
        )
        db.execute("DELETE FROM jobs WHERE conversation_id = ?", (conversation_id,))
        db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        db.commit()
        return Response(status_code=204)
    finally:
        db.close()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(conversation_id: int):
    db = get_connection()
    try:
        conv = db.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        rows = db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


@router.post("/conversations/{conversation_id}/messages", status_code=202)
async def post_message(
    conversation_id: int, body: MessageCreate, background_tasks: BackgroundTasks
):
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Le contenu du message ne peut pas être vide")

    db = get_connection()
    try:
        conv = db.execute(
            "SELECT id, status FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable")

        # Conversation archivée → créer une nouvelle et y router le message
        new_conversation_id = None
        target_conversation_id = conversation_id
        if conv["status"] == "archived":
            cur = db.execute(
                "INSERT INTO conversations (title) VALUES (?)", (None,)
            )
            db.commit()
            new_conversation_id = cur.lastrowid
            target_conversation_id = new_conversation_id

        active_job = db.execute(
            """SELECT id FROM jobs
               WHERE conversation_id = ?
                 AND status IN ('PENDING', 'ROUTING', 'AGENT_RUNNING', 'SYNTHESIZING')
               LIMIT 1""",
            (target_conversation_id,),
        ).fetchone()
        if active_job:
            raise HTTPException(
                status_code=409,
                detail="Un traitement est déjà en cours pour cette conversation."
            )

        msg_cur = db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', ?)",
            (target_conversation_id, content),
        )
        user_message_id = msg_cur.lastrowid

        job_cur = db.execute(
            "INSERT INTO jobs (conversation_id, user_message_id, status) VALUES (?, ?, 'PENDING')",
            (target_conversation_id, user_message_id),
        )
        job_id = job_cur.lastrowid

        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (target_conversation_id,),
        )
        db.commit()
    finally:
        db.close()

    background_tasks.add_task(process_job, job_id)

    result: dict = {"job_id": job_id}
    if new_conversation_id is not None:
        result["new_conversation_id"] = new_conversation_id
    return result


@router.post("/conversations/{conversation_id}/archive", status_code=200)
async def archive_conversation(conversation_id: int, background_tasks: BackgroundTasks):
    db = get_connection()
    try:
        conv = db.execute(
            "SELECT id, status FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        if conv["status"] == "archived":
            raise HTTPException(status_code=409, detail="Conversation déjà archivée")
        db.execute(
            "UPDATE conversations SET status = 'archived', updated_at = datetime('now') WHERE id = ?",
            (conversation_id,),
        )
        db.commit()
    finally:
        db.close()

    from backend.services import archiviste_service
    background_tasks.add_task(
        archiviste_service.run,
        conversation_id=conversation_id,
        next_conversation_id=None,
        trigger_reason="manual",
    )
    return {"archived": True, "conversation_id": conversation_id}


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def patch_conversation(conversation_id: int, body: ConversationPatch):
    if "title" not in body.model_fields_set:
        raise HTTPException(status_code=422, detail="Le champ 'title' est requis")

    db = get_connection()
    try:
        conv = db.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable")

        db.execute(
            "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (body.title, conversation_id),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        return dict(row)
    finally:
        db.close()
