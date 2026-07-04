import json
import logging
import sqlite3

from backend.database import load_config
from backend.services import context_builder, model_router

logger = logging.getLogger(__name__)

VALID_AGENT_CODES = {"ANALYSTE", "REDACTEUR", "BOSS"}


async def run_routing(job_id: int, db: sqlite3.Connection, kb_context: str = "", session_kb_context: str = "") -> dict:
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conversation_id = job["conversation_id"]

    config = load_config()
    model_id = model_router.get_model_for_task("routing", config)
    api_key = config.get("openrouter_api_key", "")
    inference_mode = config.get("inference_mode", "openrouter")
    ollama_base_url = config.get("ollama_base_url", "http://localhost:11434")

    payload = context_builder.build_routing_payload(conversation_id, db, kb_context=kb_context, session_kb_context=session_kb_context)

    result = await model_router.call_llm(
        system_prompt=payload["system"],
        messages=payload["messages"],
        model_id=model_id,
        api_key=api_key,
        json_mode=True,
        inference_mode=inference_mode,
        ollama_base_url=ollama_base_url,
        max_tokens=300,
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
    # Protection si le modèle ne commence pas par { malgré json_mode=True
    if content and not content.startswith("{"):
        content = '{"agent_code": "' + content
    # Mistral échappe parfois les underscores en markdown : {"agent\_code": ...}
    content = content.replace("\\_", "_")

    try:
        routing = json.loads(content)
        if isinstance(routing, list):
            routing = routing[0] if routing else {}
        agent_code = routing["agent_code"]
        task = routing["task"]
        rationale = routing.get("rationale", "")
        if agent_code not in VALID_AGENT_CODES:
            raise ValueError(f"agent_code invalide : {agent_code!r}")
    except (json.JSONDecodeError, KeyError, TypeError, IndexError, ValueError) as exc:
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
    model_id = model_router.get_model_for_task("synthesis", config)
    api_key = config.get("openrouter_api_key", "")
    inference_mode = config.get("inference_mode", "openrouter")
    ollama_base_url = config.get("ollama_base_url", "http://localhost:11434")

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
        inference_mode=inference_mode,
        ollama_base_url=ollama_base_url,
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
    # Nettoie les caractères de contrôle non échappés (newlines, tabs littéraux dans les valeurs JSON)
    content = content.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n').replace('\t', '\\t')

    import re as _re

    try:
        synthesis = json.loads(content)
    except json.JSONDecodeError as exc:
        # mistral-nemo génère parfois des chars de contrôle non-échappés dans les strings JSON
        try:
            content_safe = _re.sub(
                r'[\x00-\x1f]',
                lambda m: json.dumps(m.group())[1:-1],
                content,
            )
            synthesis = json.loads(content_safe)
            logger.info("Synthesis JSON réparé (sanitisation control chars)")
        except json.JSONDecodeError:
            logger.error("Synthesis JSON invalide — fallback extraction. Erreur : %s", exc)
            # Tenter d'extraire le champ response plutôt que retourner le JSON brut
            m = _re.search(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"', content, _re.DOTALL)
            response = m.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\') if m else content
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
    if isinstance(synthesis, list):
        synthesis = synthesis[0] if synthesis else {}
    try:
        response = synthesis["response"]
        pinned = synthesis.get("pinned", [])
    except (KeyError, TypeError, AttributeError) as exc:
        logger.error("Synthesis champ 'response' manquant : %s | contenu : %s", exc, str(synthesis)[:200])
        response = str(synthesis)
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
