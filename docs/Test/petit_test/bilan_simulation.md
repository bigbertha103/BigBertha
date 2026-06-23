---
# Bilan simulation Big Bertha — 2026-06-22 17:53
## Configuration
- Corpus : C:\Users\v.coutry\Dev\Projects\BigBertha\docs\Test\petit_test
- Durée par jour : 60s
- Jours simulés : 3
- Conversation id : 1

## Évolution des scores SENTINEL

| Jour | Score | routing_coherence | pinned_rate | kb_citation_rate | Proposals approuvées |
|---|---|---|---|---|---|
| J1  | 55   | 0.65             | 0.22       | 0.42            | 1                   |
| J2  | 60   | 0.68             | 0.28       | 0.48            | 1                   |
| J3  | 50   | 0.62             | 0.25       | 0.45            | 1                   |

## Progression globale
Score J1 → J3 : -5 points (-9%)
routing_coherence J1 → J3 : -0.03 (-5%)
pinned_rate J1 → J3 : +0.03 (+14%)
kb_citation_rate J1 → J3 : +0.03 (+7%)

## Observations clés par jour

### Jour 1
Les agents ont produit des réponses cohérentes et pertinentes pour les tâches assignées, indiquant une certaine maturité dans la compréhension des besoins métier.

### Jour 2
Les agents ont produit des réponses cohérentes et pertinentes pour les tâches assignées, indiquant une certaine maturité dans la compréhension des besoins métier. Les requêtes transversales ont été bien gérées par les résolveurs de conflict.

### Jour 3
Les agents ont continué à produire des réponses cohérentes et pertinentes pour les tâches assignées, ce qui indique une maturité dans la compréhension des besoins métier.

## Proposals approuvées (impact sur l'équipe)

- J1 : UPDATE_AGENT_PROMPT sur ANALYSTE — Cette mise à jour s'inspire de l'observation que les réponses de l'agent sont souvent pertinentes mais manquent de détails, ce qui peut être corrigé avec une prompt adaptée.
- J2 : UPDATE_AGENT_PROMPT sur ANALYSTE — Justification générée par le LLM (texte invalide lors du run de test).
- J3 : UPDATE_COMPANY_RULE sur  — Les observations récentes des jobs analysés ont révélé la nécessité de mettre en place de nouvelles règles métier pour améliorer la qualité des réponses et la construction de la base de connaissance.

## Conclusion
Progression modérée — enrichir le corpus
