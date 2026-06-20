import logging

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

        routing = await boss_service.run_routing(job_id, db)
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
            agent_output = await agent_analyste.run(job_id, task, db)

        elif agent_code == "REDACTEUR":
            db.execute(
                "UPDATE jobs SET status = 'AGENT_RUNNING', updated_at = datetime('now') WHERE id = ?",
                (job_id,),
            )
            db.commit()
            logger.info("Job %d status=AGENT_RUNNING agent=REDACTEUR", job_id)
            agent_output = await agent_redacteur.run(job_id, task, db)

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
