"""
simulate_day.py — Script de simulation d'un jour de test pour Big Bertha.

Usage :
    python tests/simulate_day.py --day 1
    python tests/simulate_day.py --day 2 --conv-id 42
    python tests/simulate_day.py --day 1 --api-url http://localhost:8000
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CORPUS_DIR = Path(__file__).parent / "corpus"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"
POLL_INTERVAL = 2
POLL_TIMEOUT = 120


# ── Helpers HTTP (stdlib uniquement) ─────────────────────────────

def _get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        raise ConnectionError(f"API inaccessible : {exc}") from exc


def _post_json(url: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} : {body_text[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ConnectionError(f"API inaccessible : {exc}") from exc


def _post_multipart(url: str, filepath: Path) -> dict:
    boundary = "----BigBerthaBoundary"
    mime_map = {".txt": "text/plain", ".md": "text/markdown", ".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".py": "text/x-python"}
    content_type = mime_map.get(filepath.suffix.lower(), "application/octet-stream")

    with open(filepath, "rb") as fh:
        file_data = fh.read()

    lines = []
    lines.append(f"--{boundary}".encode())
    lines.append(
        f'Content-Disposition: form-data; name="files"; filename="{filepath.name}"'.encode()
    )
    lines.append(f"Content-Type: {content_type}".encode())
    lines.append(b"")
    lines.append(file_data)
    lines.append(f"--{boundary}--".encode())
    body = b"\r\n".join(lines)

    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} : {body_text[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ConnectionError(f"API inaccessible : {exc}") from exc


# ── Étapes ────────────────────────────────────────────────────────

def import_documents(api_url: str, doc_filenames: list[str]) -> int:
    if not doc_filenames:
        print("  (aucun document à importer ce jour)")
        return 0
    imported = 0
    for filename in doc_filenames:
        filepath = CORPUS_DIR / filename
        if not filepath.exists():
            print(f"  [WARN] Fichier introuvable : {filepath}")
            continue
        try:
            result = _post_multipart(f"{api_url}/api/knowledge/import", filepath)
            items = result if isinstance(result, list) else []
            statuses = [r.get("status", "?") for r in items]
            status_str = ", ".join(statuses) if statuses else "?"
            print(f"  [IMPORT] {filename} → {status_str}")
            if any(s == "INDEXED" for s in statuses):
                imported += 1
        except Exception as exc:
            print(f"  [ERROR] Import {filename} : {exc}")
    return imported


def ensure_conversation(api_url: str, conv_id: int | None) -> int:
    if conv_id is not None:
        print(f"  Utilisation de la conversation #{conv_id}")
        return conv_id
    try:
        result = _post_json(f"{api_url}/api/conversations", {})
        new_id = result["id"]
        print(f"  Nouvelle conversation créée → id={new_id}")
        return new_id
    except Exception as exc:
        raise RuntimeError(f"Impossible de créer une conversation : {exc}") from exc


def send_messages(api_url: str, conv_id: int, messages: list[str]) -> int:
    if not messages:
        print("  (aucun message ce jour)")
        return 0
    sent = 0
    for msg in messages:
        print(f"\n  [MSG] {msg[:80]}{'…' if len(msg) > 80 else ''}")
        try:
            result = _post_json(
                f"{api_url}/api/conversations/{conv_id}/messages",
                {"content": msg},
            )
            job_id = result.get("job_id")
            if not job_id:
                print("    [ERROR] Pas de job_id dans la réponse")
                continue

            print(f"    → job #{job_id} en cours…", end="", flush=True)
            final_response = _poll_job(api_url, job_id)
            print(f"\n    → {final_response[:300]}{'…' if len(final_response) > 300 else ''}")
            sent += 1
        except Exception as exc:
            print(f"    [ERROR] {exc}")
    return sent


def _poll_job(api_url: str, job_id: int) -> str:
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        try:
            data = _get(f"{api_url}/api/jobs/{job_id}")
        except Exception:
            time.sleep(POLL_INTERVAL)
            continue
        status = data.get("status", "?")
        if status == "DONE":
            return data.get("final_response", "(réponse vide)")
        if status == "ERROR":
            return f"[ERREUR job] {data.get('error_message', 'inconnue')}"
        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL)
    return "[TIMEOUT] Le job n'a pas terminé dans les 120 secondes"


# ── Point d'entrée ─────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simule un jour de test Big Bertha depuis le manifest."
    )
    parser.add_argument("--day", type=int, required=True, help="Numéro du jour (ex: 1)")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL de l'API")
    parser.add_argument("--conv-id", type=int, default=None, help="ID de conversation existante")
    args = parser.parse_args()

    day_key = str(args.day)
    api_url = args.api_url.rstrip("/")

    # Vérifier accessibilité API
    try:
        _get(f"{api_url}/api/conversations")
    except ConnectionError as exc:
        print(f"[FATAL] {exc}")
        sys.exit(1)

    # Lire le manifest
    if not MANIFEST_PATH.exists():
        print(f"[FATAL] manifest.json introuvable : {MANIFEST_PATH}")
        sys.exit(1)
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[FATAL] manifest.json invalide : {exc}")
        sys.exit(1)

    days = manifest.get("days", {})
    if day_key not in days:
        print(f"[FATAL] Jour {args.day} introuvable dans le manifest (jours disponibles : {', '.join(days)})")
        sys.exit(1)

    day_data = days[day_key]
    doc_filenames: list[str] = day_data.get("documents", [])
    messages: list[str] = day_data.get("messages", [])

    print(f"\n=== Simulation Jour {args.day} — Big Bertha ===")
    print(f"API : {api_url}")
    print(f"Documents : {len(doc_filenames)} | Messages : {len(messages)}\n")

    # Étape 1 : import documents
    print("── Import documents ──────────────────────────")
    docs_imported = import_documents(api_url, doc_filenames)

    # Étape 2 : conversation
    print("\n── Conversation ──────────────────────────────")
    try:
        conv_id = ensure_conversation(api_url, args.conv_id)
    except RuntimeError as exc:
        print(f"[FATAL] {exc}")
        sys.exit(1)

    # Étape 3 : messages
    msgs_sent = send_messages(api_url, conv_id, messages)

    # Résumé
    print("\n\n── Résumé ────────────────────────────────────")
    print(f"  Documents importés : {docs_imported}/{len(doc_filenames)}")
    print(f"  Messages envoyés   : {msgs_sent}/{len(messages)}")
    print(f"  Conversation id    : {conv_id}  (passer --conv-id {conv_id} pour le prochain jour)")


if __name__ == "__main__":
    main()
