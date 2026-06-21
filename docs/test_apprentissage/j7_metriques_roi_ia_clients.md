# Métriques ROI — Déploiements agents IA Neuraltech H1 2026

**Périmètre** : 6 missions Neuraltech ayant atteint le stade production ou fin de POC validée en H1 2026.  
**Méthodologie** : mesures réalisées en mission sur des échantillons de tâches (avant/après déploiement), sur 2 à 4 semaines d'observation. Les noms clients sont anonymisés.  
**Usage** : ces métriques servent d'ordre de grandeur dans les propositions commerciales — toujours accompagnées d'hypothèses explicites.

---

## Tableau de synthèse des missions H1 2026

| Mission | Secteur | Type d'agent | Réduction temps tâche cible | Volume mensuel estimé | ROI estimé 12 mois |
|---|---|---|---|---|---|
| Banque Lumière (POC validé) | Banque | Analyse risque crédit RAG | -75% | 120 dossiers/mois | 340% |
| RetailCo (POC validé) | Retail | Classification tickets SAV | -60% | 800 tickets/mois | 280% |
| IndustryCo (production) | Industrie | Recherche documentaire maintenance | -50% | 300 requêtes/jour | 190% |
| AssurancePro (production) | Assurance | Extraction contrats (clauses, dates) | -65% | 250 contrats/mois | 410% |
| LogisticsCo (POC validé) | Logistique | Traitement emails fournisseurs | -40% | 1500 emails/mois | 150% |
| RetailGroup (production) | Retail | Assistant merchandising RAG | +25% temps terrain libéré | 50 chefs de rayon | 220% |

---

## Analyse par secteur

### Banque et assurance — ROI moyen observé : 375%
Le potentiel est élevé pour trois raisons convergentes :
- Les tâches documentaires à haute valeur ajoutée (analyse de risque, extraction contractuelle, conformité) sont très chronophages et occupent des profils coûteux (juristes, analystes risque).
- Les critères de succès sont factuellement mesurables (concordance, précision d'extraction).
- L'IA Act renforce la valeur perçue des solutions avec traçabilité et explicabilité — un avantage structurel du RAG.

**Limite** : le ROI est sensible à la qualité des documents sources. Les PDF scannés de mauvaise qualité peuvent réduire le ROI de 30 à 50%.

### Retail — ROI moyen observé : 250%
Les gains se font principalement sur le volume (grand nombre de tickets, fiches produits, emails à traiter). Le ROI est plus sensible à la qualité de la KB que dans les autres secteurs — la fraîcheur des données est critique.

**Limite** : le ROI chute rapidement si le processus de mise à jour de la KB n'est pas opérationnel. Observé sur 1 projet retail : perte de 60% du ROI en 3 mois faute de mise à jour.

### Industrie et logistique — ROI moyen observé : 170%
Les gains sont réels mais plus progressifs. La résistance au changement des opérationnels (techniciens, acheteurs) est un facteur de ralentissement fréquent. Le ROI monte avec le temps d'adoption.

---

## Facteurs amplificateurs du ROI (classés par impact)

### 1. Volume de tâches (impact : très élevé)
Le ROI est fortement lié au volume de tâches automatisées. Seuil de rentabilité estimé :
- Agent documentaire : > 100 unités/mois (dossiers, contrats, tickets)
- Assistant RAG : > 30 utilisateurs actifs/jour

En dessous de ces seuils, le coût d'infrastructure et de déploiement dépasse les gains opérationnels à 12 mois.

### 2. Valeur unitaire de la tâche automatisée (impact : très élevé)
Un analyste risque bancaire facturé 200€/h qui gagne 3h par dossier génère un ROI bien supérieur à un assistant commercial qui gagne 20 min par email. L'agent doit être déployé sur les tâches à haute valeur unitaire en priorité.

### 3. Qualité initiale de la KB (impact : élevé)
Chaque point de qualité de la KB se traduit directement en qualité de réponse agent. Une KB à 70% de fraîcheur → performances dégradées → adoption en chute.

### 4. Taux d'adoption utilisateurs (impact : élevé)
Un agent utilisé à 40% de son potentiel génère 40% du ROI. La formation et l'accompagnement au changement sont des investissements ROI, pas des coûts.

---

## Recommandations d'utilisation de ces métriques

Ces chiffres sont des ordres de grandeur issus de cas réels. Avant de les utiliser dans une proposition commerciale :
1. Adapter les hypothèses au volume réel du client (ne jamais utiliser le ROI d'un client 10× plus grand).
2. Être explicite sur les hypothèses de réduction de temps (mesurées ou estimées).
3. Toujours inclure le délai de constatation du ROI — en général, 2 à 4 semaines après déploiement pour les agents documentaires.
4. Ne jamais promettre un ROI spécifique sans avoir mesuré la tâche cible en Phase 0.
