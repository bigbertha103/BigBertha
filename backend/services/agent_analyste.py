import logging
import sqlite3

from backend.database import load_config
from backend.services import context_builder, model_router

logger = logging.getLogger(__name__)

AGENT_CODE = "ANALYSTE"


async def run(job_id: int, task: str, db: sqlite3.Connection) -> str:
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conversation_id = job["conversation_id"]

    config = load_config()
    model_id = config.get("model_id", "anthropic/claude-sonnet-4-5")
    api_key = config.get("openrouter_api_key", "")

    payload = context_builder.build_agent_payload(AGENT_CODE, task, db)

    result = await model_router.call_llm(
        system_prompt=payload["system"],
        messages=payload["messages"],
        model_id=model_id,
        api_key=api_key,
    )

    agent_row = db.execute("SELECT id FROM agents WHERE code = ?", (AGENT_CODE,)).fetchone()
    agent_id = agent_row["id"] if agent_row else None

    model_router.log_decision(
        db=db,
        job_id=job_id,
        conversation_id=conversation_id,
        phase="AGENT_CALL",
        model_name=result["model_name"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        duration_ms=result["duration_ms"],
        cost_usd=result["cost_usd"],
        agent_id=agent_id,
    )

    output = result["content"].strip()
    db.execute(
        "UPDATE jobs SET agent_output = ?, updated_at = datetime('now') WHERE id = ?",
        (output, job_id),
    )
    db.commit()

    logger.info("ANALYSTE job=%d terminé (%d chars)", job_id, len(output))
    return output
