import json
import logging
import sqlite3

from backend.database import load_config
from backend.services import context_builder, model_router

logger = logging.getLogger(__name__)


async def run_routing(job_id: int, db: sqlite3.Connection, kb_context: str = "") -> dict:
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conversation_id = job["conversation_id"]

    config = load_config()
    model_id = config.get("model_id", "anthropic/claude-sonnet-4-5")
    api_key = config.get("openrouter_api_key", "")

    payload = context_builder.build_routing_payload(conversation_id, db, kb_context=kb_context)

    result = await model_router.call_llm(
        system_prompt=payload["system"],
        messages=payload["messages"],
        model_id=model_id,
        api_key=api_key,
        json_mode=True,
    )

    model_router.log_decision(
        db=db,
        job_id=job_id,
        conversation_id=conversation_id,
        phase="ROUTING",
        model_name=result["model_name"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        duration_ms=result["duration_ms"],
        cost_usd=result["cost_usd"],
    )

    content = result["content"].strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
    # Reconstruction JSON si prefill { utilisé (le modèle génère la suite sans l'accolade ouvrante)
    if content and not content.startswith("{") and not content.startswith("["):
        content = "{" + content
    # Mistral échappe parfois les underscores en markdown : {"agent\_code": ...}
    content = content.replace("\\_", "_")

    try:
        routing = json.loads(content)
        if isinstance(routing, list):
            routing = routing[0] if routing else {}
        agent_code = routing["agent_code"]
        task = routing["task"]
        rationale = routing.get("rationale", "")
    except (json.JSONDecodeError, KeyError, TypeError, IndexError) as exc:
        logger.error("Routing JSON invalide — fallback BOSS. Erreur : %s | Contenu : %s", exc, content)
        routing = {
            "agent_code": "BOSS",
            "task": "Répondre directement à l'utilisateur — erreur de parsing du routing.",
            "rationale": "fallback",
        }
        agent_code = routing["agent_code"]
        task = routing["task"]
        rationale = routing["rationale"]

    agent_row = db.execute("SELECT id FROM agents WHERE code = ?", (agent_code,)).fetchone()
    selected_agent_id = agent_row["id"] if agent_row else None

    db.execute(
        """UPDATE jobs SET routing_output = ?, agent_input = ?, selected_agent_id = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (json.dumps(routing), task, selected_agent_id, job_id),
    )
    db.commit()

    return {"agent_code": agent_code, "task": task, "rationale": rationale}


async def run_synthesis(
    job_id: int,
    user_message: str,
    agent_output: str,
    agent_code: str,
    db: sqlite3.Connection,
) -> str:
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conversation_id = job["conversation_id"]

    config = load_config()
    model_id = config.get("model_id", "anthropic/claude-sonnet-4-5")
    api_key = config.get("openrouter_api_key", "")

    payload = context_builder.build_synthesis_payload(
        user_message=user_message,
        agent_output=agent_output,
        agent_code=agent_code,
        db=db,
    )

    result = await model_router.call_llm(
        system_prompt=payload["system"],
        messages=payload["messages"],
        model_id=model_id,
        api_key=api_key,
        json_mode=True,
    )

    model_router.log_decision(
        db=db,
        job_id=job_id,
        conversation_id=conversation_id,
        phase="SYNTHESIS",
        model_name=result["model_name"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        duration_ms=result["duration_ms"],
        cost_usd=result["cost_usd"],
    )

    content = result["content"].strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
    # Reconstruction JSON si prefill { utilisé
    if content and not content.startswith("{") and not content.startswith("["):
        content = "{" + content

    try:
        synthesis = json.loads(content)
        if isinstance(synthesis, list):
            synthesis = synthesis[0] if synthesis else {}
        response = synthesis["response"]
        pinned = synthesis.get("pinned", [])
    except (json.JSONDecodeError, KeyError, TypeError, IndexError) as exc:
        logger.error("Synthesis JSON invalide — utilisation réponse brute. Erreur : %s", exc)
        response = content
        pinned = []

    db.execute(
        "UPDATE jobs SET final_response = ?, updated_at = datetime('now') WHERE id = ?",
        (response, job_id),
    )

    for pin_content in pinned:
        if pin_content and isinstance(pin_content, str):
            db.execute(
                """INSERT INTO pinned_context (conversation_id, content, source, job_id, is_active)
                   VALUES (?, ?, 'boss', ?, 1)""",
                (conversation_id, pin_content, job_id),
            )

    db.commit()
    return response
