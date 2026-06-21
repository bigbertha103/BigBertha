import json
import logging
import sqlite3

from backend.database import load_config
from backend.services import model_router

logger = logging.getLogger(__name__)

VALID_PROPOSAL_TYPES = {"UPDATE_AGENT_PROMPT", "UPDATE_COMPANY_RULE", "ARCHIVE_DOCUMENT"}

SENTINEL_PROMPT = """Tu es le SENTINEL de Big Bertha, un agent d'analyse
chargé d'évaluer la qualité et la progression de l'équipe IA au service
de l'entreprise cliente.

## Profil de l'entreprise
{PROFIL_ENTREPRISE}

## Rapport baseline (état initial — référence absolue)
{BASELINE_REPORT}

## Rapport précédent
{PREVIOUS_REPORT}

## Données d'analyse

### Derniers jobs ({JOB_COUNT} jobs analysés)
{JOBS_SUMMARY}

### Statistiques base de connaissance
{KB_STATS}

## Ta mission

Analyse l'évolution de la qualité de l'équipe depuis le baseline.
Produis un rapport d'évaluation structuré et des propositions d'amélioration
concrètes et applicables.

Règles pour les proposals :
- Uniquement 3 types autorisés : UPDATE_AGENT_PROMPT, UPDATE_COMPANY_RULE, ARCHIVE_DOCUMENT
- UPDATE_AGENT_PROMPT : target = code exact de l'agent (ANALYSTE ou REDACTEUR), fournir le system_prompt COMPLET dans content (pas un diff)
- UPDATE_COMPANY_RULE : fournir les business_rules COMPLÈTES dans content
- ARCHIVE_DOCUMENT : target = id du document en string (entier), content = raison de l'archivage
- Maximum 3 proposals par rapport. 0 si rien ne le justifie.
- Ne proposer que ce que les données observées justifient clairement.

IMPORTANT : Les valeurs numériques dans l'exemple ci-dessous sont fictives et illustrent uniquement la structure JSON attendue.
Tu dois calculer tes propres valeurs en analysant les données réelles fournies dans ce prompt.
Ne reproduis jamais les valeurs de l'exemple — produis des valeurs qui reflètent ce que tu observes réellement dans les jobs et la KB.

Format de sortie (structure uniquement — calculer toutes les valeurs à partir des données réelles) :
{
  "score": 45,
  "metrics": {
    "routing_coherence": 0.60,
    "pinned_rate": 0.20,
    "boss_direct_rate": 0.35,
    "kb_citation_rate": 0.40
  },
  "observations": [
    "Premier constat concret basé sur les jobs analysés — décrire ce que les données révèlent réellement.",
    "Deuxième constat concret basé sur les données — décrire un constat différent du premier."
  ],
  "delta_vs_baseline": {
    "score_delta": 5,
    "routing_coherence_delta": 0.05,
    "summary": "Synthèse de l'évolution observée depuis le baseline, basée sur les données réelles."
  },
  "proposals": [
    {
      "proposal_type": "UPDATE_AGENT_PROMPT",
      "target": "ANALYSTE",
      "content": "System prompt complet et réel de l'agent ici — pas un placeholder.",
      "rationale": "Justification basée sur les observations réelles des jobs analysés.",
      "previous_value": null
    }
  ]
}

Note : "delta_vs_baseline" doit être null si ce rapport est lui-même le baseline.
"""


def _build_profil_entreprise(db: sqlite3.Connection) -> str:
    row = db.execute("SELECT * FROM company_profile WHERE id = 1").fetchone()
    if row is None:
        return "Profil entreprise non configuré."
    parts = [f"Nom : {row['name']}"]
    if row["sector"]:
        parts.append(f"Secteur : {row['sector']}")
    if row["tone"]:
        parts.append(f"Ton : {row['tone']}")
    if row["business_rules"]:
        parts.append(f"Règles métier :\n{row['business_rules']}")
    return "\n".join(parts)


def _build_jobs_summary(db: sqlite3.Connection) -> tuple[str, int]:
    rows = db.execute(
        """SELECT j.id, j.routing_output, j.agent_input, j.agent_output,
                  j.final_response,
                  COUNT(pc.id) as pinned_count
           FROM jobs j
           LEFT JOIN pinned_context pc ON pc.job_id = j.id AND pc.is_active = 1
           WHERE j.status = 'DONE'
           GROUP BY j.id
           ORDER BY j.id DESC
           LIMIT 50"""
    ).fetchall()

    if not rows:
        return "(aucun job DONE disponible)", 0

    lines = []
    for r in rows:
        routing = {}
        try:
            routing = json.loads(r["routing_output"] or "{}")
        except (json.JSONDecodeError, TypeError):
            pass
        agent_code = routing.get("agent_code", "?")
        task = (r["agent_input"] or "")[:150]
        response = (r["final_response"] or "")[:200]
        pinned = r["pinned_count"]
        lines.append(
            f"Job #{r['id']} | Agent: {agent_code} | Pinned: {pinned}\n"
            f"Tâche: {task}\n"
            f"Réponse: {response}"
        )

    return "\n\n".join(lines), len(rows)


def _build_kb_stats(db: sqlite3.Connection) -> str:
    doc_count = db.execute(
        "SELECT COUNT(*) FROM knowledge_documents WHERE is_active=1 AND status='INDEXED'"
    ).fetchone()[0]
    chunk_row = db.execute(
        "SELECT SUM(chunk_count) FROM knowledge_documents WHERE is_active=1"
    ).fetchone()
    chunk_count = chunk_row[0] or 0
    return f"Documents indexés : {doc_count} | Chunks total : {chunk_count}"


def _format_report_for_prompt(row) -> str:
    if row is None:
        return "(aucun)"
    try:
        obs = json.loads(row["observations"] or "[]")
        metrics = json.loads(row["metrics"] or "{}")
        obs_text = "; ".join(obs[:3]) if obs else "(aucune)"
        metrics_text = ", ".join(f"{k}={v}" for k, v in list(metrics.items())[:4])
        return (
            f"Score: {row['score']} | Métriques: {metrics_text}\n"
            f"Observations: {obs_text}"
        )
    except Exception:
        return f"Score: {row['score']}"


async def run_analysis(db: sqlite3.Connection) -> dict:
    profil = _build_profil_entreprise(db)
    jobs_summary, job_count = _build_jobs_summary(db)
    kb_stats = _build_kb_stats(db)

    baseline_row = db.execute(
        "SELECT * FROM sentinel_reports WHERE is_baseline = 1 ORDER BY created_at ASC LIMIT 1"
    ).fetchone()
    previous_row = db.execute(
        "SELECT * FROM sentinel_reports WHERE is_baseline = 0 ORDER BY created_at DESC LIMIT 1"
    ).fetchone()

    is_first_run = db.execute(
        "SELECT COUNT(*) FROM sentinel_reports"
    ).fetchone()[0] == 0

    baseline_text = (
        "(aucun baseline — ce rapport sera le baseline)"
        if baseline_row is None
        else _format_report_for_prompt(baseline_row)
    )
    previous_text = (
        "(aucun rapport précédent)"
        if previous_row is None
        else _format_report_for_prompt(previous_row)
    )

    system_prompt = (
        SENTINEL_PROMPT
        .replace("{PROFIL_ENTREPRISE}", profil)
        .replace("{BASELINE_REPORT}", baseline_text)
        .replace("{PREVIOUS_REPORT}", previous_text)
        .replace("{JOB_COUNT}", str(job_count))
        .replace("{JOBS_SUMMARY}", jobs_summary)
        .replace("{KB_STATS}", kb_stats)
    )

    config = load_config()
    model_id = config.get("model_id", "anthropic/claude-sonnet-4-5")
    api_key = config.get("openrouter_api_key", "")

    result = await model_router.call_llm(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": "Produis le rapport SENTINEL."}],
        model_id=model_id,
        api_key=api_key,
        json_mode=True,
    )

    content = result["content"].strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("SENTINEL JSON invalide : %s | Contenu : %s", exc, content[:500])
        raise ValueError(f"Réponse SENTINEL non parseable : {exc}") from exc

    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else {}
    if not isinstance(parsed, dict):
        raise ValueError(f"Réponse SENTINEL inattendue — type {type(parsed).__name__} au lieu de dict")

    score = int(parsed.get("score", 0))
    metrics = parsed.get("metrics", {})
    observations = parsed.get("observations", [])
    delta = parsed.get("delta_vs_baseline", None)
    if is_first_run:
        delta = None

    raw_proposals = parsed.get("proposals", [])
    valid_proposals = []
    for p in raw_proposals[:3]:
        ptype = p.get("proposal_type", "")
        if ptype not in VALID_PROPOSAL_TYPES:
            logger.warning("SENTINEL proposal rejetée — type invalide : %s", ptype)
            continue
        target = p.get("target", "")
        if ptype == "UPDATE_AGENT_PROMPT":
            if not db.execute("SELECT id FROM agents WHERE code = ?", (target,)).fetchone():
                logger.warning("SENTINEL proposal rejetée — agent cible invalide : %s", target)
                continue
        elif ptype == "ARCHIVE_DOCUMENT":
            try:
                int(target)
            except (ValueError, TypeError):
                logger.warning("SENTINEL proposal rejetée — target ARCHIVE_DOCUMENT non entier : %s", target)
                continue
        valid_proposals.append(p)

    cur = db.execute(
        """INSERT INTO sentinel_reports
           (is_baseline, score, metrics, observations, delta_vs_baseline, jobs_analyzed)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            1 if is_first_run else 0,
            score,
            json.dumps(metrics),
            json.dumps(observations),
            json.dumps(delta) if delta is not None else None,
            job_count,
        ),
    )
    report_id = cur.lastrowid
    db.commit()

    for p in valid_proposals:
        db.execute(
            """INSERT INTO learning_proposals
               (sentinel_report_id, proposal_type, target, content, previous_value, rationale, status)
               VALUES (?, ?, ?, ?, NULL, ?, 'PENDING')""",
            (
                report_id,
                p["proposal_type"],
                p.get("target", ""),
                p.get("content", ""),
                p.get("rationale", ""),
            ),
        )
    db.commit()

    db.execute(
        "UPDATE app_config SET value='0', updated_at=datetime('now') "
        "WHERE key='sentinel_suggestion_pending'"
    )
    db.commit()

    logger.info(
        "SENTINEL rapport #%d créé — score=%d is_baseline=%s proposals=%d",
        report_id,
        score,
        is_first_run,
        len(valid_proposals),
    )

    return {
        "id": report_id,
        "is_baseline": is_first_run,
        "score": score,
        "metrics": metrics,
        "observations": observations,
        "delta_vs_baseline": delta,
        "jobs_analyzed": job_count,
        "proposals": valid_proposals,
    }
