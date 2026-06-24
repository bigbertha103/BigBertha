"""
simulate_all.py — Simulation multi-jours complète pour Big Bertha.

Usage :
    python tests/simulate_all.py --corpus-dir "docs/petit_test" --day-duration 0
    python tests/simulate_all.py --corpus-dir "docs/petit_test" --conv-id 42
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

POLL_INTERVAL = 2
POLL_TIMEOUT = 180


# ── Helpers HTTP (stdlib uniquement) ─────────────────────────────

def _get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        raise ConnectionError(f"API inaccessible : {exc}") from exc


def _post_json(url: str, data: dict, timeout: int = 180) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} : {body_text[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ConnectionError(f"API inaccessible : {exc}") from exc


def _post_multipart(url: str, filepath: Path) -> dict:
    boundary = "----BigBerthaBoundary"
    mime_map = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".py": "text/x-python",
    }
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


def _patch_json(url: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} : {body_text[:300]}") from exc
    except urllib.error.URLError as exc:
        raise ConnectionError(f"API inaccessible : {exc}") from exc


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


# ── Étapes par jour ──────────────────────────────────────────────

def import_documents(api_url: str, corpus_dir: Path, doc_filenames: list[str]) -> tuple[int, list[dict]]:
    if not doc_filenames:
        print("  (aucun document à importer ce jour)")
        return 0, []
    imported = 0
    imported_docs: list[dict] = []
    for filename in doc_filenames:
        filepath = (corpus_dir / filename).resolve()
        if not filepath.exists():
            print(f"  [WARN] Fichier introuvable : {filepath}")
            imported_docs.append({"file": Path(filename).name, "status": "NOT_FOUND", "error": "fichier introuvable"})
            continue
        try:
            result = _post_multipart(f"{api_url}/api/knowledge/import", filepath)
            items = result if isinstance(result, list) else []
            statuses = [r.get("status", "?") for r in items]
            status_str = ", ".join(statuses) if statuses else "?"
            print(f"  [IMPORT] {filename} → {status_str}")
            first_status = statuses[0] if statuses else "?"
            first_error = items[0].get("error") if items else None
            imported_docs.append({"file": Path(filename).name, "status": first_status, "error": first_error})
            if any(s == "INDEXED" for s in statuses):
                imported += 1
        except Exception as exc:
            print(f"  [ERROR] Import {filename} : {exc}")
            imported_docs.append({"file": Path(filename).name, "status": "ERROR", "error": str(exc)[:200]})
    return imported, imported_docs


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


def send_messages(api_url: str, conv_id: int, messages: list[str]) -> tuple[int, list[dict]]:
    if not messages:
        print("  (aucun message ce jour)")
        return 0, []
    sent = 0
    exchanges: list[dict] = []
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
            response_data = fetch_last_response(api_url, conv_id)
            response_data["message"] = msg
            exchanges.append(response_data)
        except Exception as exc:
            print(f"    [ERROR] {exc}")
    return sent, exchanges


def run_sentinel(api_url: str) -> dict:
    print("\n── SENTINEL ──────────────────────────────────")
    try:
        report = _post_json(f"{api_url}/api/sentinel/analyze", {})
        score = report.get("score", 0)
        observations = report.get("observations", [])
        proposals = report.get("proposals", [])
        print(f"  Score : {score}")
        print(f"  Observations : {len(observations)}")
        print(f"  Proposals générées : {len(proposals)}")
        return report
    except Exception as exc:
        print(f"  [ERROR] SENTINEL : {exc}")
        return {}


def auto_approve_proposals(api_url: str) -> list[dict]:
    print("\n── Auto-approbation proposals ────────────────")
    approved: list[dict] = []
    try:
        pending = _get(f"{api_url}/api/learning-proposals?status=PENDING")
        if not pending:
            print("  (aucune proposal PENDING)")
            return approved
        for proposal in pending:
            pid = proposal["id"]
            ptype = proposal.get("proposal_type", "?")
            target = proposal.get("target", "?")
            rationale = proposal.get("rationale", "")
            try:
                _patch_json(
                    f"{api_url}/api/learning-proposals/{pid}",
                    {"action": "approve"},
                )
                print(f"  {ptype} sur {target} — APPROUVÉE")
                approved.append({
                    "id": pid,
                    "type": ptype,
                    "target": target,
                    "rationale": rationale,
                })
            except Exception as exc:
                print(f"  [ERROR] Approbation proposal #{pid} : {exc}")
    except Exception as exc:
        print(f"  [ERROR] Récupération proposals : {exc}")
    return approved


def wait_next_day(day_duration: int, is_last: bool) -> None:
    if day_duration <= 0 or is_last:
        return
    print(f"\n── Attente {day_duration}s avant le jour suivant ──")
    remaining = day_duration
    while remaining > 0:
        step = min(60, remaining)
        print(f"  Prochain jour dans {remaining}s…")
        time.sleep(step)
        remaining -= step


# ── Mod B — Session de test dédiée ──────────────────────────────

def create_test_session(api_url: str, company: str) -> int | None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{company}_{timestamp}"
    try:
        result = _post_json(f"{api_url}/api/test-sessions", {"name": name})
        session_id = result.get("id") or result.get("session_id")
        if not session_id:
            print(f"  [WARN] create_test_session : pas d'id dans la réponse")
            return None
        try:
            _post_json(f"{api_url}/api/test-sessions/{session_id}/activate", {})
        except Exception as exc:
            print(f"  [WARN] Activation session #{session_id} : {exc}")
        print(f"  Session de test créée : #{session_id} ({name})")
        return session_id
    except Exception as exc:
        print(f"  [WARN] create_test_session ignorée : {exc}")
        return None


# ── Mod C — Capture dernière réponse ─────────────────────────────

def fetch_last_response(api_url: str, conversation_id: int) -> dict:
    empty = {"agent_code": "?", "response_preview": "", "response_length": 0, "kb_cited": False}
    try:
        messages = _get(f"{api_url}/api/conversations/{conversation_id}/messages")
        if not isinstance(messages, list) or not messages:
            return empty
        boss_msgs = [m for m in messages if m.get("role") in ("boss", "assistant")]
        if not boss_msgs:
            return empty
        last = boss_msgs[-1]
        content = last.get("content", "")
        job_id = last.get("job_id")
        agent_code = "?"
        kb_used = 0
        if job_id:
            try:
                job = _get(f"{api_url}/api/jobs/{job_id}")
                agent_code = job.get("agent_code", "?") or "?"
                kb_used = job.get("kb_used", 0)
            except Exception:
                pass
        return {
            "agent_code": agent_code,
            "response_preview": content[:300],
            "response_length": len(content),
            "kb_cited": bool(kb_used),
        }
    except Exception:
        return empty


# ── Mod C — Génération log JSON ───────────────────────────────────

def generate_log(
    api_url: str,
    run_dir: Path | None,
    company: str,
    mode: str,
    conv_id: int,
    simulation_reports: list[dict],
    approved_by_day: list[list[dict]],
    exchanges_by_day: list[list[dict]],
    imported_docs_by_day: list[list[dict]] | None = None,
) -> None:
    logs_dir = Path("docs/Test/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{company}_{timestamp}_log.json"
    log_path = logs_dir / log_filename

    if imported_docs_by_day is None:
        imported_docs_by_day = [[] for _ in simulation_reports]

    n_days = len(simulation_reports)
    n_messages = sum(len(ex) for ex in exchanges_by_day)
    n_docs = sum(
        sum(1 for d in day_docs if d.get("status") == "INDEXED")
        for day_docs in (imported_docs_by_day or [])
    )

    days_log = []
    for idx, (report, approved, exchanges) in enumerate(
        zip(simulation_reports, approved_by_day, exchanges_by_day), start=1
    ):
        metrics = report.get("metrics", {})
        sentinel_entry = {
            "score": report.get("score", 0),
            "routing_coherence": metrics.get("routing_coherence", 0),
            "pinned_rate": metrics.get("pinned_rate", 0),
            "kb_citation_rate": metrics.get("kb_citation_rate", 0),
        }
        day_docs = (imported_docs_by_day[idx - 1] if imported_docs_by_day and idx - 1 < len(imported_docs_by_day) else [])
        days_log.append({
            "day": idx,
            "docs_imported": day_docs,
            "sentinel": sentinel_entry,
            "proposals_approved": len(approved),
            "exchanges": [
                {
                    "message": ex.get("message", ""),
                    "agent_code": ex.get("agent_code", "?"),
                    "response_preview": ex.get("response_preview", ""),
                    "response_length": ex.get("response_length", 0),
                    "kb_cited": ex.get("kb_cited", False),
                }
                for ex in exchanges
            ],
        })

    score_start = simulation_reports[0].get("score", 0) if simulation_reports else 0
    score_end = simulation_reports[-1].get("score", 0) if simulation_reports else 0
    delta = score_end - score_start
    routing_fallback_count = sum(
        1
        for day_exchanges in exchanges_by_day
        for ex in day_exchanges
        if ex.get("agent_code") in ("BOSS", "?")
    )

    log_data = {
        "meta": {
            "company": company,
            "mode": mode,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "n_days": n_days,
            "n_messages": n_messages,
            "n_docs": n_docs,
        },
        "days": days_log,
        "summary": {
            "score_start": score_start,
            "score_end": score_end,
            "delta": f"{delta:+d}",
            "total_proposals_approved": sum(len(a) for a in approved_by_day),
            "routing_fallback_count": routing_fallback_count,
        },
    }

    with open(log_path, "w", encoding="utf-8") as fh:
        json.dump(log_data, fh, ensure_ascii=False, indent=2)

    print(f"Log JSON sauvegardé : {log_path}")


# ── Bilan final ──────────────────────────────────────────────────

def _format_date() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


def _safe_metric(metrics: dict, key: str) -> float:
    try:
        return float(metrics.get(key, 0))
    except (TypeError, ValueError):
        return 0.0


def _pct_delta(initial: float, final: float) -> str:
    if initial == 0:
        return "N/A"
    pct = ((final - initial) / initial) * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.0f}%"


def build_report(
    corpus_dir: Path,
    day_duration: int,
    conv_id: int,
    reports: list[dict],
    approved_by_day: list[list[dict]],
) -> str:
    n_days = len(reports)
    date_str = _format_date()
    lines = [
        f"---",
        f"# Bilan simulation Big Bertha — {date_str}",
        f"## Configuration",
        f"- Corpus : {corpus_dir}",
        f"- Durée par jour : {day_duration}s",
        f"- Jours simulés : {n_days}",
        f"- Conversation id : {conv_id}",
        "",
        "## Évolution des scores SENTINEL",
        "",
        "| Jour | Score | routing_coherence | pinned_rate | kb_citation_rate | Proposals approuvées |",
        "|---|---|---|---|---|---|",
    ]
    for idx, (report, approved) in enumerate(zip(reports, approved_by_day), start=1):
        metrics = report.get("metrics", {})
        lines.append(
            f"| J{idx}  | {report.get('score', 0)}   | "
            f"{_safe_metric(metrics, 'routing_coherence'):.2f}             | "
            f"{_safe_metric(metrics, 'pinned_rate'):.2f}       | "
            f"{_safe_metric(metrics, 'kb_citation_rate'):.2f}            | "
            f"{len(approved)}                   |"
        )
    lines.append("")

    if reports:
        initial_score = reports[0].get("score", 0)
        final_score = reports[-1].get("score", 0)
        delta_score = final_score - initial_score
        pct = _pct_delta(initial_score, final_score)
        lines.append("## Progression globale")
        lines.append(f"Score J1 → J{n_days} : {delta_score:+d} points ({pct})")
        for metric_key in ("routing_coherence", "pinned_rate", "kb_citation_rate"):
            initial_val = _safe_metric(reports[0].get("metrics", {}), metric_key)
            final_val = _safe_metric(reports[-1].get("metrics", {}), metric_key)
            delta_val = final_val - initial_val
            sign = "+" if delta_val >= 0 else ""
            lines.append(
                f"{metric_key} J1 → J{n_days} : {sign}{delta_val:.2f} "
                f"({_pct_delta(initial_val, final_val)})"
            )
        lines.append("")

    lines.append("## Observations clés par jour")
    lines.append("")
    for idx, report in enumerate(reports, start=1):
        observations = report.get("observations", [])
        first_obs = observations[0] if observations else "(aucune observation)"
        lines.append(f"### Jour {idx}")
        lines.append(first_obs)
        lines.append("")

    lines.append("## Proposals approuvées (impact sur l'équipe)")
    lines.append("")
    any_approved = False
    for idx, approved in enumerate(approved_by_day, start=1):
        if not approved:
            continue
        any_approved = True
        for proposal in approved:
            lines.append(
                f"- J{idx} : {proposal['type']} sur {proposal['target']} — {proposal['rationale']}"
            )
    if not any_approved:
        lines.append("- Aucune proposal approuvée pendant la simulation.")
    lines.append("")

    lines.append("## Conclusion")
    if reports and final_score > initial_score + 20:
        lines.append("Apprentissage significatif détecté")
    else:
        lines.append("Progression modérée — enrichir le corpus")
    lines.append("")

    return "\n".join(lines)


def generate_final_report(
    api_url: str,
    corpus_dir: Path,
    day_duration: int,
    conv_id: int,
    sentinel_report_ids: list[int],
    approved_by_day: list[list[dict]],
) -> Path:
    print("\n\n=== Bilan final multi-jours ===")
    all_reports = _get(f"{api_url}/api/sentinel/reports")
    if not isinstance(all_reports, list):
        all_reports = []
    # Filtrer uniquement les rapports créés pendant ce run, dans l'ordre chronologique
    id_set = set(r for r in sentinel_report_ids if r is not None)
    simulation_reports = [r for r in reversed(all_reports) if r.get("id") in id_set]

    content = build_report(corpus_dir, day_duration, conv_id, simulation_reports, approved_by_day)
    output_path = corpus_dir / "bilan_simulation.md"
    output_path.write_text(content, encoding="utf-8")

    print("\nRésumé :")
    if simulation_reports:
        initial_score = simulation_reports[0].get("score", 0)
        final_score = simulation_reports[-1].get("score", 0)
        print(f"  Score initial : {initial_score}")
        print(f"  Score final   : {final_score}")
        print(f"  Delta         : {final_score - initial_score:+d}")
    print(f"  Proposals approuvées : {sum(len(a) for a in approved_by_day)}")
    print(f"  Bilan sauvegardé : {output_path}")
    return output_path


# ── Point d'entrée ───────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simule plusieurs jours de test Big Bertha depuis un manifest."
    )
    parser.add_argument(
        "--corpus-dir",
        default=None,
        help="Dossier contenant le manifest.json et les documents (rétrocompat)",
    )
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Dossier généré par plan_simulation.py (ex: docs/Test/runs/bluecart_20260622/)",
    )
    parser.add_argument(
        "--company",
        default=None,
        help="Nom de l'entreprise (extrait du meta du manifest si absent)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL de l'API (défaut : http://localhost:8000)",
    )
    parser.add_argument(
        "--day-duration",
        type=int,
        default=60,
        help="Secondes entre chaque jour simulé (défaut : 60, 0 pour test rapide)",
    )
    parser.add_argument(
        "--conv-id",
        type=int,
        default=None,
        help="ID de conversation existante à réutiliser",
    )
    args = parser.parse_args()

    if not args.run_dir and not args.corpus_dir:
        print("[FATAL] Fournir --run-dir ou --corpus-dir")
        sys.exit(1)

    corpus_dir = Path(args.run_dir or args.corpus_dir).resolve()
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    api_url = args.api_url.rstrip("/")
    day_duration = args.day_duration
    conv_id = args.conv_id

    # Vérifier accessibilité API
    try:
        _get(f"{api_url}/api/conversations")
    except ConnectionError as exc:
        print(f"[FATAL] {exc}")
        sys.exit(1)

    # Lire le manifest
    manifest_path = corpus_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"[FATAL] manifest.json introuvable : {manifest_path}")
        sys.exit(1)
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[FATAL] manifest.json invalide : {exc}")
        sys.exit(1)

    days = manifest.get("days", {})
    if not days:
        print("[FATAL] Aucun jour trouvé dans le manifest")
        sys.exit(1)

    sorted_days = sorted(days.keys(), key=lambda k: int(k))
    n_days = len(sorted_days)

    if "meta" in manifest:
        company = manifest["meta"].get("company", "unknown")
        mode = manifest["meta"].get("mode", "")
        n_days = manifest["meta"].get("n_days", n_days)
    else:
        company = args.company or "unknown"
        mode = ""

    print(f"\n{'='*50}")
    print(f"  SIMULATION COMPLÈTE — Big Bertha")
    print(f"{'='*50}")
    print(f"Corpus  : {corpus_dir}")
    print(f"API     : {api_url}")
    print(f"Jours   : {n_days}")
    print(f"Pause   : {day_duration}s")
    print(f"Company : {company} | Mode : {mode or '—'}")
    print(f"{'='*50}\n")

    # Mod B — Session de test dédiée
    print("── Session de test ───────────────────────────")
    create_test_session(api_url, company)

    # Créer la conversation une seule fois si besoin
    print("── Initialisation conversation ───────────────")
    try:
        conv_id = ensure_conversation(api_url, conv_id)
    except RuntimeError as exc:
        print(f"[FATAL] {exc}")
        sys.exit(1)

    approved_by_day: list[list[dict]] = []
    exchanges_by_day: list[list[dict]] = []
    imported_docs_by_day: list[list[dict]] = []
    sentinel_report_ids: list[int] = []

    for idx, day_key in enumerate(sorted_days, start=1):
        day_data = days[day_key]
        doc_filenames: list[str] = day_data.get("documents", [])
        messages: list[str] = day_data.get("messages", [])

        print(f"\n{'='*50}")
        print(f"  JOUR {day_key}/{n_days}")
        print(f"{'='*50}")
        print(f"Documents : {len(doc_filenames)} | Messages : {len(messages)}\n")

        # Étape A — import documents
        print("── Import documents ──────────────────────────")
        _imported_count, day_imported_docs = import_documents(api_url, corpus_dir, doc_filenames)
        imported_docs_by_day.append(day_imported_docs)

        # Étape B — conversation (réutilisée)
        print("\n── Conversation ──────────────────────────────")
        print(f"  Utilisation de la conversation #{conv_id}")

        # Étape C — messages
        _sent, day_exchanges = send_messages(api_url, conv_id, messages)
        exchanges_by_day.append(day_exchanges)

        # Étape D — attente jour suivant
        is_last = idx == n_days
        wait_next_day(day_duration, is_last)

        # Étape E — SENTINEL
        report = run_sentinel(api_url)
        sentinel_report_ids.append(report.get("id"))

        # Étape F — auto-approbation proposals
        approved = auto_approve_proposals(api_url)
        approved_by_day.append(approved)

    # Étape G/H — bilan final
    generate_final_report(api_url, corpus_dir, day_duration, conv_id, sentinel_report_ids, approved_by_day)

    # Mod C — log JSON
    try:
        sentinel_reports_raw = _get(f"{api_url}/api/sentinel/reports")
        simulation_reports = (sentinel_reports_raw if isinstance(sentinel_reports_raw, list) else [])[:n_days]
        simulation_reports = list(reversed(simulation_reports))
    except Exception:
        simulation_reports = [{} for _ in range(len(sorted_days))]
    generate_log(
        api_url, run_dir, company, mode, conv_id,
        simulation_reports, approved_by_day, exchanges_by_day,
        imported_docs_by_day=imported_docs_by_day,
    )


if __name__ == "__main__":
    main()
