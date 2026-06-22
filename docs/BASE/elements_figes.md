---
owner: Kinder
last_updated: 2026-06-22
review_every: 60j
---

# Éléments figés — Décisions inviolables

> Ces décisions ne se rediscutent pas. Avant de proposer une alternative technique ou produit, vérifier qu'elle ne contredit pas ce qui est listé ici.

---

## Architecture technique

- Stack V1 figée : **FastAPI + SQLite (sqlite3 natif, zéro ORM) + HTML5/CSS3/JS vanilla + OpenRouter**
- SQLite uniquement — pas de migration vers Postgres ou autre DB
- Pas de framework frontend (pas de React, Vue, Angular)
- `agent_code` absent de la table `messages` — parsé depuis `jobs.routing_output` à la demande
- Boss prompts V1 hardcodés dans `context_builder.py` (pas en DB)
- JSON mode obligatoire sur tous les appels LLM (routing, synthesis, SENTINEL, agents)
- DELETE /api/conversations/{id} = **hard delete en cascade** — pas de soft-delete sur les conversations
- `agent_code` toujours extrait de `routing_output`, jamais depuis `selected_agent_id` (NULL quand Boss répond directement)
- `openrouter_api_key` jamais retourné en clair dans les réponses API
- `model_name` dans `model_decision_log` : TEXT libre sans CHECK — le catalogue OpenRouter évolue fréquemment

## Architecture V2-Mémoire (figée 2026-06-21)

- **Model routing par tâche** : 2 modes configurables (COST / PERFORMANCE), 5 modèles indépendants — routing, agents, synthesis, sentinel, archiviste. Toggle dans settings.html.
- **Pinned context** limité aux 5 derniers éléments actifs (ORDER BY created_at DESC LIMIT 5)
- **2 collections vectorielles séparées** : `bigbertha_prod` (documents clients, top_k=3) + `session_memory` (bilans ARCHIVISTE, top_k=1). Backend : `SimpleVectorStore` (pure Python/numpy) — ChromaDB incompatible Python 3.14, ne pas réintroduire sans changement de runtime Python.
- **Handoff trigger** : seuil tokens estimés (1 tok ≈ 4 chars, clé `handoff_token_threshold`) + fallback messages (clé `handoff_message_fallback`, défaut 15). Archivage synchrone post-DONE, bilan ARCHIVISTE asynchrone.
- **`previous_conversation_id`** sur table `conversations` — lie les conversations d'une même session. La sidebar groupe par session (accordéon).

## Déploiement

- Vision finale : 100% on-premise chez le client (zéro cloud)
- V1 : même architecture mais LLM via OpenRouter (développement)
- `v2-pc` : OpenRouter (cloud test, développement)
- `v2-machine` : Ollama local (cible production client)

## Déploiement — décision actée

- **Rester sur OpenRouter pendant la phase de test/dev** — le sujet "serveur français" sera traité une fois l'outil performant

## Produit

- Mono-tenant : une instance = une entreprise cliente
- Approche B2B uniquement — pas de SaaS grand public
- Cible : PME françaises au centre du triangle Sécurité / Performance / Personnalisation — pas les extrêmes

## Agents

- Agents actifs V1 : ANALYSTE, REDACTEUR (+ BOSS comme fallback)
- SENTINEL : analyse les 50 derniers jobs, score 0-100, proposals auto-approuvables
- ARCHIVISTE : agent séparé de SENTINEL, modèle léger, dédié à la mémoire de session

## UI

- Badges agent non affichés dans l'UI (décision D5 wireframe)
- DELETE /api/pinned/{id} pour désépingler (soft-delete is_active=0), pas PATCH
- Job blocking : backend retourne 409 si job actif sur la conversation
