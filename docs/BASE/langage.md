---
owner: Kinder + tezcatlypoca
last_updated: 2026-06-21
review_every: 30j
---

# Glossaire — Termes BigBertha

> **Source de vérité du langage commun.** Quand un terme apparaît ici, sa définition s'applique partout dans le projet — dans le code, les prompts, les conversations, les tests. Ne pas réinventer.

---

## Termes fondamentaux

**Agent** : spécialiste stateless qui reçoit une tâche isolée du Boss et retourne un résultat en markdown. Ne voit jamais l'historique de conversation. Stocké en DB (`agents`), activable/désactivable. En V1 : ANALYSTE et RÉDACTEUR.
| N'est PAS : le Boss (orchestrateur), un utilisateur.

**ANALYSTE** : agent spécialisé en recherche, synthèse, veille et benchmarks. Retourne du markdown structuré.
| N'est PAS : le RÉDACTEUR — ne produit pas de documents finaux destinés à être envoyés.

**RÉDACTEUR** : agent spécialisé en documents professionnels finis (propositions, notes, emails, CR). Retourne un document prêt à l'emploi.
| N'est PAS : l'ANALYSTE — ne fait pas de recherche de fond.

**ARCHIVISTE** : agent léger dédié à la mémoire de session. Déclenché sur archivage d'une conversation (manuel ou handoff automatique). Produit un résumé JSON (`Bilan ARCHIVISTE`) stocké dans `session_summaries`.
| N'est PAS : SENTINEL — SENTINEL améliore les agents, ARCHIVISTE résume les conversations.

**SENTINEL** : agent qui analyse les jobs passés (50 derniers), produit un score qualité (0–100) et génère des proposals d'amélioration. Déclenché automatiquement ou manuellement. *Distinct de l'agent "Sentinelle" du projet JARVIS 2.0 — même radical, rôles différents.*
| N'est PAS : un outil de monitoring technique (logs), l'ARCHIVISTE.

**Boss** : orchestrateur central invisible. Effectue 2 appels LLM internes par message (Phase 1 = ROUTING, Phase 2 = SYNTHESIS). L'utilisateur perçoit un interlocuteur unique — les agents ne sont jamais mentionnés dans l'UI.
| N'est PAS : un agent au sens de la table `agents`, pas visible comme "un agent parmi d'autres".

**Routing** : Phase 1 du Boss. Décide quel agent traite le message (ou BOSS si réponse directe). Retourne un JSON strict `{agent_code, task, rationale}`. La valeur `task` est la seule information que l'agent recevra en plus de son propre prompt.
| N'est PAS : du load balancing, un système de files d'attente.

**Synthesis** : Phase 2 du Boss. Reformule la réponse brute de l'agent dans le ton de l'entreprise. Décide aussi des éléments à épingler (max 2 par tour).
| N'est PAS : un résumé de la conversation, un post-traitement optionnel.

**Job** : unité de traitement asynchrone par message utilisateur. Cycle : PENDING → ROUTING → AGENT_RUNNING → SYNTHESIZING → DONE/ERROR. 3 appels LLM au total. Pollé toutes les secondes par le frontend.
| N'est PAS : un ticket de support, une tâche planifiée, une requête HTTP.

**Conversation** : session de questions/réponses à ardoise vierge. Pinned et historique repartent à zéro à chaque nouvelle conversation. Statut : `active` ou `archived`. Liée à la suivante via `previous_conversation_id`.
| N'est PAS : une session utilisateur (pas d'auth), un projet long terme dans le système.

**Pinned** (élément épinglé) : information réinjectée dans tous les appels Boss Phase 1 suivants de la même conversation. Deux sources : Boss automatique (Phase 2) ou utilisateur manuellement. Scopé par conversation. Soft-delete. Limité aux 5 plus récents lors de l'injection.
| N'est PAS : une note permanente (réinitialisé à chaque nouvelle conversation), un favori global.

**Company** (company_profile) : profil de l'entreprise cliente. Injecté dans chaque appel LLM (nom, secteur, ton, règles métier). Une seule ligne en DB (mono-tenant). 404 si pas encore configuré.
| N'est PAS : un compte utilisateur, un tenant SaaS.

**Corpus** : ensemble de documents importés dans la base de connaissance (RAG), indexés dans ChromaDB. Alimenté via l'UI (PDF/MD/TXT/DOCX). Top-3 pertinents injectés dans chaque appel LLM.
| N'est PAS : l'historique des conversations, les prompts système des agents.

**Apprentissage** : cycle automatique SENTINEL → proposals → approbation → mise à jour des prompts/règles. S'appuie sur les jobs réels passés.
| N'est PAS : du fine-tuning du modèle LLM sous-jacent, de l'entraînement ML.

**Proposal** : suggestion d'amélioration générée par SENTINEL. Types : `UPDATE_AGENT_PROMPT`, `UPDATE_COMPANY_RULE`, `ARCHIVE_DOCUMENT`. Statut PENDING → APPROVED ou REJECTED. Max 3 par rapport.
| N'est PAS : une proposition commerciale (terme différent dans ce contexte).

**Sample** : entreprise fictive pour tests d'apprentissage. Dossier dans `Samples/` avec documents + script de simulation. 9 entreprises fake disponibles. Profil de test prod = "Neuraltech Consulting".
| N'est PAS : une démo pour vrai client, un template d'onboarding.

**Inference mode** : mode de sélection des modèles LLM. COST (modèles légers) ou PERFORMANCE (modèles puissants). Toggle `perf_mode` dans les settings. 11 clés `app_config`, une par tâche.
| N'est PAS : un paramètre par requête, un indicateur de vitesse affiché à l'utilisateur.

---

## Termes V2-Mémoire

**Handoff** : transition automatique déclenchée quand une conversation atteint son seuil (tokens ou nombre de messages). La conversation est archivée, une nouvelle est créée, l'utilisateur continue sans interruption visible.

**Session** : ensemble de conversations liées par `previous_conversation_id`. Une session = un fil de travail continu sur un sujet, découpé en plusieurs conversations pour maîtriser la taille du contexte.

**Bilan ARCHIVISTE** : JSON à 5 clés (`sujet_principal`, `decisions_prises`, `informations_cles`, `questions_ouvertes`, `prochaine_etape`) produit par l'agent ARCHIVISTE à chaque archivage. Réinjecté dans le routing de la conversation suivante.

**RAG bicéphale** : double retrieval à chaque routing : `kb_documents` (top_k=3, documents clients) + `session_memory` (top_k=1, bilans de sessions passées). Les deux sources sont injectées séparément dans le prompt avec des labels distincts.

**Trigger** : cause d'un archivage. Valeurs possibles : `token_threshold`, `message_threshold`, `manual`.

**Session memory** : collection ChromaDB distincte (`session_memory`) qui stocke les bilans ARCHIVISTE sous forme d'embeddings. Séparée de `kb_documents` (documents clients).

**Test session** : environnement isolé avec sa propre collection ChromaDB (`bigbertha_test_{session_id}`). Teste l'apprentissage sans altérer la production (`bigbertha_prod`).
| N'est PAS : une conversation de test normale, un environnement de staging classique.
