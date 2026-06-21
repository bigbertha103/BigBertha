import json
import logging
import sqlite3

from backend.database import get_connection, load_config
from backend.services import context_builder, model_router

logger = logging.getLogger(__name__)

ARCHIVISTE_PROMPT = """Tu es l'ARCHIVISTE de Big Bertha. Ta mission est de produire un bilan structuré de la conversation qui vient de se terminer, afin qu'il puisse être réinjecté dans la conversation suivante.

## Profil de l'entreprise cliente

{PROFIL_ENTREPRISE}

## Ta mission

Analyse l'intégralité des messages de la conversation ci-dessous et produis un bilan synthétique. Ce bilan sera lu au début de la prochaine conversation pour donner au système tout le contexte nécessaire sans relire tous les messages.

## Format de sortie

Tu dois retourner UNIQUEMENT le JSON suivant, sans aucun texte avant ou après :

{"sujet_principal": "En une phrase : de quoi parlait cette conversation.", "decisions_prises": ["Décision 1", "Décision 2"], "informations_cles": ["Information clé 1", "Information clé 2"], "questions_ouvertes": ["Question encore en suspens 1"], "prochaine_etape": "Ce que l'utilisateur voudra probablement faire ensuite."}

- decisions_prises : liste vide [] si aucune décision actée
- questions_ouvertes : liste vide [] si tout est résolu
- prochaine_etape : chaîne vide "" si imprévisible
- Maximum 3 éléments par liste
- Aucune autre sortie n'est acceptée."""


def _build_conversation_text(conversation_id: int, db: sqlite3.Connection) -> tuple[str, int, int]:
    rows = db.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    lines = []
    total_chars = 0
    for r in rows:
        label = "Utilisateur" if r["role"] == "user" else "Big Bertha"
        lines.append(f"{label} : {r['content']}")
        total_chars += len(r["content"])
    return "\n\n".join(lines), len(rows), total_chars // 4


async def run(
    conversation_id: int,
    next_conversation_id: int | None,
    trigger_reason: str,
) -> None:
    db = get_connection()
    try:
        config = load_config()
        model_id = model_router.get_model_for_task("archiviste", config)
        api_key = config.get("openrouter_api_key", "")
        inference_mode = config.get("inference_mode", "openrouter")
        ollama_base_url = config.get("ollama_base_url", "http://localhost:11434")

        profil = context_builder._build_profil_entreprise(db)
        system = ARCHIVISTE_PROMPT.replace("{PROFIL_ENTREPRISE}", profil)

        conversation_text, messages_count, estimated_tokens = _build_conversation_text(conversation_id, db)

        result = await model_router.call_llm(
            system_prompt=system,
            messages=[{"role": "user", "content": f"Conversation à archiver :\n\n{conversation_text}"}],
            model_id=model_id,
            api_key=api_key,
            json_mode=True,
            inference_mode=inference_mode,
            ollama_base_url=ollama_base_url,
        )

        content = result["content"].strip()
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
        if content and not content.startswith("{"):
            content = "{" + content
        content = content.replace("\\_", "_")

        summary_json = None
        summary_text = None
        try:
            parsed = json.loads(content)
            summary_json = json.dumps(parsed, ensure_ascii=False)
        except Exception as exc:
            logger.warning("ARCHIVISTE JSON malformé — fallback texte brut. Erreur : %s", exc)
            summary_text = content

        db.execute(
            """INSERT INTO session_summaries
               (conversation_id, next_conversation_id, summary_json, summary_text,
                trigger_reason, messages_count, estimated_tokens)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (conversation_id, next_conversation_id, summary_json, summary_text,
             trigger_reason, messages_count, estimated_tokens),
        )
        db.commit()
        logger.info(
            "ARCHIVISTE — bilan stocké pour conversation %d (trigger=%s, %d msgs, ~%d tokens)",
            conversation_id, trigger_reason, messages_count, estimated_tokens,
        )

    except Exception as exc:
        logger.error("ARCHIVISTE erreur conversation %d : %s", conversation_id, exc, exc_info=True)
    finally:
        db.close()
