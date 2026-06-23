"""
plan_simulation.py — Génère un manifest.json de simulation à partir des fichiers d'une entreprise Samples/.

Usage :
    python tests/plan_simulation.py --company BlueCart-Retail [--mode court|moyen|long] [--auto]

Doit être lancé depuis la racine du projet.
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ── Bibliothèques doc (déjà dans requirements.txt) ─────────────────────────
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constantes ───────────────────────────────────────────────────────────────
DB_PATH = Path("backend/data/bigbertha.db")
SAMPLES_DIR = Path("Samples")
RUNS_DIR = Path("docs/Test/runs")
CHAR_LIMIT = 2500
DEFAULT_MODEL = "anthropic/claude-haiku-4-5"
MODES = {"court": 7, "moyen": 14, "long": 30}

SYSTEM_PROMPT_TEMPLATE = (
    "Tu es un planificateur de simulation d'utilisation quotidienne d'un outil IA "
    "en entreprise. Tu reçois les documents réels d'une entreprise fictive.\n\n"
    "Ta mission : générer un plan de simulation sur {N} jours qui reproduit "
    "le comportement naturel d'employés qui utilisent l'outil au quotidien — "
    "ils apportent un article trouvé en ligne, une nouvelle norme, un rapport, "
    "une procédure mise à jour, une question terrain.\n\n"
    "Règles :\n"
    "- Chaque jour : 1 à 4 fichiers + 2 à 3 messages\n"
    "- Les messages sont en français, naturels, ancrés dans le contexte métier\n"
    "- Simule un employé qui parle à son outil, pas un consultant qui fait un audit\n"
    "- Un doc peut être réutilisé sur plusieurs jours si son contenu le justifie\n"
    "- Répartis les thèmes de façon progressive (base → terrain → expertise)\n"
    "- Ne génère AUCUNE donnée fictive — base-toi uniquement sur le contenu fourni\n\n"
    "Retourne UNIQUEMENT ce JSON :\n"
    "{{\n"
    "  'days': [\n"
    "    {{\n"
    "      'day': 1,\n"
    "      'theme': 'description courte du thème du jour',\n"
    "      'documents': ['nom_exact_du_fichier.md', 'autre.pdf'],\n"
    "      'messages': ['message naturel 1', 'message naturel 2']\n"
    "    }}\n"
    "  ]\n"
    "}}"
)


# ── Étape 1 — Extraction de contenu ──────────────────────────────────────────

def _truncate(text: str, limit: int) -> str:
    """Tronque proprement à la fin d'un mot."""
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_space = truncated.rfind(" ")
    if last_space > limit // 2:
        truncated = truncated[:last_space]
    return truncated


def _read_md_txt(path: Path) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _read_pdf(path: Path) -> str:
    if pypdf is None:
        logger.warning("pypdf non disponible — %s ignoré", path.name)
        return ""
    reader = pypdf.PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _read_docx(path: Path) -> str:
    if docx is None:
        logger.warning("python-docx non disponible — %s ignoré", path.name)
        return ""
    try:
        doc = docx.Document(str(path))
    except (ValueError, Exception) as exc:
        logger.warning("Fichier Word illisible — %s ignoré (%s)", path.name, exc)
        return ""
    return "\n".join(p.text for p in doc.paragraphs)


def extract_company_files(company_dir: Path) -> dict:
    """Retourne {nom_fichier: contenu_tronqué} pour tous les fichiers du dossier."""
    contents = {}
    for path in sorted(company_dir.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext in (".md", ".txt"):
            raw = _read_md_txt(path)
        elif ext == ".pdf":
            raw = _read_pdf(path)
        elif ext in (".docx", ".doc"):
            raw = _read_docx(path)
        else:
            logger.info("Extension ignorée : %s", path.name)
            continue
        contents[path.name] = _truncate(raw.strip(), CHAR_LIMIT)
        logger.info("Lu : %s (%d car.)", path.name, len(contents[path.name]))
    return contents


# ── Étape 2 — Appel LLM ──────────────────────────────────────────────────────

def load_config_from_db() -> dict:
    """Lit openrouter_api_key et routing_model_cost depuis bigbertha.db."""
    if not DB_PATH.exists():
        logger.error("DB introuvable : %s", DB_PATH)
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT key, value FROM app_config WHERE key IN ('openrouter_api_key', 'routing_model_cost')"
    )
    config = {row["key"]: row["value"] for row in cur.fetchall()}
    conn.close()
    return config


def call_openrouter(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """Appel HTTP direct via urllib (stdlib). Retourne le contenu texte du message."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        logger.error("OpenRouter HTTP %s : %s", e.code, detail)
        sys.exit(1)
    except urllib.error.URLError as e:
        logger.error("Connexion OpenRouter impossible : %s", e.reason)
        sys.exit(1)

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error("Réponse OpenRouter inattendue : %s", body)
        sys.exit(1)


# ── Étape 3 — Parse et validation ────────────────────────────────────────────

def parse_and_validate(raw_json: str, available_files: set, company: str) -> list:
    """Parse le JSON LLM, valide les noms de fichiers, retourne la liste days."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.error("JSON invalide retourné par le LLM : %s", e)
        sys.exit(1)

    # Si liste à la racine, prendre le premier élément
    if isinstance(data, list):
        data = data[0]

    days = data.get("days", [])
    if not days:
        logger.error("Le LLM n'a retourné aucun jour dans le JSON.")
        sys.exit(1)

    validated_days = []
    for day_obj in days:
        validated_docs = []
        for doc in day_obj.get("documents", []):
            if doc in available_files:
                validated_docs.append(doc)
            else:
                logger.warning("Fichier halluciné ignoré (jour %s) : %s", day_obj.get("day"), doc)
        day_obj["documents"] = validated_docs
        validated_days.append(day_obj)

    return validated_days


# ── Étape 4 — Affichage et confirmation ──────────────────────────────────────

def display_plan(company: str, mode: str, n_days: int, source_files: list, days: list) -> None:
    print()
    print(f"=== PLAN DE SIMULATION — {company} ({mode}, {n_days} jours) ===")
    print(f"Fichiers source : {', '.join(source_files)}")
    print()
    for day_obj in days:
        day_num = day_obj.get("day", "?")
        theme = day_obj.get("theme", "")
        docs = day_obj.get("documents", [])
        messages = day_obj.get("messages", [])
        print(f"Jour {day_num} — {theme}")
        print(f"  Docs   : {', '.join(docs) if docs else '(aucun)'}")
        for i, msg in enumerate(messages, 1):
            print(f"  Msg {i}  : \"{msg}\"")
        print()


def confirm_plan(auto: bool) -> bool:
    if auto:
        return True
    answer = input("Valider ce plan ? (o/n) : ").strip().lower()
    return answer == "o"


# ── Étape 5 — Écriture manifest ──────────────────────────────────────────────

def write_manifest(company: str, mode: str, n_days: int, days: list) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{company}_{timestamp}"
    run_dir = RUNS_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "meta": {
            "company": company,
            "mode": mode,
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "n_days": n_days,
        },
        "days": {},
    }

    for day_obj in days:
        day_num = str(day_obj.get("day", "?"))
        relative_docs = [
            f"../../../../Samples/{company}/{fname}"
            for fname in day_obj.get("documents", [])
        ]
        manifest["days"][day_num] = {
            "theme": day_obj.get("theme", ""),
            "documents": relative_docs,
            "messages": day_obj.get("messages", []),
        }

    manifest_path = run_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return run_dir


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère un plan de simulation à partir des fichiers d'une entreprise Samples/."
    )
    parser.add_argument("--company", required=True, help="Nom du dossier dans Samples/")
    parser.add_argument(
        "--mode",
        choices=list(MODES.keys()),
        default="moyen",
        help="Durée de simulation : court (7j) | moyen (14j) | long (30j)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Skip la confirmation manuelle",
    )
    args = parser.parse_args()

    company = args.company
    mode = args.mode
    n_days = MODES[mode]
    auto = args.auto

    # Vérification dossier Samples
    company_dir = SAMPLES_DIR / company
    if not company_dir.is_dir():
        logger.error("Dossier introuvable : %s", company_dir)
        sys.exit(1)

    # Étape 1 — Extraction
    logger.info("Extraction des fichiers de %s...", company)
    file_contents = extract_company_files(company_dir)
    if not file_contents:
        logger.error("Aucun fichier lisible dans %s", company_dir)
        sys.exit(1)

    available_files = set(file_contents.keys())
    source_files = sorted(available_files)

    # Étape 2 — Appel LLM
    config = load_config_from_db()
    api_key = config.get("openrouter_api_key", "").strip()
    if not api_key:
        logger.error("openrouter_api_key vide dans app_config.")
        sys.exit(1)
    model = config.get("routing_model_perf", "").strip() or DEFAULT_MODEL

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(N=n_days)
    user_prompt = "\n\n".join(
        f"[{fname}]\n{content}" for fname, content in sorted(file_contents.items())
    )

    logger.info("Appel OpenRouter (modèle : %s, %d jours)...", model, n_days)
    raw_response = call_openrouter(api_key, model, system_prompt, user_prompt)

    # Étape 3 — Parse et validation
    days = parse_and_validate(raw_response, available_files, company)

    # Étape 4 — Affichage et confirmation
    display_plan(company, mode, n_days, source_files, days)

    if not confirm_plan(auto):
        print("Plan annulé. Relancer avec d'autres paramètres.")
        sys.exit(0)

    # Étape 5 — Écriture manifest
    run_dir = write_manifest(company, mode, n_days, days)
    run_rel = run_dir.as_posix().replace("docs/Test/runs", "docs/Test/runs")

    print(f"OK Manifest ecrit : {run_dir}/manifest.json")
    print(f" Lancer la simulation avec :")
    print(f" python tests/simulate_all.py --run-dir {run_dir.as_posix()}")


if __name__ == "__main__":
    main()
