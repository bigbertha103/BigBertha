# Orchestration et gouvernance des agents IA

## Projets et repos de référence

- **OpenRouter** — intégration OpenAI-compatible pour nombreux modèles, routage multi-fournisseurs
- **Local LLaMA Server Setup Documentation** — doc pratique sur local inference, RAG, MCP, gestion de modèles
- **AI-Agent-Governance-Toolkit** — gouvernance hiérarchique pour coordination d'agents
- **awesome-multi-agent-orchestrators** — liste curatée de runtimes, orchestrateurs et couches de gouvernance
- **claude-hybrid-router** — exemple de routage hybride entre modèles premium et modèles locaux

## Modules à prévoir dans une plateforme d'orchestration

| Module | Rôle |
|---|---|
| Router LLM | Sélectionner le bon modèle selon tâche, coût, latence, sensibilité |
| Policy engine | Appliquer les règles de gouvernance avant exécution |
| Memory store | Persister la mémoire par tenant, équipe, projet |
| Tool executor | Exécuter les outils appelés par les agents |
| Model registry | Gérer le catalogue des modèles disponibles (cloud + local) |
| Eval harness | Mesurer la qualité des réponses par tâche |
| Human approval layer | Valider les actions à risque avant exécution |
| Observability & billing | Monitorer coûts, latence, erreurs, usage |

## Principes de gouvernance avant exécution

La gouvernance ne doit pas être un afterthought. Elle doit être intégrée dans le flux d'orchestration :

1. **Classification de la requête** — données sensibles ou non ?
2. **Application de la politique** — quel modèle est autorisé pour ce niveau de sensibilité ?
3. **Budget check** — le quota de tokens/coût est-il disponible ?
4. **Approbation humaine** — pour les actions irréversibles ou à fort impact
5. **Audit log** — traçabilité complète de chaque décision d'orchestration

## Mémoire multi-niveau

La mémoire d'un agent IA d'entreprise doit être structurée en 3 niveaux :
- **Mémoire de session** : contexte de la conversation en cours (in-context)
- **Mémoire court terme** : informations récentes de la semaine ou du projet
- **Mémoire entreprise** : base de connaissance persistante, partagée par l'équipe

Le cloisonnement par tenant est non négociable en mode multi-entreprise.

## Défis d'orchestration multi-agents

- Cohérence entre agents spécialisés qui partagent un contexte
- Éviter les boucles infinies (deadlocks, appels circulaires)
- Gérer les échecs partiels sans perdre l'état de la mission
- Limiter les hallucinations en cascade (erreur d'un agent propagée aux suivants)
