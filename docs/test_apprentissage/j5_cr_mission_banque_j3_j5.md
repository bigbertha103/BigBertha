# Compte-rendu de mission — Banque Lumière (Semaines 3 à 5)

**Projet** : POC agents IA — Analyse risque crédit  
**Client** : Banque Lumière  
**Période couverte** : Semaines 3 à 5 du projet (3 juin au 20 juin 2026)  
**Interlocuteurs client** : Directrice des Risques (DR), DSI adjoint, 2 analystes pilotes  
**Consultant Neuraltech référent** : Consultant Senior IA

---

## Semaine 3 — Premier benchmark et détection du problème principal

### Avancées
- Pipeline RAG opérationnel sur les 150 dossiers historiques anonymisés
- Stratégie de chunking validée : 1 dossier = 1 espace d'indexation isolé (pas de mélange inter-dossiers)
- Premier benchmark interne réalisé sur les 30 dossiers de test

### Résultats benchmark semaine 3
Concordance globale : **71%** — sous le critère de succès de 80%

Analyse des erreurs :
- Les dossiers contenant des bilans comptables en PDF scanné obtiennent une concordance de seulement 58% (vs 79% pour les PDF natifs)
- Cause identifiée : Tesseract standard échoue sur les tableaux comptables multi-colonnes en police condensée — les chiffres clés (ratios) sont souvent mal extraits ou absents

### Décision prise
Intégration d'une étape OCR renforcée (Tesseract v5 + prétraitement image : redressement, amélioration contraste) avant l'indexation des PDF scannés. Délai additionnel estimé : 5 jours ouvrés.

---

## Semaine 4 — Intégration OCR et amélioration de la concordance

### Avancées
- OCR renforcé intégré et validé sur les 150 dossiers (traitement complet en 4h)
- Re-indexation complète du corpus avec les données OCR améliorées
- Nouveau benchmark : concordance **79%** — à 1 point du critère

### Tests en conditions réelles (hors benchmark)
Les 2 analystes pilotes ont testé l'outil sur 5 nouveaux dossiers non inclus dans le benchmark. Retours :
- Qualité des synthèses : 8,0/10 en moyenne (analystes DR)
- "L'outil identifie bien les ratios clés, la mise en forme est claire" — Analyste pilote 1
- "Sur 1 dossier sur 5, les provisions pour risques étaient mal interprétées car mal formattées dans le bilan" — Analyste pilote 2

### Actions semaine 4
Ajustement du prompt d'extraction : ajout d'une section dédiée aux provisions et aux engagements hors-bilan dans le template de fiche risque.

---

## Semaine 5 — Benchmark final et rapport de faisabilité

### Benchmark final
Concordance : **83%** — Critère de succès de 80% atteint ✅

Détail par catégorie de dossier :
- PDF natifs : 89% de concordance
- PDF scannés (bilans simples) : 81%
- PDF scannés (bilans complexes multi-entités) : 74% (cas limite identifié)

### Rapport de faisabilité
Document rédigé et transmis au client le 20 juin 2026. Recommandation : **Go production** avec les conditions suivantes.

---

## Points de vigilance actifs

### Point 1 — PDF avec tableaux HTML embarqués
Les rapports sectoriels récents (post-2025) contiennent parfois des tableaux générés en HTML dans le PDF (via Word ou LibreOffice export). Ces tableaux ne sont pas couverts par le pipeline OCR actuel — le texte des tableaux est perdu. Impact estimé : 12% des dossiers concernés. Traitement recommandé en phase production.

### Point 2 — Fonctionnalité d'explicabilité (hors scope POC)
La Directrice des Risques souhaite que l'agent explique les 3 facteurs déterminants de la notation risque (pas seulement la synthèse). Fonctionnalité non dans le scope POC. Chiffrage en cours pour la proposition phase production.

---

## Prochaines étapes

| Action | Responsable | Date cible |
|---|---|---|
| Comité Go/No-Go client | DR + DSI adjoint + Neuraltech | 15 juillet 2026 |
| Proposition phase production (si Go) | Neuraltech | 22 juillet 2026 |
| Chiffrage fonctionnalité explicabilité | Neuraltech | 18 juillet 2026 |
| Revue conformité IA Act préliminaire | Neuraltech + DPO client | 25 juillet 2026 |
