import logging
import time
import sqlite3

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def call_llm(
    system_prompt: str,
    messages: list[dict],
    model_id: str,
    api_key: str,
) -> dict:
    if not api_key or not api_key.strip():
        raise RuntimeError(
            "Clé API OpenRouter manquante. Configurez-la dans Paramètres → Clé API."
        )

    payload = {
        "model": model_id,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://bigbertha.local",
        "X-Title": "Big Bertha",
    }

    start = time.monotonic()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)

    duration_ms = int((time.monotonic() - start) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(
            f"OpenRouter erreur {resp.status_code} : {resp.text[:500]}"
        )

    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"OpenRouter erreur API : {data['error']}")

    choice = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cost_usd = data.get("usage", {}).get("cost", None)
    model_name = data.get("model", model_id)

    logger.info(
        "LLM call model=%s in=%d out=%d dur=%dms",
        model_name,
        input_tokens,
        output_tokens,
        duration_ms,
    )

    return {
        "content": choice,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "cost_usd": cost_usd,
        "model_name": model_name,
    }


def log_decision(
    db: sqlite3.Connection,
    job_id: int,
    conversation_id: int,
    phase: str,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    cost_usd: float | None = None,
    agent_id: int | None = None,
) -> None:
    db.execute(
        """INSERT INTO model_decision_log
           (job_id, conversation_id, phase, agent_id, model_name,
            input_tokens, output_tokens, duration_ms, cost_usd)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            job_id,
            conversation_id,
            phase,
            agent_id,
            model_name,
            input_tokens,
            output_tokens,
            duration_ms,
            cost_usd,
        ),
    )
    db.commit()
