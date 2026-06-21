---
owner: Kinder
last_updated: 2026-06-21
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

## Déploiement

- Vision finale : 100% on-premise chez le client (zéro cloud)
- V1 : même architecture mais LLM via OpenRouter (développement)
- `v2-pc` : OpenRouter (cloud test, développement)
- `v2-machine` : Ollama local (cible production client)

## Produit

- Mono-tenant : une instance = une entreprise cliente
- Approche B2B uniquement — pas de SaaS grand public

## Agents

- Agents actifs V1 : ANALYSTE, REDACTEUR (+ BOSS comme fallback)
- SENTINEL : analyse les 50 derniers jobs, score 0-100, proposals auto-approuvables
- ARCHIVISTE : agent séparé de SENTINEL, modèle léger, dédié à la mémoire de session

## UI

- Badges agent non affichés dans l'UI (décision D5 wireframe)
- DELETE /api/pinned/{id} pour désépingler (soft-delete is_active=0), pas PATCH
- Job blocking : backend retourne 409 si job actif sur la conversation
