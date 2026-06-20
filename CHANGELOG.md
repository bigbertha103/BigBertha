# CHANGELOG — Big Bertha

## 2026-06-20 — Sessions de test + simulation (BLOC 7 RAG)
- `backend/routers/test_sessions.py` : 5 routes (créer, lister, active, activer, reset) — reset supprime ChromaDB + hard-delete docs + désactive session
- `backend/main.py` : router test_sessions enregistré
- `frontend/chat.html` : `div#test-mode-banner` ajouté dans `<main>`
- `frontend/chat.js` : `showTestModeBanner()` + appel `getActiveTestSession()` dans `init()`
- `frontend/style.css` : styles bandeau mode test (orange foncé) + UI sessions de test
- `frontend/api.js` : `getActiveTestSession()`, `getTestSessions()`, `createTestSession()`, `activateTestSession()`, `resetTestSession()`
- `frontend/settings.html` : section "Sessions de test" (formulaire création + liste avec boutons Activer/Reset)
- `frontend/settings.js` : `loadTestSessions()`, `createSession()`, `activateSession()`, `resetSession()` + appel dans `init()`
- `tests/simulate_day.py` : script CLI stdlib-only (argparse + urllib) — import docs, crée/réutilise conversation, poll jobs, résumé
- `tests/corpus/manifest.json` : manifest exemple 3 jours

## 2026-06-20 — Routes proposals + UI (BLOC 6 RAG)
- `backend/routers/proposals.py` : GET `/api/learning-proposals?status=` (jointure sentinel_reports) + PATCH `/api/learning-proposals/{id}` (approve/reject) — logique UPDATE_AGENT_PROMPT, UPDATE_COMPANY_RULE, ARCHIVE_DOCUMENT avec RAG soft-delete + fallback si RAG None
- `backend/main.py` : router proposals enregistré
- `frontend/settings.html` : section "Propositions d'amélioration" (badge PENDING, liste cartes, historique)
- `frontend/style.css` : styles proposals (cartes, badges types colorés, boutons approve/reject, historique)
- `frontend/api.js` : `getProposals(status)` + `patchProposal(id, action)`
- `frontend/settings.js` : `loadProposals()`, `loadProposalHistory()`, `approveProposal()`, `rejectProposal()` + appels dans `init()`

## 2026-06-20 — Agent SENTINEL (BLOC 5 RAG)
- `backend/services/sentinel_service.py` : `run_analysis()` async — charge contexte (jobs, KB, profil), appelle LLM, parse JSON strict, valide proposals (3 types autorisés, max 3), stocke en DB, remet flag SENTINEL à 0
- `backend/routers/sentinel.py` : POST `/api/sentinel/analyze` (appel direct await) + GET `/api/sentinel/reports` (liste + nb proposals PENDING)
- `backend/main.py` : router sentinel enregistré
- `frontend/settings.html` : section "Analyse de l'équipe" (score coloré, observations, métriques, delta, historique)
- `frontend/style.css` : styles SENTINEL (score coloré, spinner pulse, historique, delta)
- `frontend/api.js` : `runSentinelAnalysis()` + `getSentinelReports()`
- `frontend/settings.js` : `_renderSentinelReport()`, `loadSentinelReports()`, bouton analyse avec spinner

## 2026-06-20 — Injection contexte KB (BLOC 4 RAG)
- `backend/services/context_builder.py` : `build_routing_payload()` + `build_agent_payload()` acceptent `kb_context: str = ""` — section "Base documentaire" injectée si non vide + signal SENTINEL lu depuis `app_config`
- `backend/services/boss_service.py` : `run_routing()` accepte et propage `kb_context`
- `backend/services/agent_analyste.py` : `run()` accepte et propage `kb_context`
- `backend/services/agent_redacteur.py` : `run()` accepte et propage `kb_context`
- `backend/services/job_runner.py` : `_fetch_kb_context()` async (import local RAG, fallback `""`), `_update_sentinel_signal()` sync, propagation de `kb_context` à toute la chaîne

## 2026-06-20 — Routes KB + UI import (BLOC 3 RAG)
- `backend/routers/knowledge.py` : 5 routes (import multipart, liste, delete, search, stats) avec anyio.to_thread.run_sync + fallback 503 si RAG non disponible
- `backend/main.py` : router knowledge enregistré
- `frontend/settings.html` : section "Base de connaissance" (badge compteur, import fichiers, tableau documents)
- `frontend/style.css` : styles KB (badge, table, statuts colorés, bouton supprimer)
- `frontend/api.js` : 4 fonctions KB (getKnowledgeStats, getKnowledgeDocuments, importKnowledgeDocuments, deleteKnowledgeDocument)
- `frontend/settings.js` : fonctions loadKnowledgeStats, loadKnowledgeDocuments, importDocuments, deleteDocument + intégration dans init()

## 2026-06-20 — Moteur RAG standalone (BLOC 2 RAG)
- `backend/services/rag_engine.py` : moteur RAG complet (`CustomTextSplitter`, `DocumentLoader`, `RAGManager`, singleton `init_rag`/`get_rag`) — ChromaDB `DefaultEmbeddingFunction` (all-MiniLM-L6-v2 via onnxruntime, zéro torch)
- `backend/main.py` : init RAG dans le lifespan avec fallback mode dégradé
- `backend/database.py` : ajout de `get_config_value()` pour lecture unitaire de clés app_config
- `requirements.txt` : ajout chromadb, fastembed, pypdf, python-docx, python-multipart
- `tests/test_rag_engine.py` : 5 tests standalone — tous PASSED
- `PROJET_CONTEXTE.md` : section 8 mise à jour avec profil Neuraltech Consulting

## 2026-06-20 — Foundation V2 (BLOC 1 RAG)
- `database.py` : ajout des 4 tables V2 (`test_sessions`, `knowledge_documents`, `sentinel_reports`, `learning_proposals`) + 4 index + 2 clés `app_config` (`sentinel_suggestion_pending`, `active_test_session_id`)
- `database.py` : seed profil entreprise Neuraltech Consulting (remplace Cabinet Moreau Conseil sur nouvelle installation)
- `.env.example` : section `# RAG` ajoutée avec 6 variables (`RAG_COLLECTION_NAME`, `RAG_PERSIST_DIR`, `RAG_EMBEDDING_MODEL`, `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`, `RAG_TOP_K`)
- `.gitignore` : ajout de `backend/data/chroma_db/`
- `tests/__init__.py` : dossier tests/ initialisé
- `PROJET_CONTEXTE.md` : sections 4, 9 et 12 mises à jour avec la structure et le roadmap V2

## 2026-06-20 — Audit post-build V1
- `backend/routers/pinned.py` : nouveau router dédié aux éléments épinglés (3 routes)
- `backend/schemas/pinned.py` : schéma Pydantic `PinnedOut` complet avec tous les champs
- `backend/main.py` : enregistrement du router pinned + import StaticFiles corrigé en chemin absolu
- `frontend/chat.js` : intervalle de polling réduit à 1000ms
- `backend/routers/conversations.py` : vérification 409 si job actif avant INSERT message

## 2026-06-20 — Build V1 complet
- Implémentation complète backend : database.py, main.py, tous les routers et services
- Implémentation complète frontend : chat.html/js, settings.html/js, api.js, shared.js, style.css
