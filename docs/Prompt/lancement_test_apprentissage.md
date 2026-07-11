# Protocole — Lancement Test Apprentissage Big Bertha

> Ce document est le point d'entrée standard pour tout test apprentissage.
> À chaque lancement, Claude Code suit ce protocole dans l'ordre.

---

## Ce que ce test valide

- **RAG retrieval** sur corpus hétérogène (md / txt / pdf / docx) — les documents importés sont retrouvés et cités dans les réponses.
- **Routing Boss/Agents** sur des demandes employés réelles — ANALYSTE et RÉDACTEUR reçoivent les bons messages, BOSS ne répond en direct qu'en cas d'ambiguïté légitime.
- **Apprentissage SENTINEL** sur la durée — le score progresse jour après jour, les proposals générées sont cohérentes avec le contexte métier de l'entreprise testée.

---

## Prérequis

- Big Bertha lancé via `start.bat` sur la machine cible
- Clé OpenRouter configurée dans les Settings
- Dossier `Samples/{entreprise}/` présent dans le projet

---

## Étape 1 — Collecte des paramètres

Claude Code pose ces 4 questions dans l'ordre, une à la fois :

**1. Quelle entreprise tester ?**
Afficher la liste des dossiers présents dans `Samples/` (voir tableau en fin de document).

**2. Quel mode ?**

| Mode | Jours | Durée approx. |
|---|---|---|
| `court` | 7 j | ~30 min |
| `moyen` | 14 j | ~1h |
| `long` | 30 j | ~2-3h |

**3. `--day-duration` ?**
Valeur recommandée : `0` — les proposals SENTINEL s'appliquent immédiatement entre les jours, le temps d'attente n'apporte rien à la mécanique d'apprentissage.
Autre valeur possible si on veut tester la stabilité dans le temps (ex : `300` pour 5 min entre chaque jour).

**4. Modèle ?**
- `COST` — Mistral-Nemo (défaut, rapide, économique)
- `PERFORMANCE` — selon config `routing_model_perf` dans les Settings

**5. Moteur LLM ?**
- `openrouter` — appels via OpenRouter (défaut en production)
- `ollama` — appels via Ollama local (v2-machine uniquement)

Si la réponse diffère de la valeur actuelle en DB :
- **DB fraîche** (après suppression de `bigbertha.db`) : rien à faire — le serveur lit `INFERENCE_MODE` dans `.env` au démarrage.
- **DB existante** avec une mauvaise valeur : exécuter **après** avoir démarré le serveur, **avant** le test (compatible PowerShell) :
```
python -c "import sqlite3; c=sqlite3.connect('backend/data/bigbertha.db'); c.execute('UPDATE app_config SET value=? WHERE key=?',('openrouter','inference_mode')); c.commit(); print('inference_mode OK')"
```
*(remplacer `openrouter` par `ollama` si besoin)*

---

## Étape 2 — Génération du plan

Commande à exécuter depuis la racine du projet :

```
python tests/plan_simulation.py --company "{entreprise}" --mode {mode}
```

Claude Code affiche le plan complet jour par jour et attend la validation avant de continuer.

Si un ajustement est demandé : relancer `plan_simulation.py` avec les mêmes paramètres — le manifest est écrasé par le nouveau.

---

## Étape 3 — Validation du plan

Points à vérifier dans le plan affiché :

- Les thèmes progressent logiquement (base → terrain → expertise)
- Les messages sonnent comme un employé, pas un consultant
- Aucun doc halluciné dans la liste (`WARNING` = fichier ignoré automatiquement)
- Le nombre de jours correspond au mode choisi

---

## Étape 4 — Lancement sur la machine cible

Big Bertha doit être lancé (`start.bat`) sur la machine avant cette commande.

Le `{timestamp}` est affiché à la fin de l'étape 2, dans la ligne :
`✓ Manifest écrit : docs/Test/runs/{entreprise}_{timestamp}/manifest.json`

Commande à exécuter sur la machine externe :

```
python tests/simulate_all.py --run-dir docs/Test/runs/{entreprise}_{timestamp}/
```

---

## Étape 5 — Récupération des résultats

Après la simulation, un log JSON est produit dans `docs/Test/logs/`.

Commandes git pour rapatrier sur la machine de travail :

```
git add docs/Test/logs/{entreprise}_{timestamp}_log.json
git commit -m "test({entreprise}): résultats simulation {mode} {date}"
```

Analyser ensuite avec Claude Code : ouvrir le `_log.json` et demander un bilan (évolution score SENTINEL, `routing_fallback_count`, `kb_citation_rate`, proposals approuvées).

---

## Entreprises disponibles

| Dossier `Samples/` | Secteur | Fichiers disponibles |
|---|---|---|
| `AgroPulse-Coop` | Agriculture coopérative | md×3, txt×1, pdf×1, docx×1 |
| `Atelier-Mecaflux` | Mécanique industrielle | md×3, txt×1, pdf×1, docx×1 |
| `BlueCart-Retail` | E-commerce omnicanal | md×3, txt×1, pdf×1, docx×1 |
| `Finovia-InsureTech` | Assurance / InsurTech | md×3, txt×1, pdf×1, docx×1 |
| `HelioMove-Logistics` | Logistique | md×3, txt×1, pdf×1, docx×1 |
| `Novalys-Sante` | Santé | md×3, txt×1, pdf×1, docx×1 |
| `PixelForge-Games` | Jeux vidéo / Studio | md×3, txt×1, pdf×1, docx×1 |
| `UrbanNest-RealEstate` | Immobilier | md×3, txt×1, pdf×1, docx×1 |
| `VerdantGrid-Energy` | Énergie / Transition | md×3, txt×1, pdf×1, docx×1 |
| `Neuraltech Consulting` | Conseil IA | pdf×2, doc×2, md×1, txt×1 |

> Vérifier `Samples/` pour la liste à jour si de nouveaux dossiers ont été ajoutés.
