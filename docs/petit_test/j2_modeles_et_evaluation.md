# Modèles IA en 2026 — panorama et critères d'évaluation

## Familles de modèles à tester

### Modèles cloud (API)
- **OpenAI (GPT-4o, o3)** — raisonnement général, tool use, vision multimodale
- **Anthropic (Claude 3.5/4.x)** — rédaction, agents, code, tâches longues avec grand contexte
- **Google (Gemini 2.x)** — raisonnement multimodal, contexte très long (1M tokens)
- **Mistral (Mistral Large, Pixtral)** — alternative européenne souveraine, bonne performance/coût
- **OpenRouter** — accès unifié à tous les modèles via une seule API

### Modèles open-weight (local)
- **Llama 3.1/3.2** (Meta) — référence open-weight, performances compétitives
- **Mistral 7B/Mixtral** — excellent rapport qualité/taille, MoE efficace
- **Qwen 2.5** (Alibaba) — fort en code et mathématiques, multilingue
- **DeepSeek V3/R1** — très performant en raisonnement, architecture innovante
- **Phi-3/4** (Microsoft) — petits modèles avec performances surprenantes
- **Gemma 2** (Google) — compact, optimisé pour edge et mobile

## Critères d'évaluation

### Qualité
- Qualité de raisonnement (benchmarks MMLU, GPQA, HumanEval)
- Qualité du code (HumanEval, SWEBench)
- Robustesse sur tâches longues (suivre des instructions complexes sur 10+ tours)
- Taux d'hallucination mesuré sur corpus métier interne

### Performance
- Latence (tokens par seconde en génération)
- Throughput (requêtes simultanées gérables)
- Coût par tâche (tokens input + output × prix)
- Empreinte mémoire (VRAM ou RAM nécessaire)

### Opérationnel
- Facilité de quantization et de serving local
- Disponibilité via API (uptime, limites de débit)
- Taille du contexte (context window)
- Support des outils (function calling, structured output)
- Licence (commerciale, open, restrictions d'usage)

## Stratégie de routing dynamique

L'objectif n'est pas de choisir un seul modèle mais de router intelligemment :

1. **Classification de la requête** : simple FAQ → petit modèle local, analyse complexe → modèle premium
2. **Sensibilité des données** : données internes → modèle local, données publiques → API cloud
3. **Contrainte budget** : quota dépassé → fallback modèle moins cher
4. **Contrainte latence** : temps réel → modèle rapide local, batch → modèle de qualité

## Modèles recommandés par cas d'usage (2026)

| Usage | Modèle recommandé | Raison |
|---|---|---|
| Raisonnement complexe | Claude 4 Opus / GPT-4o | Qualité maximale |
| Génération de code | DeepSeek R1 / Claude Sonnet | Performance/coût |
| FAQ rapide | Phi-4 / Gemma 2 9B (local) | Latence + coût zéro |
| Multilingue | Qwen 2.5 / Mistral | Support langues |
| Air-gapped | Llama 3.1 70B quantized | Open-weight + local |
