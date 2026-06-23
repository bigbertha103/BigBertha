import asyncio
import logging
import time
import sqlite3

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_MAX_RETRIES = 3
_RETRY_BASE_WAIT = 30  # secondes


async def call_llm(
    system_prompt: str,
    messages: list[dict],
    model_id: str,
    api_key: str,
    json_mode: bool = False,
    inference_mode: str = "openrouter",
    ollama_base_url: str = "http://localhost:11434",
    max_tokens: int | None = None,
) -> dict:
    if inference_mode == "ollama":
        return await _call_ollama(
            system_prompt=system_prompt,
            messages=messages,
            model_id=model_id,
            json_mode=json_mode,
            base_url=ollama_base_url,
            max_tokens=max_tokens,
        )
    return await _call_openrouter(
        system_prompt=system_prompt,
        messages=messages,
        model_id=model_id,
        api_key=api_key,
        json_mode=json_mode,
        max_tokens=max_tokens,
    )


async def _call_ollama(
    system_prompt: str,
    messages: list[dict],
    model_id: str,
    json_mode: bool,
    base_url: str,
    max_tokens: int | None = None,
) -> dict:
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model_id,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    if max_tokens is not None:
        payload["options"] = {"num_predict": max_tokens}

    headers = {"Content-Type": "application/json"}

    start = time.monotonic()
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
    duration_ms = int((time.monotonic() - start) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama erreur {resp.status_code} : {resp.text[:500]}")

    data = resp.json()
    choice = data["message"]["content"]
    input_tokens = data.get("prompt_eval_count", 0)
    output_tokens = data.get("eval_count", 0)
    model_name = data.get("model", model_id)

    logger.info(
        "LLM call [ollama] model=%s in=%d out=%d dur=%dms",
        model_name, input_tokens, output_tokens, duration_ms,
    )

    return {
        "content": choice,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "cost_usd": None,
        "model_name": model_name,
    }


async def _call_openrouter(
    system_prompt: str,
    messages: list[dict],
    model_id: str,
    api_key: str,
    json_mode: bool,
    max_tokens: int | None = None,
) -> dict:
    if not api_key or not api_key.strip():
        raise RuntimeError(
            "Clé API OpenRouter manquante. Configurez-la dans Paramètres → Clé API."
        )

    payload = {
        "model": model_id,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://bigbertha.local",
        "X-Title": "Big Bertha",
    }

    for attempt in range(_MAX_RETRIES):
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        duration_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code == 429:
            if attempt < _MAX_RETRIES - 1:
                wait = _RETRY_BASE_WAIT * (attempt + 1)
                logger.warning(
                    "Rate limit 429 — attente %ds avant retry %d/%d",
                    wait, attempt + 2, _MAX_RETRIES,
                )
                await asyncio.sleep(wait)
                continue
            raise RuntimeError(
                f"OpenRouter erreur 429 après {_MAX_RETRIES} tentatives : {resp.text[:500]}"
            )

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
        cost_usd = usage.get("cost", None)
        model_name = data.get("model", model_id)

        logger.info(
            "LLM call [openrouter] model=%s in=%d out=%d dur=%dms",
            model_name, input_tokens, output_tokens, duration_ms,
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


def get_model_for_task(task: str, config: dict) -> str:
    """Retourne le model_id approprié selon la tâche et le mode COST/PERFORMANCE."""
    perf = config.get("perf_mode", "0") == "1"
    suffix = "perf" if perf else "cost"
    key = f"{task}_model_{suffix}"
    fallback = config.get("model_id") or "mistralai/mistral-nemo"
    return config.get(key) or fallback
