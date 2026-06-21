---
# Bilan simulation Big Bertha — 2026-06-21 10:48
## Configuration
- Corpus : C:\DEV\PROJETS\intelligence_artificielle\Big Bertha\docs\petit_test
- Durée par jour : 60s
- Jours simulés : 3
- Conversation id : 1

## Évolution des scores SENTINEL

| Jour | Score | routing_coherence | pinned_rate | kb_citation_rate | Proposals approuvées |
|---|---|---|---|---|---|
| J1  | 45   | 0.60             | 0.20       | 0.40            | 2                   |
| J2  | 50   | 0.70             | 0.15       | 0.50            | 2                   |
| J3  | 55   | 0.80             | 0.10       | 0.60            | 2                   |

## Progression globale
Score J1 → J3 : +10 points (+22%)
routing_coherence J1 → J3 : +0.20 (+33%)
pinned_rate J1 → J3 : -0.10 (-50%)
kb_citation_rate J1 → J3 : +0.20 (+50%)

## Observations clés par jour

### Jour 1
Les agents ne semblent pas utiliser de manière cohérente les informations contenues dans la base de connaissances. Il y a un manque de citations et de références aux documents indexés.

### Jour 2
Les agents semblent maintenant utiliser plus efficacement les informations contenues dans la base de connaissances, avec une augmentation de 25% du taux de citation de la KB.

### Jour 3
Les agents semblent maintenant utiliser de manière plus cohérente les informations contenues dans la base de connaissances, avec une augmentation de 50% du taux de citation de la KB.

## Proposals approuvées (impact sur l'équipe)

- J1 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les agents doivent fournir des analyses plus détaillées et citer les sources appropriées pour garantir la qualité et la précision de leurs réponses.
- J1 : UPDATE_AGENT_PROMPT sur REDACTEUR — Les agents doivent fournir des résumés plus détaillés et se baser sur des sources appropriées pour garantir la qualité et la précision de leurs réponses.
- J2 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les agents ont besoin d'une meilleure guidance sur la façon de fournir des réponses plus détaillées et de mieux intégrer les informations de la base de connaissances dans leurs réponses.
- J2 : UPDATE_COMPANY_RULE sur  — 
- J3 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les agents analystes pourraient bénéficier d'un système prompt plus spécifique pour les tâches d'analyse, en mettant l'accent sur l'utilisation de la base de connaissances et la fourniture de réponses détaillées.
- J3 : UPDATE_COMPANY_RULE sur  — 

## Conclusion
Progression modérée — enrichir le corpus
