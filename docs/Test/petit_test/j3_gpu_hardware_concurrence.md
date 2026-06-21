# GPU, hardware IA et paysage concurrentiel 2026

## Tendance matérielle

La course à l'IA pousse les fabricants à sortir des GPU plus rapides et plus gourmands en mémoire, avec une tension accrue sur HBM (High Bandwidth Memory) et DRAM.

## Acteurs GPU majeurs

### NVIDIA
- **H100** — GPU datacenter de référence, 80 GB HBM3, 3.35 TB/s bandwidth
- **H200** — successor H100, HBM3e, 141 GB, 4.8 TB/s — meilleur pour l'inférence LLM
- **B200 (Blackwell)** — architecture nouvelle génération, 192 GB HBM3e, ~20 PetaFLOPS FP4
- **GB200 NVL72** — configuration rack complète, 72 GPU interconnectés, pour les très grands modèles
- NVIDIA reste dominant mais dépendance à TSMC pour la fabrication

### AMD
- **MI300X** — 192 GB HBM3 unifié, compétitif sur inférence (meilleure densité mémoire que H100)
- **MI325X** — évolution MI300X, meilleure performance par watt
- **MI350** — annoncé avec forte progression sur l'inférence, attendu 2025-2026
- AMD gagne des parts de marché sur l'inférence grâce à sa densité mémoire supérieure

## Implications pour un produit d'orchestration IA

- **Ne pas dépendre d'un seul type de GPU** — le marché évolue vite (NVIDIA, AMD, Intel, cloud custom ASIC)
- **Profils de modèles selon VRAM disponible** — configurer automatiquement selon le GPU détecté
- **Fallback CPU** — prévoir un mode dégradé sans GPU (llama.cpp, quantization agressive)
- **Quantization et serving adaptatif** — Q4 sur GPU modeste, Q8 ou FP16 sur GPU haut de gamme
- **Métriques de coût énergétique par requête** — indispensable pour les datacenters

## Paysage concurrentiel des acteurs IA (à surveiller)

### Fournisseurs de modèles
- **OpenAI** — leader marché, GPT-4o, o1/o3, API dominante
- **Anthropic** — Claude 3.x/4.x, focus sur sécurité et fiabilité des agents
- **Google** — Gemini 2.x, intégration GCP, multimodal
- **Mistral** — alternative européenne souveraine, open-source partiel
- **Meta** — Llama open-weight, démocratise le déploiement local
- **Alibaba (Qwen)**, **DeepSeek** — challengers asiatiques très compétitifs

### Infrastructure et stack
- **NVIDIA** — GPU + CUDA + stack NIM pour serving
- **Hugging Face** — plateforme modèles, TGI, datasets
- **EDB / AI Factory** — Postgres + vector + orchestration hybride
- **OpenRouter** — agrégateur API multi-modèles
- **Northflank** — infrastructure déploiement IA

### Offres air-gapped / souverain
- **ibl.ai** — plateforme L&D enterprise sans appel API externe
- Solutions VDF, Rack2Cloud — stack IA locale complète

## Opportunités de différenciation

Votre différenciation peut venir de :
- La **souveraineté** (contrôle total des données, aucun cloud obligatoire)
- L'**orchestration multi-modèle** (routage intelligent selon coût/latence/sensibilité)
- La **mémoire métier** persistante et cloisonnée par tenant
- La **gouvernance** avant exécution (politiques, budgets, approbations)
- Le **déploiement local** sur hardware existant du client
- L'**observabilité** (audit trail, coûts par requête, métriques de qualité)
- Le **contrôle coût/énergie** (routing vers petit modèle sur tâches simples)
