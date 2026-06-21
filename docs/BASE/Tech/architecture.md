---
owner: Kinder
last_updated: 2026-06-21
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
| RAG | ChromaDB + all-MiniLM-L6-v2 |

## Structure dossiers

```
backend/
├── routers/        ← routes FastAPI
├── services/       ← logique métier (boss, agents, sentinel, rag...)
├── schemas/        ← modèles Pydantic
└── data/           ← DB SQLite + ChromaDB + logs

frontend/           ← HTML/CSS/JS vanilla
docs/               ← documentation et corpus de test
Samples/            ← entreprises fake pour tests
tests/              ← scripts de simulation
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

## Tables principales DB

- `conversations` — statut active/archived
- `messages` — rôles user/boss
- `jobs` — pipeline de traitement
- `agents` — prompts système des agents
- `app_config` — configuration clé/valeur
- `sentinel_reports` + `learning_proposals` — apprentissage
- `knowledge_documents` — RAG
- `session_memory` (ChromaDB) — mémoire de session (V2-Mémoire)
