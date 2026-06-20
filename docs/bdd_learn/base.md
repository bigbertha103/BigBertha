# Veille IA - orchestration d’agents, souveraineté, infra et marché

## 1) Objectif produit

Construire une plateforme d’orchestration d’agents IA capable de fonctionner :
- via API cloud (OpenAI, Anthropic, OpenRouter, etc.).
- via modèles locaux exécutés sur GPU internes.
- dans des environnements souverains, isolés ou air-gapped.
- avec mémoire, apprentissage opérationnel et spécialisation métier pour entreprise.

Ce positionnement est cohérent avec les architectures d’IA souveraine qui insistent sur le contrôle local du plan de contrôle, la résidence des données et l’exécution des inférences dans le périmètre client [web:7][web:1].

## 2) Architecture et souveraineté

### Références utiles
- [AI Factory Architecture on Hybrid Manager v1.3](https://www.enterprisedb.com/docs/edb-postgres-ai/latest/hybrid-manager/ai-factory/architecture/) — architecture containerisée orientée souveraineté et exécution sur clusters Kubernetes contrôlés par le client [web:1].
- [The Enterprise Local AI Stack: Models, Serving, RAG, Orchestration, Governance](https://vdf.ai/resources/enterprise-local-ai-stack/) — découpe très utile en 7 couches pour penser un stack local entreprise [web:4].
- [Sovereign AI Infrastructure Guide](https://www.rack2cloud.com/ai-infrastructure-strategy-guide/) — insiste sur contrôle local, résidence des données et absence de dépendance à un control plane externe [web:7].
- [Air-Gapped AI for Corporate L&D](https://ibl.ai/service/air-gapped-ai/corporate) — exemple d’offre enterprise “no external API calls” avec exécution locale sur serveurs GPU [web:10].

### Points d’architecture à intégrer
- Routage multi-fournisseurs selon coût, latence, confidentialité et criticité.
- Sélection automatique du modèle selon tâche.
- Mémoire entreprise avec cloisonnement par tenant, équipe et projet.
- Journal d’audit complet des prompts, outils, versions de modèles et décisions.
- Gouvernance avant exécution : politiques, budgets, approbations, sandbox, révocation.

## 3) Orchestration et gouvernance

### Projets et repos à surveiller
- [OpenRouter examples](https://github.com/OpenRouterTeam/openrouter-examples) — intégration OpenAI-compatible pour nombreux modèles [web:11].
- [Local LLaMA Server Setup Documentation](https://github.com/varunvasudeva1/llm-server-docs) — doc pratique sur local inference, RAG, MCP, gestion de modèles [web:12].
- [AI-Agent-Governance-Toolkit](https://github.com/socragpt/AI-Agent-Governance-Toolkit) — gouvernance hiérarchique pour coordination d’agents [web:16].
- [awesome-multi-agent-orchestrators](https://github.com/Agent-Analytics/awesome-multi-agent-orchestrators) — liste curatée de runtimes, orchestrateurs et couches de gouvernance [web:19].
- [claude-hybrid-router](https://pkg.go.dev/github.com/peter-wagstaff/claude-hybrid-router) — exemple de routage hybride entre modèles premium et modèles locaux [web:17].

### Modules à prévoir dans votre produit
- Router LLM.
- Policy engine.
- Memory store.
- Tool executor.
- Model registry.
- Eval harness.
- Human approval layer.
- Observability et billing.

## 4) Moteurs locaux

### Repos et outils
- [llama.cpp](https://github.com/ggml-org/llama.cpp) — moteur de référence pour exécution locale, quantization et déploiement léger.
- [vLLM](https://github.com/vllm-project/vllm) — moteur haute performance pour serving d’inférence.
- [Ollama](https://github.com/ollama/ollama) — distribution simple pour exécuter des modèles localement.
- [TGI](https://github.com/huggingface/text-generation-inference) — serving production orienté Hugging Face.
- [vLLM / Ollama integration examples](https://github.com/sbhavani/ollama-vllm) — utile pour combiner simplicité et performance [web:15].

### Idée de stack locale
- Développement rapide : Ollama + RAG + orchestrateur.
- Production GPU : vLLM ou TGI.
- Edge ou machines modestes : llama.cpp.
- Air-gapped : modèle open-weight + serving local + gouvernance stricte.

## 5) Modèles intéressants

### Sources à suivre
- [AI Models in 2026: Which One Should You Actually Use?](https://gurusup.com/blog/ai-comparisons) — synthèse de benchmarks et usages par famille de modèle [web:6].
- [Top AI companies in 2026](https://northflank.com/blog/top-ai-companies) — panorama des acteurs clés de l’infrastructure IA [web:9].

### Familles de modèles à tester
- OpenAI pour raisonnement général et outillage.
- Anthropic pour rédaction, agents et tâches de programmation.
- Google Gemini pour raisonnement multimodal.
- Mistral, Qwen, DeepSeek, Llama, Phi, Gemma pour local/open-weight.
- Routing dynamique selon coût, latence et sensibilité des données.

### Critères d’évaluation
- Qualité de raisonnement.
- Qualité du code.
- Robustesse sur tâches longues.
- Coût par tâche.
- Latence.
- Empreinte mémoire.
- Facilité de quantization et de serving local.

## 6) Puces, GPU et concurrence matérielle

### Tendance matérielle
La course à l’IA pousse les fabricants à sortir des GPU plus rapides et plus gourmands en mémoire, avec une tension accrue sur HBM et DRAM [web:2][web:5].

### Références utiles
- [NVIDIA GPU Architectures for ML](https://theorempath.com/topics/nvidia-gpu-architectures) — aperçu H100, H200, B200, GB200 [web:21].
- [AMD Accelerates Pace of Data Center AI Innovation](https://www.amd.com/en/newsroom/press-releases/2024-6-2-amd-accelerates-pace-of-data-center-ai-innovation-.html) — MI350 annoncé avec forte progression d’inférence [web:22].
- [AMD MI325X / MI350 coverage](https://www.tomshardware.com/tech-industry/artificial-intelligence/amd-announces-mi325x-ai-accelerator-reveals-mi350-and-mi400-p...) — détails complémentaires sur la feuille de route AMD [web:25].
- [Blackwell B200 / GB200 coverage](https://www.generation-nt.com/actualites/nvidia-blackwell-architecture-b200-gpu-intelligence-artificielle-2045455) — compréhension des enjeux d’architecture et de consommation [web:24].
- [NVIDIA Blackwell video coverage](https://www.youtube.com/watch?v=urR5aBVs_NU) — présentation produit et positionnement stratégique [web:27].

### Ce que cela implique pour votre produit
- Optimiser pour plusieurs types de GPU, pas seulement NVIDIA.
- Prévoir profils de modèles selon VRAM disponible.
- Gérer la quantization et le fallback CPU.
- Intégrer des métriques de coût énergétique par requête.

## 7) RAM, mémoire et énergie

### Constats de marché
La pression sur les datacenters IA s’accompagne d’une forte demande en mémoire et en énergie électrique, avec des pénuries prolongées et des contraintes de capacité [web:2][web:5][web:8].

### Références
- [Memory chip shortage to last through 2027](https://www.cnbc.com/2026/01/26/memory-chip-shortage-synopsys-lenovo-ai-data-centers.html) — shortages de mémoire et hausse des prix [web:5].
- [Memory loss: As AI gobbles up chips](https://www.npr.org/2025/12/26/nx-s1-5656190/memory-loss-as-ai-gobbles-up-chips-prices-for-devices-may-rise) — impact sur RAM et appareils grand public [web:8].
- [After the Power Crunch, AI Infrastructure Hits a Silicon Wall](https://www.datacenterknowledge.com/infrastructure/after-the-power-crunch-ai-infrastructure-hits-a-gpu-wall) — contraintes sur fabrication, HBM et packaging [web:2].
- [IDC AI datacenter energy consumption report](https://my.idc.com/getdoc.jsp?containerId=prUS52611224) — projection forte croissance de la consommation d’énergie des datacenters IA [web:23].
- [Nature / IEA on data center energy](https://www.nature.com/articles/d41586-025-01113-z) — le sujet énergétique devient structurel [web:29].
- [Gartner power shortage coverage](https://www.networkworld.com/article/3603332/energy-shortages-threaten-to-restrict-40-of-ai-data-centers-by-2027.html) — contraintes possibles sur une large part des datacenters [web:26].

### Opportunités produit
- Prendre en compte coût énergétique dans le routage.
- Intégrer un mode “eco”.
- Préférer petits modèles sur tâches simples.
- Prédire la charge et lisser les pics.
- Ajouter du caching sémantique et du batching.

## 8) Recherche et optimisation

### Axes de recherche pertinents
- MoE et routage expert.
- Distillation de modèles lourds vers modèles spécialisés.
- Quantization agressive sans perte critique.
- Speculative decoding.
- Cache KV et réutilisation de contexte.
- RAG plus propre plutôt que fine-tuning systématique.
- Tool use + memory + retrieval pour améliorer la pertinence sans augmenter la taille du modèle.
- Monitoring automatique des taux d’hallucination et des coûts par tâche.

### Pistes d’implémentation
- Benchmarks internes par métier.
- Régression continue sur jeux de données métiers.
- Séparation entre mémoire à court terme, mémoire de session et mémoire d’entreprise.
- Apprentissage contrôlé via feedback humain et signaux d’usage.
- Versioning complet des prompts, outils et politiques.

## 9) Concurrents et acteurs

### Acteurs à suivre
- OpenAI.
- Anthropic.
- Google.
- Microsoft.
- OpenRouter.
- Mistral.
- NVIDIA.
- AMD.
- Hugging Face.
- Northflank.
- EDB / AI Factory.
- Solutions air-gapped et sovereign AI.

### Lecture stratégique
Votre différenciation peut venir de :
- la souveraineté,
- l’orchestration multi-modèle,
- la mémoire métier,
- la gouvernance,
- le déploiement local,
- l’observabilité,
- et le contrôle coût/énergie.

## 10) Idées de fonctions produit

- Sélecteur de modèle automatique selon sensibilité des données.
- Agent supervisor pour valider les actions à risque.
- Mode local-only.
- Mode hybrid-cloud.
- Journal d’audit exportable.
- Evaluation runner.
- Knowledge base entreprise.
- Connecteurs API internes.
- Détection de dérive comportementale.
- Quotas par équipe.
- Policy engine compatible JSON/YAML.
- Gestion multi-tenant.

## 11) Ressources à conserver

### Vidéos
- [Nvidia Blackwell / B200 overview](https://www.youtube.com/watch?v=urR5aBVs_NU) [web:27].

### Articles
- [Datacenter Knowledge on AI chip and memory bottlenecks](https://www.datacenterknowledge.com/infrastructure/after-the-power-crunch-ai-infrastructure-hits-a-gpu-wall) [web:2].
- [CNBC memory shortage article](https://www.cnbc.com/2026/01/26/memory-chip-shortage-to-last-through-2027-semiconductor-boss-says.html) [web:5].
- [Nature on data center energy](https://www.nature.com/articles/d41586-025-01113-z) [web:29].

### GitHub / code
- [OpenRouter examples](https://github.com/OpenRouterTeam/openrouter-examples) [web:11].
- [llm-server-docs](https://github.com/varunvasudeva1/llm-server-docs) [web:12].
- [AI Agent Governance Toolkit](https://github.com/socragpt/AI-Agent-Governance-Toolkit) [web:16].
- [awesome multi-agent orchestrators](https://github.com/Agent-Analytics/awesome-multi-agent-orchestrators) [web:19].

### Produits et stacks
- [EDB AI Factory](https://www.enterprisedb.com/docs/edb-postgres-ai/latest/hybrid-manager/ai-factory/architecture/) [web:1].
- [ibl.ai air-gapped AI](https://ibl.ai/service/air-gapped-ai/corporate) [web:10].
- [OpenRouter API](https://openrouter.ai/anthropic/claude-2.0/api) [web:14].

## 12) Plan de veille recommandé

1. Suivre hebdomadairement les sorties modèles et GPU.
2. Suivre les annonces RAM/HBM, prix mémoire et supply chain.
3. Maintenir une liste de benchmarks internes.
4. Cartographier les concurrents par couche de stack.
5. Identifier les modèles open-weight adaptés au local.
6. Tester chaque nouveauté sur un corpus métier.
7. Mesurer qualité, coût, latence, énergie et conformité.