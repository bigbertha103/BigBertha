---
owner: Kinder
last_updated: 2026-06-24
review_every: 30j
---

# Architecture technique — BigBertha

> Vue d'ensemble pour ne pas réinventer l'architecture existante. Lire avant toute mission technique.

---

## Stack

| Couche | Technologie |
|---|---|
| Backend | FastAPI (Python) |
| Base de données | SQLite — sqlite3 natif, zéro ORM |
| Frontend | HTML5 / CSS3 / JS vanilla |
| LLM (V1/v2-pc) | OpenRouter (cloud) |
| LLM (v2-machine) | Ollama (local) |
| RAG | SimpleVectorStore (pure Python/numpy) — ChromaDB retiré (incompatible Python 3.14) |

## Structure dossiers

```
backend/
├── routers/        ← routes FastAPI
├── services/       ← logique métier (boss, agents, sentinel, rag...)
├── schemas/        ← modèles Pydantic
└── data/           ← DB SQLite + vecteurs (.npz/.json) + logs

frontend/           ← HTML/CSS/JS vanilla
docs/
├── BASE/           ← connaissance partagée (source de vérité)
├── Test/
│   ├── runs/       ← manifests de simulation (plan_simulation.py)
│   └── logs/       ← logs JSON par run (simulate_all.py)
└── Prompt/         ← protocoles de session (clôture, lancement tests)
Samples/            ← entreprises fake — un dossier par entreprise (md/txt/pdf/docx)
tests/
├── plan_simulation.py   ← génère manifest depuis Samples/{company}/
└── simulate_all.py      ← exécute la simulation, produit le log JSON
```

## Pipeline d'un message utilisateur

```
User message → Job créé (PENDING)
→ ROUTING (Boss choisit l'agent)
→ AGENT_RUNNING (ANALYSTE ou REDACTEUR)
→ SYNTHESIZING (Boss synthétise la réponse)
→ DONE → réponse affichée
```

## Routing de modèles (V2)

Deux modes configurables : **COST** et **PERFORMANCE**

| Tâche | Clé config cost | Clé config perf |
|---|---|---|
| Routing | routing_model_cost | routing_model_perf |
| Agent | agent_model_cost | agent_model_perf |
| Synthesis | synthesis_model_cost | synthesis_model_perf |
| Sentinel | sentinel_model_cost | sentinel_model_perf |
| Archiviste | archiviste_model_cost | archiviste_model_perf |

## V2-Mémoire

Deux blocs ajoutés en V2 :

**Bloc A — Routing de modèles par tâche** : 11 clés `app_config`, toggle `perf_mode` dans settings (COST / PERFORMANCE).

**Bloc B — Archivage conversations** :
- `conversations.status` = active/archived
- Archivage manuel (bouton UI) ou handoff automatique (seuils `handoff_token_threshold` / `handoff_message_fallback`)
- L'archivage déclenche l'ARCHIVISTE → résumé JSON stocké dans `session_summaries` et vectorisé dans `session_memory`
- Le bilan est réinjecté en contexte dans la conversation suivante via RAG bicéphale

## Tables principales DB (SQLite)

- `conversations` — statut active/archived, lien `previous_conversation_id`
- `messages` — rôles user/boss
- `jobs` — pipeline de traitement ; champ `kb_used` (1 si le RAG avait du contexte à injecter, 0 sinon — source de vérité pour `kb_citation_rate` SENTINEL)
- `agents` — prompts système des agents
- `pinned_context` — éléments épinglés (soft-delete)
- `app_config` — configuration clé/valeur
- `sentinel_reports` + `learning_proposals` — apprentissage SENTINEL
- `knowledge_documents` — documents RAG indexés
- `test_sessions` — sessions de test isolées
- `session_summaries` — résumés ARCHIVISTE (SQLite, pas ChromaDB)

## Collections vectorielles (SimpleVectorStore)

Stockage : `backend/data/chroma_db/<collection_name>/` (fichiers `.npz` + `.json`)

- `bigbertha_prod` — documents clients (top_k=3 à chaque appel)
- `session_memory` — bilans ARCHIVISTE vectorisés (top_k=1)
- `bigbertha_test_{session_id}` — collection isolée par test session

## Deployment Checklist

Avant lancement sur LBB ou production, vérifier :

- [ ] Fichier `.env` : `OPENROUTER_API_KEY` défini et non-vide
- [ ] `backend/main.py` : tous les routers montés (knowledge, sentinel, proposals, test_sessions)
- [ ] Logs démarrage FastAPI : pas d'erreur route registration
- [ ] Test : `curl -X POST -F "files=@test.md" http://localhost:8000/api/knowledge/import` → 200 OK
- [ ] Test : `curl -X POST http://localhost:8000/api/sentinel/analyze` → 200 OK
- [ ] Test : `curl http://localhost:8000/api/sentinel/reports` → 200 OK (liste vide si aucun rapport)
- [ ] Git : `git log --oneline -1` confirme branche v2 déployée
- [ ] Simulation courte : `python tests/simulate_all.py --corpus-dir "Samples/Neuraltech Consulting" --day-duration 0 --mode quick`
