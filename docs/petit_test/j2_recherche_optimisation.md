# Axes de recherche et optimisation pour systèmes LLM

## Axes de recherche pertinents

### Architectures et efficacité
- **MoE (Mixture of Experts)** — routage d'experts : activer seulement 1/8e des paramètres par token, réduire le coût d'inférence de 4-8x à qualité comparable (Mixtral, DeepSeek MoE)
- **Distillation** — comprimer un modèle lourd (70B) vers un modèle spécialisé plus petit (7-13B) sur un domaine métier spécifique
- **Quantization agressive** — Q4_K_M réduit la VRAM de 60% avec <5% de dégradation sur la plupart des tâches
- **Speculative decoding** — utiliser un petit modèle pour prédire les tokens, vérifier avec le grand modèle, gain de vitesse 2-3x

### Mémoire et contexte
- **Cache KV et réutilisation de contexte** — éviter de recalculer les embeddings du prompt système à chaque requête (prompt caching Anthropic, prefix caching OpenAI)
- **RAG plutôt que fine-tuning** — pour les connaissances dynamiques ou volumineuses, le RAG est plus flexible et moins coûteux que le fine-tuning
- **Tool use + memory + retrieval** — améliorer la pertinence sans augmenter la taille du modèle
- **Séparation mémoire à 3 niveaux** : court terme (session), moyen terme (projet), long terme (entreprise)

### Qualité et fiabilité
- **Monitoring automatique des taux d'hallucination** — détecter les affirmations non vérifiables par comparaison avec la base de connaissance
- **Monitoring des coûts par tâche** — alertes si une tâche dépasse un seuil de coût
- **Eval harness interne** — jeu de questions de référence avec réponses attendues, lancé après chaque changement de modèle ou de prompt

## Pistes d'implémentation

### Benchmarks et régression
- Construire des benchmarks internes par métier (ex : 50 questions de qualification RH avec réponses de référence)
- Exécuter la régression après chaque changement de modèle, prompt ou base de connaissance
- Comparer les scores entre versions pour détecter les régressions

### Apprentissage contrôlé
- Feedback humain explicite (like/dislike, annotation des erreurs)
- Signaux d'usage implicites (taux d'épinglage, reformulations de l'utilisateur)
- Versioning complet des prompts, outils et politiques — jamais de changement sans traçabilité

### Caching sémantique
- Répondre depuis le cache si la question est sémantiquement similaire à une question récente
- Réduction de coût potentielle de 40-70% sur les charges FAQ répétitives
- Seuil de similarité cosinus configurable selon le niveau d'exactitude requis

## Optimisation coût-énergie

- Préférer les petits modèles sur les tâches simples (classification, FAQ)
- Mode "eco" : fallback automatique vers modèle local pour les requêtes non urgentes
- Prédire la charge et lisser les pics (batching, queue)
- Mesurer et rapporter le coût énergétique par requête (pour les datacenters)
- Caching agressif pour réduire les appels répétitifs inutiles
