# Pénurie mémoire, énergie et contraintes infrastructure IA 2026

## La pénurie mémoire — état des lieux (Davos 2026)

Sources : CNBC (Davos 2026), NPR All Things Considered (décembre 2025)

### Le constat
L'explosion de l'IA en datacenter a provoqué une pénurie mondiale de puces mémoire RAM :
- La demande de RAM dépasse l'offre de **+10%** et continue de croître (TrendForce)
- Les fabricants paient **50% de plus** qu'au trimestre précédent pour les DRAM les plus courantes
- Les prix DRAM devraient augmenter encore **+40%** au prochain trimestre (Avril Wu, TrendForce)
- La pénurie devrait durer **jusqu'à 2027** selon le CEO de Synopsys (Sassine Ghazi)

### Pourquoi l'IA gobble la mémoire
*"AI workloads are built around memory"* — Sanchit Vir Gogia, CEO Greyhound Research

Les datacenters IA nécessitent massivement de la **HBM (High Bandwidth Memory)** pour les GPU. Cette mémoire à haute bande passante est critique pour :
- L'entraînement de grands modèles (larges batches, poids des modèles)
- L'inférence rapide (KV cache, attention layers)
- La persistance du contexte sur des milliers de tokens

*"AI has changed the nature of demand itself. Training and inference systems require large, persistent memory footprints, extreme bandwidth, and tight proximity to compute."*

### Impact sur les autres marchés
Les fabricants (Samsung, SK Hynix, Micron) réorientent leur production vers la HBM pour l'IA :
- **Moins de DRAM standard** pour les PC, smartphones, consoles de jeux
- **Hausse des prix** des appareils grand public en 2026-2027
- Micron Idaho — nouvelle usine opérationnelle en 2027 seulement
- Le CEO de Lenovo : *"I don't see how this will certainly not make its way into the customer base"*

## Contraintes énergétiques des datacenters IA

### Le mur énergétique
Après la pénurie de GPU et de mémoire, les datacenters IA se heurtent à un nouveau mur : l'énergie électrique.

Données clés :
- Projections IDC : croissance forte de la consommation énergétique des datacenters
- **40% des datacenters IA** pourraient être contraints par les pénuries d'énergie d'ici 2027 (Gartner)
- La question énergétique devient structurelle selon Nature/IEA

### Contraintes spécifiques
- Construction de nouveaux datacenters limitée par la disponibilité du réseau électrique
- La fabrication HBM est elle-même très énergivore (TSMC, packaging avancé)
- Tension entre les géants tech (hyperscalers) et la demande locale d'énergie

## Opportunités produit liées à ces contraintes

### Optimisation énergétique
- Intégrer le **coût énergétique par requête** dans les métriques de routing
- **Mode "eco"** : préférer les petits modèles locaux sur les tâches simples
- Routing vers modèles efficaces en énergie (Phi-4, Gemma 2) pour les requêtes courantes
- Caching sémantique agressif pour éviter les inférences redondantes

### Optimisation mémoire
- Profils de modèles adaptés à la VRAM disponible (auto-détection)
- Quantization dynamique selon les ressources disponibles
- Gestion intelligente du KV cache (libération après session inactive)
- Préférer les modèles avec architecture MoE (moins de mémoire active par requête)

### Indépendance infrastructure
- Ne pas dépendre d'un seul type de GPU (NVIDIA vs AMD)
- Prévoir fallback CPU pour les modèles quantizés
- Support multi-nœuds pour distribuer la charge mémoire
- Monitoring des ressources et alertes avant saturation
