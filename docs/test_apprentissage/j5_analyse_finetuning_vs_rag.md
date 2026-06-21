# Analyse comparative : Fine-tuning vs RAG pour la classification documentaire bancaire en français

## Contexte de l'analyse
Cette analyse s'applique à un cas d'usage courant en banque et assurance : la classification automatique de documents entrants (bilans comptables, RIBs, justificatifs de domicile, contrats de prêt) avec extraction d'informations clés (montants, dates, noms, ratios).

## Synthèse des trade-offs

| Critère | RAG | Fine-tuning |
|---|---|---|
| **Délai de mise en œuvre** | 2-4 semaines | 6-12 semaines |
| **Coût initial** | Faible (embedding + infra stockage) | Élevé (GPU training, data labeling : 10-50k€) |
| **Qualité sur données stables** | Bonne (85-90% de précision) | Excellente (90-97% si données labellisées de qualité) |
| **Adaptabilité à de nouveaux types de docs** | Immédiate (re-indexation uniquement) | Nécessite un nouveau cycle de fine-tuning (4-8 sem.) |
| **Explicabilité des décisions** | Bonne — les sources sont citées | Faible — boîte noire |
| **Conformité IA Act (systèmes haut risque)** | Facilitée par la traçabilité | Plus complexe (documentation de l'entraînement) |
| **Coût de maintenance** | Faible (re-indexation incrémentale) | Élevé (re-training tous les 6-12 mois) |
| **Robustesse aux données hors-distribution** | Modérée | Faible sans données d'entraînement représentatives |

## Recommandation pour la classification documentaire bancaire

**Recommandation : RAG avec extraction structurée**, avec les justifications suivantes :

### 1. Délai
La banque a besoin de résultats en semaines, pas en mois. Le RAG permet une mise en production en 4-6 semaines vs 3-4 mois pour un fine-tuning complet (incluant la production des données labellisées).

### 2. Adaptabilité réglementaire
Les types de documents bancaires évoluent (nouvelles normes comptables IFRS, nouveaux formulaires réglementaires). Le RAG absorbe ces changements par re-indexation des nouveaux documents sans re-training.

### 3. Conformité IA Act
L'article 10 de l'IA Act classe les systèmes d'évaluation de solvabilité comme systèmes à haut risque. La traçabilité des sources (RAG) facilite l'audit trail et la documentation obligatoire.

### 4. Coût total sur 2 ans
Estimation sur un corpus de 5000 documents/mois :
- RAG : ~25k€ (infra) + 5k€/an maintenance = 35k€ sur 2 ans
- Fine-tuning : ~60k€ (data labeling + training) + 25k€/an maintenance = 110k€ sur 2 ans

## Cas où le fine-tuning reste pertinent

- **Tâche très spécifique et stable** : classification d'un type de document unique avec format immuable (ex : extraction structurée d'un formulaire propriétaire figé).
- **Volume de données labellisées suffisant** : > 10k exemples de qualité disponibles.
- **Latence critique** : un petit modèle fine-tuné (1-7B) peut répondre en < 50ms, vs 200-400ms pour un RAG complet — pertinent pour les traitements temps réel en caisse ou scoring instantané.

## Approche hybride (recommandée pour les cas mixtes)
Fine-tuning d'un petit modèle pour la **classification** (tâche stable, haute fréquence, latence critique) + RAG pour l'**extraction de contexte** (tâche variable, sources documentaires changeantes). Les deux s'alimentent mutuellement.

## Limite de cette analyse
Cette comparaison est valide pour la classification documentaire. Pour de la génération longue (synthèse de dossier, rédaction de fiches) ou du Q&A ouvert, le RAG reste quasi-systématiquement recommandé.
