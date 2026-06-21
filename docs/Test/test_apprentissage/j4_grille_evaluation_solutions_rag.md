# Grille d'évaluation — Solutions RAG on-premise pour ETI

## Objectif
Cette grille structure la recommandation d'une solution RAG on-premise pour un client ETI. Elle est utilisée en Phase 0 (qualification) des missions Neuraltech pour objectiver le choix technologique.

## Frameworks évalués
LlamaIndex, LangChain, solution custom (Python + ChromaDB + fastembed). Note : les solutions cloud-dépendantes (Azure OpenAI on your data, AWS Bedrock Knowledge Bases) sont exclues de cette grille — hors périmètre on-premise.

---

## Critère 1 — Facilité de déploiement on-premise (poids : 20%)

| Sous-critère | LlamaIndex | LangChain | Custom |
|---|---|---|---|
| Installation sans dépendances cloud | ★★★★☆ | ★★★☆☆ | ★★★★★ |
| Documentation disponible | ★★★★☆ | ★★★★★ | N/A (interne) |
| Nombre de dépendances | 12-18 packages | 25-40 packages | 5-8 packages |
| Facilité de mise à jour | Modérée | Complexe | Contrôlée |

---

## Critère 2 — Flexibilité et personnalisation (poids : 25%)

| Sous-critère | LlamaIndex | LangChain | Custom |
|---|---|---|---|
| Sources de données supportées | Multi (PDF, Word, CSV, DB) | Multi | Selon développement |
| Stratégies de chunking | Riches (semantic, sentence, fixed) | Riches | Liberté totale |
| Pipeline modulaire | Oui | Oui | Oui |
| Re-ranking personnalisé | Oui (intégré) | Oui | À développer |

---

## Critère 3 — Performance et scalabilité (poids : 30%)

| Sous-critère | LlamaIndex | LangChain | Custom |
|---|---|---|---|
| Latence requête RAG (P50) | ~300ms | ~350ms | ~200-250ms |
| Indexation 100k documents | 2-4h | 3-5h | 1-2h |
| Scalabilité horizontale | Difficile sans orchestration | Difficile | Maîtrisée |
| Consommation mémoire | Modérée | Élevée | Faible |

---

## Critère 4 — Maintenance et pérennité (poids : 25%)

| Sous-critère | LlamaIndex | LangChain | Custom |
|---|---|---|---|
| Communauté et mises à jour | Active, roadmap stable | Très active, roadmap instable | N/A |
| Risque de breaking changes | Moyen (1-2 majeures/an) | Élevé (historique de ruptures) | Nul |
| Compétences requises en maintenance | Python + docs LlamaIndex | Python + docs LangChain | Python expert |
| Coût de formation équipe client | Faible | Moyen | Élevé |

---

## Recommandation Neuraltech par profil client

### ETI < 200k documents, équipe technique légère
**→ LlamaIndex** : bon équilibre fonctionnalités/simplicité. Documentation suffisante pour une équipe IT interne. Maintenance accessible sans expertise RAG profonde.

### ETI > 200k documents avec équipe Python interne
**→ Solution custom sur ChromaDB + fastembed** : performances supérieures, contrôle total sur les stratégies d'indexation et de recherche. Idéal quand les spécificités du corpus (multilangue, données structurées + texte) nécessitent une personnalisation poussée.

### À éviter systématiquement pour les projets long terme
**→ LangChain** : historique de breaking changes nuisible à la maintenabilité. Excellent pour des prototypes, problématique pour des systèmes en production sur 2+ ans.

---

## Grille de scoring (à compléter pour chaque prospect)

| Critère | Poids | Score LlamaIndex | Score LangChain | Score Custom |
|---|---|---|---|---|
| Facilité déploiement | 20% | _ | _ | _ |
| Flexibilité | 25% | _ | _ | _ |
| Performance | 30% | _ | _ | _ |
| Maintenance | 25% | _ | _ | _ |
| **Score total** | 100% | **_** | **_** | **_** |
