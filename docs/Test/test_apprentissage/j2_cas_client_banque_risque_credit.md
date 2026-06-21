# Cas client — Banque Lumière : Automatisation de l'analyse de risque crédit

## Contexte client
**Client** : Banque Lumière (anonymisé), banque de proximité, 400 collaborateurs, 3 régions.
**Secteur** : Banque de détail et financement des entreprises locales.
**Problème** : L'équipe risque (6 analystes) passe 60% de son temps à synthétiser des documents hétérogènes (bilans comptables, relevés bancaires, rapports sectoriels) pour produire des fiches de risque crédit. Le délai moyen d'instruction est de 12 jours. La direction veut atteindre 5 jours pour rester compétitive face aux fintechs.

## Solution POC proposée par Neuraltech

**Architecture** : RAG sur les documents de chaque dossier (injection du contexte documentaire dans le LLM) combiné à un agent d'extraction structurée des indicateurs clés (ratios financiers, signaux d'alerte).

**Modèle sélectionné** : Qwen 2.5 32B (qualité français, licence commerciale, on-premise possible).

**Infrastructure POC** : Serveur GPU client existant (A100 40GB), ChromaDB pour l'indexation, pipeline Python Neuraltech.

## Données du POC
- 150 dossiers historiques anonymisés : bilans comptables, relevés bancaires 12 mois, rapports sectoriels
- 30 dossiers de test avec notation risque réelle (label ground truth fourni par les analystes)
- Formats : PDF natif (80%), PDF scanné (20%)

## Critère de succès
Concordance entre la fiche risque produite par l'agent et la notation des analystes experts ≥ 80% sur les 30 dossiers de test.

## Résultats obtenus (POC terminé en 7 semaines)

**Benchmark final : concordance 83%** — critère de succès atteint ✅

Résultats détaillés :
- L'agent identifie les ratios clés correctement dans 92% des cas (endettement, couverture des intérêts, fonds de roulement)
- Réduction du temps de synthèse estimée : de 4h à 35 min par dossier (observation sur 15 dossiers en conditions réelles)
- Les analystes pilotes évaluent la qualité des synthèses à 8,2/10 en moyenne

## Points d'attention identifiés
- Les documents sectoriels récents (post-2024) issus de PDF scannés étaient mal OCRisés — les chiffres clés étaient parfois manquants. Résolu en semaine 4 avec intégration Tesseract v5.
- Les tableaux HTML embarqués dans certains PDF de rapports sectoriels ne sont pas encore couverts — à traiter en phase production.
- La Directrice des Risques souhaite une fonctionnalité d'explicabilité (facteurs déterminants de la notation) — hors scope POC, à chiffrer.

## Prochaines étapes
- **Comité de décision Go/No-Go** : 15 juillet 2026
- **Si Go** : proposition phase production incluant OCR renforcé, explicabilité, et revue conformité IA Act (système à haut risque — article 10)
- **Délai estimé vers production** : 4-6 mois selon scope retenu
