---
owner: Kinder + tezcatlypoca (à valider ensemble)
last_updated: 2026-06-21
review_every: 30j
---

# Glossaire — Termes BigBertha

> **Source de vérité du langage commun.** Quand un terme apparaît ici, sa définition s'applique partout dans le projet — dans le code, les prompts, les conversations, les tests. Ne pas réinventer.

---

## À compléter ensemble

Ce fichier est un squelette. Il doit être rempli lors d'une session de travail à deux, à partir des termes utilisés au quotidien dans le projet.

Questions à se poser pour chaque terme :
- C'est quoi exactement dans BigBertha (pas le sens générique) ?
- Ce que ce terme N'est PAS dans notre contexte ?
- Est-ce qu'on a deux mots pour la même chose ?

---

## Termes à définir (liste de départ)

- **Job** — 
- **Corpus** — 
- **Agent** — 
- **Boss** — 
- **Routing** — 
- **Synthesis** — 
- **Sentinel** — 
- **Proposal** — 
- **Company** — 
- **Conversation** — 
- **Pinned** — 
- **Apprentissage** — 
- **Sample** — 
- **Test session** — 
- **Inference mode** — 

## Termes V2-Mémoire (ajoutés 2026-06-21)

- **Handoff** — transition automatique déclenchée quand une conversation atteint son seuil (tokens ou nombre de messages). La conversation est archivée, une nouvelle est créée, l'utilisateur continue sans interruption visible.
- **Session** — ensemble de conversations liées par `previous_conversation_id`. Une session = un fil de travail continu sur un sujet, découpé en plusieurs conversations pour maîtriser la taille du contexte.
- **Bilan ARCHIVISTE** — JSON à 5 clés (`sujet_principal`, `decisions_prises`, `informations_cles`, `questions_ouvertes`, `prochaine_etape`) produit par l'agent ARCHIVISTE à chaque archivage. Réinjecté dans le routing de la conversation suivante.
- **RAG bicéphale** — double retrieval à chaque routing : `kb_documents` (top_k=3, documents clients) + `session_memory` (top_k=1, bilans de sessions passées). Les deux sources sont injectées séparément dans le prompt avec des labels distincts.
- **Trigger** — cause d'un archivage. Valeurs possibles : `token_threshold` (seuil de tokens estimés atteint), `message_threshold` (seuil de messages utilisateur atteint), `manual` (bouton Archiver dans l'UI).
- **Session memory** — collection ChromaDB distincte (`session_memory`) qui stocke les bilans ARCHIVISTE sous forme d'embeddings. Séparée de `kb_documents` (documents clients).
