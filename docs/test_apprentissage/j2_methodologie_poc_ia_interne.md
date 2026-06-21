# Méthodologie POC IA — Neuraltech Consulting (édition 2026)

## Principes directeurs
Un POC IA Neuraltech suit 4 règles non négociables :
1. **Données réelles dès J1** : pas de POC sur données fictives. La qualité des données réelles détermine 70% du résultat.
2. **Critère de succès binaire défini en amont** : le POC réussit ou échoue selon une métrique précise, pas selon une impression. Exemple : concordance > 80% sur un dataset de test.
3. **Durée maximale 8 semaines** : au-delà, c'est un projet, pas un POC. Tout dépassement doit être explicitement validé par les deux parties.
4. **Output livrable** : le POC produit un artefact concret (notebook évalué, démo fonctionnelle, rapport de faisabilité) — pas seulement une présentation PowerPoint.

## Phases du POC

### Phase 0 — Qualification (1 semaine)
- Identification du cas d'usage et de la donnée disponible
- Définition du critère de succès binaire avec le client
- Revue conformité données : RGPD, données sensibles, IA Act
- Audit SI préliminaire : contraintes d'intégration avec les systèmes existants
- Go/No-Go Neuraltech (décision formalisée par écrit)

### Phase 1 — Build (3-4 semaines)
- Sélection du modèle de base (benchmark rapide sur 2-3 modèles sur données réelles)
- Implémentation de l'architecture : RAG, fine-tuning ou prompt engineering selon le cas
- Pipeline de données et prétraitement
- Tests unitaires sur sous-ensemble des données

### Phase 2 — Évaluation (1-2 semaines)
- Évaluation sur dataset de test indépendant (jamais utilisé pendant le build)
- Mesure de la performance vs critère de succès
- Identification des cas limites et des catégories d'échec
- Analyse des erreurs : comprendre pourquoi le modèle échoue

### Phase 3 — Décision (1 semaine)
- Rapport de faisabilité : Go production / No-Go documenté / Pivot avec nouvelle approche proposée
- Business case si Go : estimation coûts (infra, modèle, maintenance) et ROI sur 12 mois
- Roadmap indicative vers la production (grandes étapes, ressources estimées)

## Anti-patterns à éviter
- **Changer le critère de succès en cours de route** : signe que le cas d'usage n'était pas assez qualifié.
- **Sélectionner le modèle avant d'avoir qualifié les données** : le modèle doit être choisi après avoir vu les données réelles.
- **Livrer une démo qui ne fonctionnerait pas sur les données client réelles** : le POC doit être honnête sur ce qui fonctionne.
- **Omettre l'audit SI en Phase 0** : l'intégration avec les systèmes existants est souvent le vrai verrou, pas le modèle.

## Ressources types mobilisées
| Phase | Profil | Jours estimés |
|---|---|---|
| Phase 0 | Senior IA + Manager | 3-5 jours |
| Phase 1 | Confirmé IA (×2) | 15-20 jours |
| Phase 2 | Confirmé IA + Senior | 8-10 jours |
| Phase 3 | Senior IA + Manager | 3-4 jours |
