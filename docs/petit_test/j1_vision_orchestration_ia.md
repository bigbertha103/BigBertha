# Vision produit — Plateforme d'orchestration d'agents IA souveraine

## Objectif produit

Construire une plateforme d'orchestration d'agents IA capable de fonctionner :
- via API cloud (OpenAI, Anthropic, OpenRouter, etc.)
- via modèles locaux exécutés sur GPU internes
- dans des environnements souverains, isolés ou air-gapped
- avec mémoire, apprentissage opérationnel et spécialisation métier pour entreprise

Ce positionnement est cohérent avec les architectures d'IA souveraine qui insistent sur le contrôle local du plan de contrôle, la résidence des données et l'exécution des inférences dans le périmètre client.

## Architecture et souveraineté

### Références clés
- **AI Factory Architecture on Hybrid Manager** — architecture containerisée orientée souveraineté et exécution sur clusters Kubernetes contrôlés par le client
- **The Enterprise Local AI Stack** — découpe en 7 couches pour penser un stack local entreprise
- **Sovereign AI Infrastructure Guide** — insiste sur contrôle local, résidence des données et absence de dépendance à un control plane externe
- **Air-Gapped AI for Corporate L&D** — exemple d'offre enterprise "no external API calls" avec exécution locale sur serveurs GPU

### Points d'architecture à intégrer
- Routage multi-fournisseurs selon coût, latence, confidentialité et criticité
- Sélection automatique du modèle selon tâche
- Mémoire entreprise avec cloisonnement par tenant, équipe et projet
- Journal d'audit complet des prompts, outils, versions de modèles et décisions
- Gouvernance avant exécution : politiques, budgets, approbations, sandbox, révocation

## Pourquoi la souveraineté est un avantage concurrentiel

Les entreprises dans les secteurs juridique, médical, financier et défense ne peuvent pas envoyer leurs données à des API tierces. L'exécution locale avec modèles open-weight répond à :
- La conformité RGPD et réglementations sectorielles
- L'absence de dépendance à un fournisseur cloud unique
- Le contrôle total des données et des logs d'inférence
- La possibilité de fonctionner en réseau isolé (air-gapped)

## Différenciation produit possible

- Déploiement hybride : cloud pour les tâches peu sensibles, local pour les données critiques
- Routing intelligent selon la classification des données
- Mémoire persistante par entreprise, non partagée entre tenants
- Audit trail exportable conforme aux obligations réglementaires
