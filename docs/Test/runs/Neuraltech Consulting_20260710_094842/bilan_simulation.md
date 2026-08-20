---
# Bilan simulation Big Bertha — 2026-07-10 10:10
## Configuration
- Corpus : V:\DEV\PROJETS\intelligence_artificielle\Big Bertha\docs\Test\runs\Neuraltech Consulting_20260710_094842
- Durée par jour : 0s
- Jours simulés : 14
- Conversation id : 2

## Évolution des scores SENTINEL

| Jour | Score | routing_coherence | pinned_rate | kb_citation_rate | Proposals approuvées |
|---|---|---|---|---|---|
| J1  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J2  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J3  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J4  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J5  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J6  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J7  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J8  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J9  | 45   | 0.60             | 0.00       | 0.00            | 1                   |
| J10  | 45   | 0.60             | 0.05       | 0.00            | 1                   |
| J11  | 45   | 0.60             | 0.05       | 0.00            | 1                   |
| J12  | 45   | 0.60             | 0.09       | 0.00            | 1                   |
| J13  | 45   | 0.60             | 0.08       | 0.00            | 1                   |
| J14  | 50   | 0.65             | 0.11       | 0.00            | 2                   |

## Progression globale
Score J1 → J14 : +5 points (+11%)
routing_coherence J1 → J14 : +0.05 (+8%)
pinned_rate J1 → J14 : +0.11 (N/A)
kb_citation_rate J1 → J14 : +0.00 (N/A)

## Observations clés par jour

### Jour 1
Les agents semblent souvent fournir des réponses qui ne sont pas spécifiques aux demandes posées. Par exemple, dans Job #3, l'analyse combinait les capacités de codage et de raisonnement de GPT-5.4 sans vraiment répondre clairement à la tâche qui consistait à comparer spécifiquement les forces et spécificités techniques des modèles GPT-5.4 et Claude Opus.

### Jour 2
Les agents n'ont pas réussi à fournir des réponses concrètes et pertinentes aux tâches données. Par exemple, dans les jobs #4 et #5, les agents ont du mal à répondre clairement à l'impact de la pénurie de semiconducteurs et de puces mémoire sur les coûts et choix d'infrastructures. Elles sont plus centrées sur la description des troubles économiques généraux plutôt que de proposer des solutions tangibles pour l'entreprise.

### Jour 3
Dans les deux jobs analysés, les agents fournissent des informations techniques pertinentes mais elles sont souvent déconnectées du contexte métier spécifique de Neuraltech Consulting. Par exemple, dans Job #7, le critère de la bande passante comme facteur critique pour le déploiement des LLM est pertinente, mais il n'est pas clairement lié au contexte métier de l'entreprise cliente.

### Jour 4
Les agents continuent d'ailleurs à fournir des réponses qui ne sont pas spécifiquement contextuelles pour la demande de l’entreprise cliente dans leurs jobs, ce qui révèle une absence de lien direct avec les besoins métiers. Par exemple, dans Job #9 et Job #8, bien que les réponses fournissent des informations techniques pertinentes, elles n’offrent pas de perspectives commerciales ou stratégiques utiles.

### Jour 5
Les agents ont mal fichu la mort à la tâche de Job #11, où ils n'ont pas explicitement formulé leurs besoins spécifiques pour la configuration des politiques et la segmentation des utilisateurs par tenant et équipe. La réponse était vague et générale.

### Jour 6
Les réponses des agents ne restent pas focalisées sur les demandes spécifiques des clients. Par exemple, dans Job #13, l'agent a fourni une description générale de la containerisation sans vraiment répondre au besoin de vérifier la souveraineté sur l'infrastructure Kubernetes. Dans Job #12, le contexte manque complètement concernant l'AI Factory d'EDB.

### Jour 7
Les réponses des ANALYSTE ont été généralisées et peu ciblées dans les deux jobs récents, bien que le subject de Job #15 soit apparentemment lié à l'architecture et la containerisation, il n'y a pas eu de lien direct avec l'analyse des contraintes mémoire jusqu'en 2027. Job #14, qui devrait déboucher sur un choix stratégique entre déploiement en cloud et local via des coûts et avantages, manque de cette perspective stratégique claire.

### Jour 8
Dans Job #17, l'analyse de la viabilité de l'utilisation de Grok pour du writing non-censuré se termine par une sorte de résumé des coûts et avantages, mais ne fait pas clairement le lien avec les besoins spécifiques de souveraineté des données de l'entreprise client. Cette réponse manque d'une perspective stratégique et commerciale.

### Jour 9
Dans Job #18, l'analyse de Grok en fonction de SWE-bench a été conduite de manière pertinente, soulignant la performance accrue de Grok par rapport à GPT-5.4. Cependant, malgré cette analyse technique précise, elle n'a pas fait directement le lien avec la capacité d'un agent à écrire du code pour Neuraltech Consulting, manquant ainsi de mettre en avant l'impact opérationnel potentiel.

### Jour 10
Dans les deux jobs de la période courante, les réponses fournies ne sont pas complètement inspirées par les besoins spécifiques de l'entreprise Neuraltech Consulting. Les agents se concentrent sur la fourniture de base de la réponse technique plutôt que de répondre directement à la tâche assignée et de intégrer des éléments stratégiques advant de l'entreprise. Par exemple, dans Job #20, l'analyse de tracking pour assurer la compliance lors de l'audit manque d'contextualisation métier qui pourrait être cruciale pour l'entreprise.

### Jour 11
Les deux jobs de la période courante montrent une certaine amélioration par rapport au baseline en matière de pertinence technique. Cependant, il reste difficile de générer des réponses adaptées aux besoins spécifiques de l'entreprise Neuraltech Consulting.

### Jour 12
Il est nettement appréciable que les agents aient amélioré la pertinence technicole des réponses, comme le montre Job #23, qui propose une logique d'orchestration adaptée aux besoins en termes de confidentialité. Cependant, Job #24 manque d'approfondissement et reste un peu vagues dans ses recommandations.

### Jour 13
Il est observable que les agents ont succédé à la progression signifiée par l'augmentation de la pertinence technique des réponses, comme dans Job #25 où leurs réponses sont clairement centrées sur la tâche assignée sans cependant intégrer pleinement les besoins métiers comme prévu par Neuraltech Consulting.

### Jour 14
Depuis le baseline, la réponse à Job #28 a montré une certaine pertinence technique par rapport à la demande assignée. Cependant, la réponse à Job #27 manquait d'approfondissement technique et n'intégrait pas suffisamment les besoins spécifiques de l'entreprise.

## Proposals approuvées (impact sur l'équipe)

- J1 : UPDATE_AGENT_PROMPT sur ANALYSTE — Il est crucial que les agents fournissent des analyses qui répondent directement aux demandes et qui sont pertinentes pour le contexte métier de l'entreprise cliente.
- J2 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les observations montrent qu'il est crucial pour les agents de fournir des analyses concrètes et pertinentes qui répondent directement aux besoins de l'entreprise. Cet update promet de mieux guider les agents dans leur production pour qu'ils offrent des analyses précises et applicables.
- J3 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les données montrent que les agents ne parviennent pas à connecter leurs analyses techniques aux impacts concrets pour l'entreprise. Une mise à jour du prompt aidera à clarifier cette exigence.
- J4 : UPDATE_COMPANY_RULE sur  — Les observations font état d'une absence de lien clair entre les analyses technique et les besoins métiers de l'entreprise cliente. Ces règles visent à clarifier les attentes en matière de production.
- J5 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les agents ont échoué à fournir des réponses contextuelles pour les besoins d'Neuraltech Consulting dans Job #11 et Job #10. Cette mise à jour du prompt vise à clarifier leur objectif et odierance envers le contexte job.
- J6 : UPDATE_AGENT_PROMPT sur ANALYSTE — 
- J7 : UPDATE_AGENT_PROMPT sur ANALYSTE — Ce system prompt souligne l'importance de contextualiser les analyses techniques dans le cadre des attentes et besoins métier de l'entreprise cliente, ce qui entraînera des réponses plus pertinentes et pertinentes.
- J8 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les observations montrent une absence récurrente de lien avec les besoins spécifiques de l'entreprise cliente et une perspective stratégique insuffisante dans les analyses techniques. Cette mise à jour du prompt devrait encourager les agents à prendre en compte ces aspects dans leurs recommandations.
- J9 : UPDATE_AGENT_PROMPT sur ANALYSTE — Cette mise à jour de l'agent promp souligne l'importance de la contextualisation métier et stratégique dans les analyses techniques, ce qui est manquant dans les performances actuelles.
- J10 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les agents ont tendance à fournir des réponses techniques qui ne sont pas suffisamment contextualisées et qui ne font pas le lien avec les attentes de l'entreprise. En revanche, ils se concentrent davantage sur la fourniture de base de la réponse technique.
- J11 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les agents manquent de compréhension contextuelle et de linkage avec les attentes de l'entreprise. Une mise à jour de l'agent prompt peut aider à corriger cela.
- J12 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les analyses techniques manquent de contexte métier spécifique, il est nécessaire de clarifier la mission des agents pour qu'ils prennent en compte les besoins commerciaux et stratégiques.
- J13 : UPDATE_AGENT_PROMPT sur ANALYSTE — Les analyses techniques doivent être spécifiquement alignées sur les besoins métiers, ce prompt aidera à garantir que les solutions étaient optimisées pour le client.
- J14 : UPDATE_AGENT_PROMPT sur ANALYSTE — Cette révision du prompt pour l'analyste est nécessaire pour augmenter le lien entre les analyses techniques et les attentes de l'entreprise.
- J14 : UPDATE_COMPANY_RULE sur  — Cette mise en place d'une règle claire vise à améliorer la pertinence des analyses techniques par rapport aux besoins de l'entreprise.

## Conclusion
Progression modérée — enrichir le corpus
