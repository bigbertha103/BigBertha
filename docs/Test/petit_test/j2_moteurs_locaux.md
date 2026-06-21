# Moteurs d'inférence locaux pour LLM

## Outils de référence

### llama.cpp
Moteur de référence pour l'exécution locale de LLMs. Points forts :
- Support de nombreux formats de modèles (GGUF)
- Quantization intégrée (Q4, Q5, Q8) pour réduire l'empreinte mémoire
- Peut fonctionner sur CPU seul (pas de GPU obligatoire)
- Idéal pour les machines modestes ou les déploiements edge
- Interface HTTP compatible avec le format OpenAI

### vLLM
Moteur haute performance pour le serving d'inférence en production :
- PagedAttention : gestion efficace de la mémoire KV cache
- Throughput très élevé (batching continu)
- Nécessite GPU NVIDIA avec CUDA
- Utilisé par les déploiements de type datacenter
- Support multi-GPU et multi-nœuds

### Ollama
Distribution simple pour exécuter des modèles localement :
- Installation en une commande, interface intuitive
- Bibliothèque de modèles pré-configurés (Llama 3, Mistral, Gemma, Phi, etc.)
- API compatible format OpenAI (`/v1/chat/completions`)
- Gestion automatique des modèles (téléchargement, stockage)
- Idéal pour le développement et les tests locaux
- Moins performant que vLLM pour des charges de production élevées

### TGI (Text Generation Inference)
Serving production orienté Hugging Face :
- Optimisé pour les modèles Hugging Face
- Support Flash Attention 2
- Streaming natif
- Quantization (GPTQ, AWQ)
- Adapté aux déploiements cloud/on-premise avec Docker

## Stack locale recommandée selon le contexte

| Contexte | Stack recommandé |
|---|---|
| Développement rapide | Ollama + RAG + orchestrateur |
| Production GPU | vLLM ou TGI |
| Machine modeste / edge | llama.cpp |
| Air-gapped / souverain | Modèle open-weight + llama.cpp ou vLLM + gouvernance stricte |

## Exigences matérielles indicatives par taille de modèle

| Taille modèle | VRAM GPU minimum | Mode CPU (RAM) |
|---|---|---|
| 7B paramètres | ~8 GB | ~16 GB RAM |
| 13B paramètres | ~16 GB | ~32 GB RAM |
| 34B paramètres | ~40 GB | Très lent |
| 70B paramètres | ~48 GB (multi-GPU) | Impraticable |

La quantization (Q4_K_M par exemple) réduit ces besoins de 40-60% avec une perte de qualité limitée.

## Points d'attention pour le déploiement

- La latence CPU est 5-20x supérieure à la latence GPU
- Le batching est crucial pour optimiser l'utilisation GPU en production
- vLLM et Ollama peuvent être combinés (Ollama pour dev, vLLM pour prod)
- Prévoir un fallback sur modèle plus petit si le GPU est saturé
