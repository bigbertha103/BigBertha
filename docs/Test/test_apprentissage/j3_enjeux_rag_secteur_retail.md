# Enjeux du déploiement RAG dans le secteur retail

## Spécificités du contexte retail
Le secteur retail présente des caractéristiques distinctives pour les projets RAG :
- **Volume de données élevé** : catalogues produits (100k à 1M+ références), historiques commandes, fiches fournisseurs, guides de merchandising.
- **Hétérogénéité des formats** : Excel, PDF, CSV, images produits, emails fournisseurs, données ERP.
- **Fraîcheur critique** : les prix, promotions et stocks changent quotidiennement — un RAG avec données périmées peut générer des erreurs coûteuses (prix incorrect communiqué, rupture non détectée).

## Cas d'usage RAG retail les plus mûrs (validés en production)

### Assistant merchandising
Réponses aux questions des chefs de rayon sur les règles d'implantation, les promotions en cours, les historiques de vente par référence. ROI mesuré sur 3 déploiements : gain de 25 à 40% du temps de recherche d'information.

### Support acheteurs
Synthèse des conditions fournisseurs, historique des négociations, alertes sur les délais de livraison et les pénalités contractuelles. Particulièrement utile lors des renégociations annuelles.

### Formation et onboarding
Accès aux procédures internes, guides produits, règles de conformité alimentaire ou cosmétique. Réduit le temps d'onboarding de nouveaux collaborateurs de 30 à 50% selon les retours clients.

## Défis spécifiques retail

### Mise à jour des embeddings (défi principal)
Avec des données qui changent tous les jours (prix, promotions, stocks), la stratégie d'indexation incrémentale est critique. Une ré-indexation complète quotidienne est techniquement possible mais coûteuse. Solution recommandée : indexation incrémentale sur les deltas + TTL (time-to-live) sur les données à forte péremption.

### Multi-langue fournisseurs
Les fiches produits peuvent être en français, anglais, espagnol ou mandarin selon l'origine. Les modèles multilingues (Qwen 2.5) gèrent mieux ce cas que les modèles franco-centristés.

### Données structurées vs non-structurées
Les catalogues produits sont structurés (tables Excel/SQL) — le RAG classique sur texte ne suffit pas. Il faut combiner RAG textuel avec accès SQL ou Knowledge Graph pour les données quantitatives (prix, stocks, codes EAN).

## Volumes typiques rencontrés sur les missions Neuraltech

| Type de données | Volume moyen ETI retail (500-2000 collaborateurs) |
|---|---|
| Références produits (fiches) | 50k à 500k |
| Documents procédures internes | 200 à 2000 |
| Emails fournisseurs archivés | 10k à 100k |
| Données de vente (CSV/ERP) | 10M à 500M lignes |

## Recommandations pour un déploiement réussi
1. Prioriser 2-3 cas d'usage à fort ROI mesurable plutôt que de vouloir tout indexer dès le départ.
2. Définir une stratégie de fraîcheur des données dès la phase de qualification (Phase 0 POC).
3. Ne pas négliger la gouvernance des données : qui peut voir quoi dans le RAG ? Les conditions fournisseurs sont souvent confidentielles.
4. Commencer par les données non-structurées (procédures, guides) avant de s'attaquer aux données structurées (prix, stocks).
