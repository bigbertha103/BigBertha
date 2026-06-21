import logging
import os
import sqlite3

import anyio

from backend.database import get_connection
from backend.services import agent_analyste, agent_redacteur, boss_service

logger = logging.getLogger(__name__)


def _compute_title(content: str) -> str:
    content = content.strip()
    if len(content) < 3:
        return "Nouvelle conversation"
    if len(content) <= 60:
        return content
    truncated = content[:60]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "…"


async def _fetch_kb_context(query: str) -> str:
    from backend.services.rag_engine import get_rag
    rag = get_rag()
    if rag is None:
        return ""
    try:
        return await anyio.to_thread.run_sync(
            lambda: rag.get_context_for_query(
                query,
                top_k=int(os.getenv("RAG_TOP_K", "3"))
            )
        )
    except Exception as exc:
        logger.warning("KB context fetch échoué (non bloquant) : %s", exc)
        return ""


async def _fetch_session_memory_context(query: str) -> str:
    from backend.services.rag_engine import get_session_rag
    session_rag = get_session_rag()
    if session_rag is None:
        return ""
    try:
        return await anyio.to_thread.run_sync(
            lambda: session_rag.get_context_for_query(query, top_k=1)
        )
    except Exception as exc:
        logger.warning("Session memory context fetch échoué (non bloquant) : %s", exc)
        return ""


def _update_sentinel_signal(db: sqlite3.Connection, conversation_id: int) -> None:
    try:
        pinned_count = db.execute(
            "SELECT COUNT(*) FROM pinned_context WHERE conversation_id = ? AND is_active = 1",
            (conversation_id,),
        ).fetchone()[0]

        rows = db.execute(
            "SELECT routing_output FROM jobs WHERE status='DONE' ORDER BY id DESC LIMIT 20"
        ).fetchall()
        boss_count = sum(
            1 for r in rows
            if r["routing_output"] and '"agent_code": "BOSS"' in r["routing_output"]
        )
        boss_rate = boss_count / max(len(rows), 1)

        if pinned_count >= 8 or boss_rate > 0.40:
            db.execute(
                "UPDATE app_config SET value='1', updated_at=datetime('now') "
                "WHERE key='sentinel_suggestion_pending'"
            )
            db.commit()
    except Exception as exc:
        logger.warning("Erreur calcul signal SENTINEL : %s", exc)


def _check_handoff(db: sqlite3.Connection, conversation_id: int, config: dict) -> str | None:
    threshold_tokens = int(config.get("handoff_token_threshold", "6000"))
    threshold_msgs = int(config.get("handoff_message_fallback", "15"))

    rows = db.execute(
        "SELECT content FROM messages WHERE conversation_id = ?",
        (conversation_id,),
    ).fetchall()
    estimated_tokens = sum(len(r["content"]) for r in rows) // 4

    msg_count_user = db.execute(
        "SELECT COUNT(*) FROM messages WHERE conversation_id = ? AND role = 'user'",
        (conversation_id,),
    ).fetchone()[0]

    trigger = None
    if estimated_tokens >= threshold_tokens:
        trigger = "token_threshold"
    elif msg_count_user >= threshold_msgs:
        trigger = "message_threshold"

    if trigger:
        db.execute(
            "UPDATE conversations SET status = 'archived', updated_at = datetime('now') WHERE id = ?",
            (conversation_id,),
        )
        db.commit()
        logger.info(
            "Conversation %d archivée (trigger=%s, ~%d tokens, %d msgs user)",
            conversation_id, trigger, estimated_tokens, msg_count_user,
        )

    return trigger


async def process_job(job_id: int) -> None:
    db = get_connection()
    try:
        job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if job is None:
            logger.error("Job %d introuvable", job_id)
            return

        conversation_id = job["conversation_id"]
        user_message_id = job["user_message_id"]

        user_msg_row = db.execute(
            "SELECT content FROM messages WHERE id = ?", (user_message_id,)
        ).fetchone()
        user_message = user_msg_row["content"] if user_msg_row else ""

        db.execute(
            "UPDATE jobs SET status = 'ROUTING', updated_at = datetime('now') WHERE id = ?",
            (job_id,),
        )
        db.commit()
        logger.info("Job %d status=ROUTING", job_id)

        kb_context = await _fetch_kb_context(user_message)
        if kb_context:
            logger.info("Job %d — kb_context injecté (%d chars)", job_id, len(kb_context))

        session_kb_context = await _fetch_session_memory_context(user_message)
        if session_kb_context:
            logger.info("Job %d — session_memory context injecté (%d chars)", job_id, len(session_kb_context))

        routing = await boss_service.run_routing(job_id, db, kb_context=kb_context, session_kb_context=session_kb_context)
        agent_code = routing["agent_code"]
        task = routing["task"]

        agent_output = ""

        if agent_code == "ANALYSTE":
            db.execute(
                "UPDATE jobs SET status = 'AGENT_RUNNING', updated_at = datetime('now') WHERE id = ?",
                (job_id,),
            )
            db.commit()
            logger.info("Job %d status=AGENT_RUNNING agent=ANALYSTE", job_id)
            agent_output = await agent_analyste.run(job_id, task, db, kb_context=kb_context)

        elif agent_code == "REDACTEUR":
            db.execute(
                "UPDATE jobs SET status = 'AGENT_RUNNING', updated_at = datetime('now') WHERE id = ?",
                (job_id,),
            )
            db.commit()
            logger.info("Job %d status=AGENT_RUNNING agent=REDACTEUR", job_id)
            agent_output = await agent_redacteur.run(job_id, task, db, kb_context=kb_context)

        else:
            logger.info("Job %d — BOSS direct, pas d'agent appelé", job_id)

        db.execute(
            "UPDATE jobs SET status = 'SYNTHESIZING', updated_at = datetime('now') WHERE id = ?",
            (job_id,),
        )
        db.commit()
        logger.info("Job %d status=SYNTHESIZING", job_id)

        final_response = await boss_service.run_synthesis(
            job_id=job_id,
            user_message=user_message,
            agent_output=agent_output,
            agent_code=agent_code,
            db=db,
        )

        boss_msg = db.execute(
            """INSERT INTO messages (conversation_id, role, content, job_id)
               VALUES (?, 'boss', ?, ?)""",
            (conversation_id, final_response, job_id),
        )
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,),
        )

        db.execute(
            """UPDATE jobs SET status = 'DONE', completed_at = datetime('now'),
               updated_at = datetime('now') WHERE id = ?""",
            (job_id,),
        )
        db.commit()
        logger.info("Job %d status=DONE", job_id)

        _update_sentinel_signal(db, conversation_id)

        from backend.database import load_config as _load_config
        from backend.services import archiviste_service as _archiviste
        import asyncio as _asyncio

        _trigger = _check_handoff(db, conversation_id, _load_config())
        if _trigger:
            _asyncio.create_task(
                _archiviste.run(
                    conversation_id=conversation_id,
                    next_conversation_id=None,
                    trigger_reason=_trigger,
                )
            )

        msg_count = db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ? AND role = 'user'",
            (conversation_id,),
        ).fetchone()["cnt"]

        if msg_count == 1:
            title = _compute_title(user_message)
            db.execute(
                "UPDATE conversations SET title = ? WHERE id = ?",
                (title, conversation_id),
            )
            db.commit()
            logger.info("Conversation %d titrée : %s", conversation_id, title)

    except Exception as exc:
        logger.error("Job %d ERREUR : %s", job_id, exc, exc_info=True)
        try:
            db.execute(
                """UPDATE jobs SET status = 'ERROR', error_message = ?,
                   completed_at = datetime('now'), updated_at = datetime('now')
                   WHERE id = ?""",
                (str(exc), job_id),
            )
            db.commit()
        except Exception as db_exc:
            logger.error("Impossible d'écrire ERROR en DB : %s", db_exc)
    finally:
        db.close()
