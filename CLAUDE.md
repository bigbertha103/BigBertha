# CLAUDE.md — BigBertha

## Source de vérité absolue
**Lire `PROJET_CONTEXTE.md` EN ENTIER avant toute action.** Ce fichier contient l'historique complet des sessions, le schéma DB, les prompts système, les API routes, et les règles du projet.

Index de la documentation : `docs/BASE/INDEX.md`
- Termes : `docs/BASE/langage.md`
- Décisions inviolables : `docs/BASE/elements_figes.md`
- Architecture : `docs/BASE/Tech/architecture.md`
- Vision produit : `docs/BASE/Produit/vision.md`
- Tarification : `docs/BASE/Commercial/tarification.md`

## Protocole de clôture de session
À la fin de chaque session, exécuter le prompt dans `docs/Prompt/session_closure.md`.
Ne jamais sauter l'étape 1 (sync) — deux machines travaillent sur ce projet.

## Stack technique (figée — ne pas modifier)
- **Backend** : FastAPI Python 3.11+, port 8000
- **DB** : SQLite natif (`sqlite3`) — zéro ORM — fichier `backend/data/bigbertha.db`
- **Frontend** : HTML5 + CSS3 + JS vanilla (zéro framework)
- **LLM** : OpenRouter via `httpx` async (branche v2 = v2-pc)
- **RAG** : ChromaDB + `all-MiniLM-L6-v2` — 2 collections : `kb_documents` + `session_memory`

## Règles non-négociables
- Jamais de `print()` → `logger = logging.getLogger("bigbertha")`
- Jamais d'ORM — sqlite3 natif uniquement
- Jamais de framework JS — fetch natif uniquement
- Tous les chemins via `pathlib.Path`
- `openrouter_api_key` jamais retourné en clair dans les réponses API
- Prompts agents : dans `agents_templates.json` / DB uniquement (jamais hardcodés en Python)
- Prompts Boss V1 : hardcodés dans `context_builder.py` (décision V1, pas en DB)
- JSON mode obligatoire sur tous les appels LLM
- Un seul job actif par conversation (409 si déjà actif)
- Soft-delete uniquement pour `pinned_context` (`is_active=0`, jamais de DELETE SQL)
- DELETE conversations = hard delete en cascade (seul cas)
- `agent_code` toujours extrait de `routing_output`, jamais depuis `selected_agent_id`

## Branche v2 — État actuel (2026-06-22)
V2-Mémoire est **complète** (BLOCs A+B+C+D). Fonctionnalités implémentées :
- Routing de modèles par tâche (COST/PERFORMANCE, 11 clés app_config)
- Archivage conversations (manuel + handoff automatique par seuil tokens/messages)
- Agent ARCHIVISTE → bilan JSON dans `session_summaries` + vectorisation dans `session_memory`
- RAG bicéphale : `kb_documents` (top_k=3) + `session_memory` (top_k=1)
- Injection mémoire session précédente dans le contexte Boss (routing)
- Sidebar en accordéon groupant les conversations par session
- Bannière handoff avertissement (seuil 14 messages côté UI)
- Card bilan ARCHIVISTE dans l'UI pour les conversations archivées
- Champ `previous_conversation_id` sur la table `conversations`

## Variables d'environnement requises
Copier `.env.example` → `.env` et renseigner :
- `OPENROUTER_API_KEY` : clé API OpenRouter
- `MODEL_ID` : modèle par défaut (ex: `anthropic/claude-sonnet-4-5`)
- Les autres valeurs ont des defaults raisonnables

## Démarrage
```
# Windows
start.bat

# Linux/Mac
./start.sh
```
Puis ouvrir http://localhost:8000

## Tests
```bash
pytest tests/test_rag_engine.py
pytest tests/test_archiviste.py
python tests/simulate_all.py --help
```

## Conventions de nommage
- Tables/colonnes SQLite : `snake_case`
- Fichiers Python : `snake_case`
- Classes Python : `PascalCase`
- Fonctions Python/JS : `camelCase`
- Routes API : `/api/resource-name` (kebab-case)
- Constantes : `UPPER_SNAKE_CASE`
