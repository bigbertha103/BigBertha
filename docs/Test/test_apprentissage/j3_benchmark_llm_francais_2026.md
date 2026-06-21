# Benchmark LLM open-weight pour le français — H1 2026

## Périmètre de l'évaluation
**Modèles évalués** : Mistral Nemo 12B, Mistral Small 22B, Llama 3.3 70B, Qwen 2.5 32B, Gemma 3 27B.
**Contexte d'évaluation** : cas d'usage professionnels en français (synthèse documentaire, classification, rédaction de livrables).
**Infrastructure** : GPU A100 80GB (serveur de test Neuraltech).

## Résultats synthèse

| Modèle | Qualité français | Suivi instructions | Latence (tok/s) | Licence commerciale |
|---|---|---|---|---|
| Mistral Nemo 12B | ★★★☆☆ | ★★★☆☆ | 85 tok/s | Oui (Apache 2.0) |
| Mistral Small 22B | ★★★★☆ | ★★★★☆ | 45 tok/s | Oui (Apache 2.0) |
| Llama 3.3 70B | ★★★★★ | ★★★★★ | 18 tok/s | Oui (Llama 3.3 Community) |
| Qwen 2.5 32B | ★★★★☆ | ★★★★☆ | 32 tok/s | Oui (Apache 2.0) |
| Gemma 3 27B | ★★★★☆ | ★★★☆☆ | 40 tok/s | Oui (Gemma Terms of Use) |

## Recommandations par cas d'usage

### RAG sur documents professionnels français (retail, banque)
**Recommandé : Qwen 2.5 32B** — meilleur compromis qualité/latence pour du RAG en français. Nativement multilingue (atout pour les contextes retail avec fournisseurs étrangers). Licence Apache 2.0 sans restriction commerciale.

**Alternative haute qualité** : Llama 3.3 70B si infrastructure disponible (nécessite 2×A100 80GB en fp16 ou quantization 4-bit sur 1×A100). Performances supérieures mais coût d'inférence 2× plus élevé.

**Budget limité / petit déploiement** : Mistral Small 22B — bon rapport qualité/ressources, bien documenté.

### Classification documentaire (banque, assurance)
**Recommandé : Mistral Small 22B** — bon suivi d'instructions structurées, faible consommation GPU, adapté aux tâches répétitives à haute fréquence.

### Agent conversationnel multilingue (retail avec fournisseurs étrangers)
**Recommandé : Qwen 2.5 32B** — nativement multilingue FR/EN/ZH/ES, cohérence élevée sur les réponses mixes de langues.

## Points d'attention par modèle

**Mistral Nemo 12B** : performances acceptables pour des tâches simples. Tendance à l'hallucination sur des questions factuelles précises. À éviter pour les cas à haut risque (conformité IA Act, crédit, médical).

**Llama 3.3 70B** : excellent sur toutes les dimensions mais infrastructure GPU conséquente. Le TCO (Total Cost of Ownership) doit être pris en compte — sur A100 en location : environ 3,50€/heure vs 0,70€ pour le 22B.

**Gemma 3 27B** : qualité française correcte mais moins bonne cohérence sur les instructions complexes à plusieurs critères. Intéressant pour des cas d'usage simples avec budget GPU limité.

## Limite de ce benchmark
Ces évaluations sont valides H1 2026. Le marché LLM évolue très rapidement — de nouveaux modèles (Mistral Large 3, Llama 4, Qwen 3) sont en cours de déploiement. Ce benchmark doit être réactualisé avant toute décision d'architecture.
