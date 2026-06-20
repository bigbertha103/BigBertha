# Opportunités produit et roadmap de veille

## Idées de fonctions produit prioritaires

### Fonctions cœur
- **Sélecteur de modèle automatique** selon sensibilité des données et coût
- **Agent supervisor** pour valider les actions à risque avant exécution
- **Mode local-only** : aucun appel vers des API externes
- **Mode hybrid-cloud** : cloud pour données publiques, local pour données sensibles
- **Journal d'audit exportable** : logs complets des prompts, décisions, modèles

### Qualité et évaluation
- **Evaluation runner** : jeu de test interne par métier, exécutable à tout moment
- **Knowledge base entreprise** : base documentaire RAG par tenant
- **Détection de dérive comportementale** : alerter si les réponses dérivent de la qualité de référence

### Opérationnel
- **Connecteurs API internes** : ERP, CRM, SIRH, outils métier
- **Quotas par équipe** : budget tokens/coût par département
- **Policy engine compatible JSON/YAML** : règles de gouvernance configurables sans code
- **Gestion multi-tenant** : une instance, N entreprises cloisonnées

## Plan de veille recommandé

### Hebdomadaire
1. Sorties de nouveaux modèles et benchmarks (Hugging Face leaderboard, LMSYS)
2. Annonces GPU et supply chain RAM/HBM (prix mémoire)
3. Nouvelles offres concurrentes (OpenAI, Anthropic, Google, Mistral)

### Mensuel
4. Cartographier les concurrents par couche de stack (modèles / serving / orchestration / gouvernance)
5. Identifier les modèles open-weight adaptés au déploiement local
6. Tester les nouvelles sorties sur corpus métier interne

### Par trimestre
7. Mesurer qualité, coût, latence, énergie et conformité sur jeu de test de référence
8. Mettre à jour la grille de recommandation modèle par cas d'usage
9. Réviser la roadmap produit selon l'évolution du marché

## Ressources à conserver

### Code et outils
- [OpenRouter examples](https://github.com/OpenRouterTeam/openrouter-examples) — intégration multi-modèles
- [llm-server-docs](https://github.com/varunvasudeva1/llm-server-docs) — local inference RAG MCP
- [AI Agent Governance Toolkit](https://github.com/socragpt/AI-Agent-Governance-Toolkit) — gouvernance agents
- [awesome-multi-agent-orchestrators](https://github.com/Agent-Analytics/awesome-multi-agent-orchestrators) — liste runtimes

### Produits et stacks de référence
- **EDB AI Factory** — architecture hybride Postgres + vector + orchestration
- **ibl.ai air-gapped** — exemple enterprise sans API externe
- **Northflank** — infrastructure déploiement IA scalable
- **VDF AI Enterprise Stack** — référence 7 couches pour stack local

## Synthèse stratégique

Le marché IA 2026 est caractérisé par :
- **Consolidation du cloud** : OpenAI, Anthropic, Google dominent les API
- **Émergence du local** : Llama, Mistral, DeepSeek rendent le déploiement local viable
- **Pression réglementaire** (EU AI Act, RGPD) qui pousse vers la souveraineté
- **Contraintes matérielles** (pénurie GPU, mémoire, énergie) qui poussent à l'efficacité

**La fenêtre d'opportunité pour un produit souverain + orchestration multi-modèle + gouvernance est ouverte.** Les grands acteurs cloud ne peuvent pas répondre aux exigences de souveraineté des entreprises sensibles. Les solutions open-source manquent de gouvernance et d'intégration enterprise.
