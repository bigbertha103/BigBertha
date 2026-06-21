PROJET_CONTEXTE — BIG BERTHA
> Source de vérité absolue. Lire EN ENTIER avant toute action.
> Toute décision qui contredit ce fichier est interdite.
---
## 0. RÔLE DE CETTE CONVERSATION
Tu es le contrôleur permanent du projet Big Bertha. Ton rôle :
1. **Valider V1** : une fois le code livré, vérifier que chaque composant
   correspond exactement aux specs de ce document. Créer une checklist
   de validation. Identifier les écarts. Les corriger ou les documenter.
2. **Piloter V2** : une fois V1 validé, planifier et guider le passage
   à V2 selon le roadmap section 9. Même méthode que V1 : rédiger des
   prompts de sous-conversation, valider les retours, coder dans ce dossier.
3. **Garder ce fichier à jour** : après chaque changement validé,
   mettre à jour les sections concernées. Ce fichier est la seule source
   de vérité — pas la mémoire des conversations.

**Première action** : si ce fichier n'existe pas encore dans le projet,
le créer à la racine sous le nom PROJET_CONTEXTE.md avec ce contenu exact.
Puis créer la structure de dossiers section 4.

---
## 1. IDENTITÉ
| Champ | Valeur |
|---|---|
| Nom | BIG BERTHA |
| Type | Chatbot professionnel avec équipe d'agents IA |
| Objectif | Produit générique vendu à des entreprises. Chatbot + agents personnalisables. |
| Vision finale | Code + machine dédiée, tout local chez le client (modèle LLM hébergé, zéro cloud) |
| V1 | Même architecture locale, appels LLM via OpenRouter |
| Statut | V1 build complet — en cours de validation |
| Utilisateurs | Employés de l'entreprise cliente, réseau interne |
| Dernière mise à jour | 2026-06-20 |

---
## 2. STACK TECHNIQUE (figé)
| Élément | Valeur |
|---|---|
| Backend | FastAPI Python 3.11+ — port 8000 |
| Base de données | SQLite natif Python (sqlite3) — backend/data/bigbertha.db |
| Frontend | HTML5 + CSS3 + JavaScript vanilla (fetch natif, zéro framework) |
| Appels LLM | OpenRouter API via httpx (async) |
| Config | Table app_config dans bigbertha.db |
| Déploiement V1 | Local, réseau interne, host 0.0.0.0 |
| Auth | Aucune en V1 |
| Tenant | Mono-tenant (1 instance = 1 entreprise) |

---
## 3. ARCHITECTURE FONCTIONNELLE
### Le Boss — 2 phases internes séquentielles
Le Boss est l'orchestrateur central. Pas un agent visible, c'est le cerveau
du système. Pour chaque message utilisateur, il effectue 2 appels LLM :

**Phase 1 — ROUTING**
- Input : historique 10-15 derniers messages + éléments figés actifs
           + profil entreprise + liste agents actifs (chargée depuis DB)
- Output : JSON strict uniquement
```json
{
  "agent_code": "ANALYSTE",
  "task": "Texte complet et autonome de la tâche. L'agent n'a pas d'autre contexte.",
  "rationale": "Pourquoi cet agent en 1 phrase."
}
```
Valeurs agent_code valides : "ANALYSTE", "REDACTEUR", "BOSS"
BOSS = le Boss répond directement sans déléguer (salutation, question
méta, demande ambiguë nécessitant clarification)
Fallback si JSON malformé : Boss répond directement + log ERROR.

**Phase 2 — SYNTHESIS**
- Input : message original + profil entreprise + réponse brute de l'agent
  (ou vide si agent_code="BOSS")
- Output : JSON strict uniquement
```json
{
  "response": "Réponse finale en markdown, prête à afficher à l'utilisateur.",
  "pinned": ["Fait clé ou règle identifiée — formulation courte"]
}
```
pinned = liste vide [] si rien à épingler. Maximum 2 éléments par tour.
Un élément épinglé = information réinjectée dans les prochains appels
de cette conversation. Ne pas épingler des banalités.
Fallback si JSON malformé : retourner la réponse brute + log WARNING.

### Les 2 agents (stateless)
Les agents ne voient jamais l'historique de conversation.
Ils reçoivent une tâche isolée, retournent un résultat en markdown.
3 couches de contexte injectées à chaque appel :
- System prompt de l'agent (identité + règles — stocké en DB, seedé depuis agents_templates.json)
- Profil de l'entreprise (depuis company_profile)
- Tâche précise formulée par le Boss (le champ "task" du routing JSON)

Format d'appel agent :
```
PROFIL ENTREPRISE :
[contenu de company_profile injecté ici]

TÂCHE :
[contenu du champ task formulé par le Boss]
```
ANALYSTE — recherche, synthèse, analyse d'information
RÉDACTEUR — rédaction de documents professionnels

### Système de jobs
Chaque message utilisateur → 1 job asynchrone (BackgroundTasks FastAPI).
Frontend poll GET /api/jobs/{id} toutes les secondes.
Cycle de vie : PENDING → ROUTING → AGENT_RUNNING → SYNTHESIZING → DONE / ERROR

Un seul job actif par conversation à la fois. Si un job est déjà en statut
PENDING/ROUTING/AGENT_RUNNING/SYNTHESIZING, le backend rejette le nouveau
message avec HTTP 409.

Indicateurs de progression affichés dans l'UI (pendant le poll) :
- ROUTING → "Le Boss analyse votre demande..."
- AGENT_RUNNING → "[NOM_AGENT] au travail..."
- SYNTHESIZING → "Synthèse en cours..."
- ERROR → message d'erreur affiché dans le chat

### Éléments figés (pinned_context)
Scopés par conversation_id (ardoise vierge à chaque nouvelle conversation)
2 sources : Boss automatique (Phase 2) ou utilisateur manuellement
Réinjectés dans l'appel Boss Phase 1 de chaque nouveau message
Soft-delete uniquement (is_active=0), jamais de DELETE SQL

---
## 4. STRUCTURE DU PROJET
```
BigBertha/
├── PROJET_CONTEXTE.md          ← ce fichier — source de vérité
├── .env.example
├── .env                        (gitignored)
├── .gitignore
├── requirements.txt
├── start.sh                    ← Linux/Mac
├── start.bat                   ← Windows
├── docs/
│   ├── big_bertha_schema_db.md
│   ├── big_bertha_api_routes.md
│   ├── big_bertha_ui_wireframe.md
│   └── big_bertha_system_prompts.md
├── backend/
│   ├── __init__.py
│   ├── main.py                 ← FastAPI app, CORS, routes, appel init_db()
│   ├── database.py             ← get_connection(), init_db(), load_config(), seed_agents()
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── conversations.py    ← CRUD conversations + messages + blocage job actif
│   │   ├── jobs.py             ← GET statut job (polling)
│   │   ├── pinned.py           ← GET/POST/DELETE éléments épinglés
│   │   ├── agents.py           ← liste agents actifs
│   │   ├── company.py          ← GET/PUT profil entreprise
│   │   └── config.py           ← GET/PUT config app + GET logs
│   ├── services/
│   │   ├── __init__.py
│   │   ├── boss_service.py     ← Phase 1 routing + Phase 2 synthesis
│   │   ├── agent_analyste.py   ← run(job_id, task, db) → str
│   │   ├── agent_redacteur.py  ← run(job_id, task, db) → str
│   │   ├── job_runner.py       ← exécution async complète du job
│   │   ├── model_router.py     ← call_llm(), log_decision()
│   │   └── context_builder.py  ← prompts Boss hardcodés + construction des 3 couches
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── conversation.py
│   │   ├── agent.py
│   │   ├── pinned.py
│   │   └── job.py
│   └── data/
│       ├── bigbertha.db        (gitignored)
│       ├── agents_templates.json
│       └── bigbertha.log       (gitignored)
└── frontend/
    ├── index.html              ← redirect → chat.html
    ├── chat.html               ← page principale
    ├── settings.html           ← paramètres entreprise + config
    └── assets/
        ├── style.css
        └── js/
            ├── api.js          ← toutes routes API (BASE_URL centralisé)
            ├── shared.js       ← renderMarkdown, formatDate, getAgentLabel
            ├── chat.js         ← chat + polling job (1s) + pinned
            └── settings.js     ← formulaires profil + config

Fichiers V2 (à venir) :
├── docs/
│   └── rag_integration_spec.md    ← spec V2 RAG (figée)
├── backend/
│   ├── services/
│   │   ├── rag_engine.py          ← NOUVEAU — moteur RAG singleton (ChromaDB + fastembed)
│   │   └── sentinel_service.py    ← NOUVEAU — agent SENTINEL analyse + proposals
│   ├── routers/
│   │   └── knowledge.py           ← NOUVEAU — routes KB (upload, liste, delete)
│   └── data/
│       └── chroma_db/             ← NOUVEAU (gitignored, créé par ChromaDB au runtime)
└── tests/
    ├── __init__.py                ← NOUVEAU
    ├── test_rag_engine.py         ← NOUVEAU — tests unitaires moteur RAG
    ├── simulate_day.py            ← NOUVEAU — script simulation corpus 14 jours
    └── corpus/
        ├── manifest.json          ← NOUVEAU — plan de test
        └── (documents .md/.txt)
```

Conventions de nommage :
- Tables/colonnes SQLite : snake_case
- Fichiers Python : snake_case
- Classes Python : PascalCase
- Fonctions Python/JS : camelCase
- Routes API : /api/resource-name (kebab-case)
- Constantes : UPPER_SNAKE_CASE

---
## 5. SCHÉMA DE BASE DE DONNÉES (figé)
### Tables
```sql
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'boss')),
    content TEXT NOT NULL,
    job_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```
> Note : pas de colonne agent_code dans messages — décision D5 validée.
> L'agent_code est parsé depuis jobs.routing_output à la demande (GET /api/jobs/{id}).
> Badges agent non affichés dans l'UI (décision D5 wireframe).

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    user_message_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','ROUTING','AGENT_RUNNING','SYNTHESIZING','DONE','ERROR')),
    selected_agent_id INTEGER,
    routing_output TEXT,
    agent_input TEXT,
    agent_output TEXT,
    final_response TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (user_message_id) REFERENCES messages(id),
    FOREIGN KEY (selected_agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS pinned_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('boss','user')),
    job_id INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS company_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    sector TEXT,
    tone TEXT,
    business_rules TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS model_decision_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    conversation_id INTEGER NOT NULL,
    phase TEXT NOT NULL CHECK (phase IN ('ROUTING','AGENT_CALL','SYNTHESIS')),
    agent_id INTEGER,
    model_name TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Index
```sql
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_conversation
    ON jobs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status
    ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_user_message
    ON jobs(user_message_id);
CREATE INDEX IF NOT EXISTS idx_pinned_context_conversation
    ON pinned_context(conversation_id, is_active);
CREATE INDEX IF NOT EXISTS idx_model_decision_log_conversation
    ON model_decision_log(conversation_id);
CREATE INDEX IF NOT EXISTS idx_model_decision_log_job
    ON model_decision_log(job_id);
CREATE INDEX IF NOT EXISTS idx_model_decision_log_agent
    ON model_decision_log(agent_id);
```

### Seed data (init_db — INSERT OR IGNORE, idempotent)
```sql
-- Config par défaut (valeurs lues depuis .env au premier démarrage)
INSERT OR IGNORE INTO app_config (key, value) VALUES ('model_id', '...');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('openrouter_api_key', '');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('host', '0.0.0.0');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('port', '8000');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('boss_routing_prompt', '');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('boss_synthesis_prompt', '');
-- (boss_routing_prompt et boss_synthesis_prompt restent vides en DB —
--  les prompts Boss sont hardcodés dans context_builder.py, décision V1)

-- Agents (system_prompt chargé depuis backend/data/agents_templates.json)
```

### Notes de schéma
- `agent_code` absent de messages : parsé depuis `jobs.routing_output` quand nécessaire
- `company_profile CHECK (id=1)` : unicité garantie par le schéma, pas l'app
- `model_name TEXT` libre sans CHECK : le catalogue OpenRouter évolue
- `pinned_context is_active` : soft-delete, cohérent avec "on garde tout"

---
## 6. API ROUTES V1

### Conversations
| Méthode | Route | Description |
|---|---|---|
| POST | /api/conversations | Crée une conversation (title optionnel) |
| GET | /api/conversations | Liste toutes (id, title, updated_at) |
| PATCH | /api/conversations/{id} | Met à jour le titre |
| DELETE | /api/conversations/{id} | Supprime conversation + messages + jobs + pinned |
| GET | /api/conversations/{id}/messages | Historique complet |
| POST | /api/conversations/{id}/messages | Envoie message → crée job → retourne job_id (409 si job déjà actif) |

### Jobs
| Méthode | Route | Description |
|---|---|---|
| GET | /api/jobs/{id} | Statut + agent_code + réponse si DONE (pollé toutes les secondes) |

### Pinned context
| Méthode | Route | Description |
|---|---|---|
| GET | /api/conversations/{id}/pinned | Éléments actifs scopés à cette conversation |
| POST | /api/conversations/{id}/pinned | Épingle manuellement (source='user') |
| DELETE | /api/pinned/{id} | Désépingle (soft-delete : is_active=0, jamais de DELETE SQL) |

### Agents
| Méthode | Route | Description |
|---|---|---|
| GET | /api/agents | Liste agents actifs (id, code, name, description) |

### Company profile
| Méthode | Route | Description |
|---|---|---|
| GET | /api/company-profile | Retourne le profil (ou 404 si pas configuré) |
| PUT | /api/company-profile | Crée ou met à jour (INSERT OR REPLACE id=1) |

### Config
| Méthode | Route | Description |
|---|---|---|
| GET | /api/config | Retourne model_id, host, port (jamais la clé API en clair) |
| PUT | /api/config | Met à jour model_id et/ou openrouter_api_key |

### Logs
| Méthode | Route | Description |
|---|---|---|
| GET | /api/logs | Dernières 50 lignes du log (pour debug UI) |

---
## 7. SYSTEM PROMPTS (V1 — figés)
> Les prompts Boss sont hardcodés dans `backend/services/context_builder.py`.
> Les prompts agents sont dans `backend/data/agents_templates.json` et seedés en DB au démarrage.
> Les clés `boss_routing_prompt` et `boss_synthesis_prompt` dans `app_config` restent vides (non utilisées en V1).

### Boss Phase 1 — ROUTING
**Emplacement :** `context_builder.py` — constante `BOSS_ROUTING_PROMPT`

```
Tu es le Boss de Big Bertha, l'orchestrateur central d'une équipe d'agents IA spécialisés,
au service de l'entreprise cliente. Dans cette phase, ta seule mission est de décider qui
doit traiter le message de l'utilisateur — tu n'y réponds pas toi-même, sauf cas prévu
ci-dessous.

[Profil entreprise, agents disponibles et éléments figés injectés dynamiquement]

Règles de routing :
- ANALYSTE : chercher, comparer, synthétiser, analyser de l'information
- REDACTEUR : produire un document fini destiné à être lu ou envoyé tel quel
- BOSS : salutation, question méta, demande ambiguë, aucun agent ne correspond clairement
- Si demande mixte : choisir l'agent de la première étape logique
- Si hésitation réelle entre deux agents : choisir BOSS et formuler une question de clarification

Le champ task doit être complet et autonome — l'agent n'a pas d'autre contexte.

Format de sortie UNIQUEMENT :
{"agent_code": "ANALYSTE", "task": "...", "rationale": "..."}
```

### Boss Phase 2 — SYNTHESIS
**Emplacement :** `context_builder.py` — constante `BOSS_SYNTHESIS_PROMPT`

```
Tu es le Boss de Big Bertha. Ta mission : composer la réponse finale affichée à l'utilisateur,
à partir du résultat brut produit par un agent — ou répondre toi-même si Phase 1 a choisi BOSS.

Ne recopie jamais la réponse agent telle quelle : retravaille-la dans le ton du profil entreprise.
Ne mentionne jamais le processus interne (agents, routing, phases).

Si réponse agent vide ou en erreur : expliquer sobrement sans détail technique, proposer de reformuler.

Logique d'épinglage : épingler uniquement ce qui a une vraie valeur de rappel à moyen terme
(contrainte, décision, chiffre clé). Jamais de banalités. Maximum 2 par tour. [] si aucun.

Format de sortie UNIQUEMENT :
{"response": "...", "pinned": []}
```

### ANALYSTE
**Emplacement :** `agents_templates.json` + DB `agents.system_prompt WHERE code='ANALYSTE'`

Périmètre : recherche, synthèse, veille, analyse, benchmarks, comparatifs.
Règles : distinguer faits/estimations/hypothèses, ne jamais inventer de chiffres ni sources,
signaler les limites explicitement, réponse en markdown structuré (pas de JSON).

### RÉDACTEUR
**Emplacement :** `agents_templates.json` + DB `agents.system_prompt WHERE code='REDACTEUR'`

Périmètre : propositions, notes, CR, emails clients, rapports — documents finaux prêts à l'emploi.
Règles : respecter le ton entreprise, produire un texte fini sans placeholder sauf si information
manquante (signaler explicitement), ne jamais inventer de chiffres, réponse en markdown (pas de JSON).

---
## 8. PROFIL ENTREPRISE DE TEST
```
Nom         : Neuraltech Consulting
Secteur     : Conseil en intelligence artificielle et agents IA
Taille      : 12 consultants
Ton         : Professionnel, précis, orienté résultats. Pédagogue sans être condescendant.
Langue      : Français exclusivement, termes techniques anglais acceptés quand standard (RAG, LLM, fine-tuning...).
Règles métier :
  - Toujours contextualiser les recommandations IA par rapport au besoin métier client
  - Citer les limites et risques des solutions proposées
  - Distinguer ce qui est production-ready de ce qui est expérimental
  - Structurer les livrables : contexte → analyse → recommandations → prochaines étapes
  - Ne jamais promettre de performances LLM sans benchmark sur les données réelles du client
ANALYSTE  : veille technologique, benchmarks modèles, analyse d'articles et papers IA, comparatifs d'outils
RÉDACTEUR : propositions commerciales clients, technical briefs, notes de cadrage POC, comptes-rendus techniques
```

### Résultat de la session — 2026-06-21 (session 11)
- `chat.html` : bouton `#btn-archive-conv` ajouté dans la sidebar après `#btn-new-conv` (masqué par défaut)
- `chat.js` : référence DOM `btnArchiveConv`, affichage au chargement d'une conversation, masquage dans `showEmptyState()`, fonction `archiveCurrentConversation()` + écouteur de clic
- Validation : aucune erreur de syntaxe JS

### Résultat de la session — 2026-06-21 (session 10)
- `conversations.py` : endpoint `POST /api/conversations/{id}/archive` ajouté — 404 si introuvable, 409 si déjà archivée, UPDATE status → archived + updated_at
- Validation : `py_compile` OK

### Résultat de la session — 2026-06-21 (session 9)
- `context_builder.py` : pinned context limité à 5 éléments les plus récents dans `_build_elements_figes()` — corrige la dégradation du routing sur les longues conversations
- Validation : `py_compile` OK

### Résultat de la session — 2026-06-21 (session 8)
- `database.py` : fondation DB BLOC B — colonne `status` (active/archived) dans `conversations`, index `idx_conversations_status`, clés `handoff_token_threshold` et `handoff_message_fallback` seedées et chargées
- Migration live exécutée et confirmée (`Migration OK — colonne status ajoutée`)
- Aucune fonctionnalité changée — fondation prête pour le handoff

### Résultat de la session — 2026-06-21 (session 7)
- `config.py` : `CONFIG_WHITELIST` et `GET /api/config` étendus aux 11 clés de routing
- `settings.html` : section Configuration remplacée — toggle perf_mode + 5 champs modèles par tâche
- `settings.js` : `loadConfig()`, toggle listener, `btnSaveConfig` réécrits pour les 11 clés
- Validation : `py_compile` OK

### Résultat de la session — 2026-06-21 (session 6)
- `database.py` : `agent_model_cost` corrigé → `mistralai/mistral-nemo` (mistral-small retournait ~2 chars)
- DB mise à jour directement via UPDATE app_config
- En mode COST, tous les modèles actifs sont désormais `mistralai/mistral-nemo`

### Résultat de la session — 2026-06-21 (session 5)
- `sentinel_service.py`, `agent_analyste.py`, `agent_redacteur.py` branchés sur `model_router.get_model_for_task()` — routing de modèles complet sur tous les services
- Validation : `py_compile` OK sur les 3 fichiers

### Résultat de la session — 2026-06-21 (session 4)
- `database.py` : `synthesis_model_cost` corrigé → `mistralai/mistral-nemo` (mistral-small générait du JSON tronqué en synthesis)
- DB mise à jour directement via UPDATE app_config
- Validation : valeur confirmée en DB

### Résultat de la session — 2026-06-21 (session 3)
- `context_builder.py` : suppression du prefill `{"role":"assistant","content":"{"}` dans `build_synthesis_payload()` — corrige l'erreur 400 des providers Mistral sur OpenRouter
- Validation : `py_compile` OK

### Résultat de la session — 2026-06-21 (session 2)
- `boss_service.py` : `run_routing()` et `run_synthesis()` branchés sur `model_router.get_model_for_task()` — routing effectif par tâche selon `perf_mode`
- Validation : `py_compile` OK

### Résultat de la session — 2026-06-21 (session 1)
- Fondation routing de modèles par tâche : 11 nouvelles clés seedées dans `app_config` (routing/agent/synthesis/sentinel/archiviste en modes cost/perf + `perf_mode`) via INSERT OR IGNORE
- `load_config()` étendu pour retourner les 15 clés de configuration (4 existantes + 11 nouvelles)
- `get_model_for_task(task, config)` ajouté dans `model_router.py` — sélection du modèle selon la tâche et le flag `perf_mode`
- Validation : `py_compile` OK sur les deux fichiers, imports Python OK

### Résultat de la session — 2026-06-20
- Support `.doc` ajouté au RAG (CHECK DB, `DocumentLoader.load_doc()`, route `knowledge/import`)
- Nouveau script `tests/simulate_all.py` : simulation multi-jours automatique avec SENTINEL + auto-approbation proposals + génération de `bilan_simulation.md`
- Validation : `py_compile` OK, `pytest tests/test_rag_engine.py` 5 passed, `python tests/simulate_all.py --help` OK

---
## 9. ÉTAT D'AVANCEMENT

### Blocs de conception
| Bloc | Contenu | Statut |
|---|---|---|
| Bloc 1 | Structure projet + nomenclature | ✅ FIGÉ |
| Bloc 2 | Schéma de base de données | ✅ FIGÉ |
| Bloc 3 | System prompts Boss + agents | ✅ FIGÉ |
| Bloc 4 | API Routes | ✅ FIGÉ |
| Bloc 5 | UI specs | ✅ FIGÉ |
| Bloc 6 | Build V1 | ✅ FAIT |

### UI V1 — Specs

**chat.html — page principale**
- Sidebar gauche : liste des conversations (titre + date, nouvelle conversation)
- Zone centrale : fil de messages
- Indicateur de progression pendant le poll (étapes visibles)
- Bloc droit : éléments figés actifs de la conversation (ajout manuel possible)
- Badges agent non affichés sur les messages (décision D5)

**settings.html — paramètres**
- Formulaire profil entreprise (name, sector, tone, business_rules)
- Config modèle (model_id, openrouter_api_key, host, port)
- Liste agents actifs (lecture seule en V1)
- Dernières erreurs (GET /api/logs)

---
## 10. ORDRE DE BUILD V1 (réalisé)

### Phase 1 — Backend core ✅
- database.py, agents_templates.json, model_router.py, context_builder.py
- boss_service.py, agent_analyste.py, agent_redacteur.py, job_runner.py
- Tous les routers FastAPI, main.py

### Phase 2 — Frontend minimal fonctionnel ✅
- api.js, shared.js, chat.html + chat.js, index.html

### Phase 3 — UX et polish ✅
- Indicateurs de progression, bloc éléments figés, settings.html + settings.js
- Titrage auto conversation, gestion erreurs

### Phase 4 — Validation end-to-end 🟡 EN COURS
- Tests avec Neuraltech Consulting
- Cas nominaux + cas limites
- Corrections post-audit appliquées (routes pinned, blocage job, poll 1s)

### Blocs V2 — RAG Integration
| Bloc V2 | Contenu | Statut |
|---|---|---|
| BLOC 1 | Foundation V2 : 4 tables DB + profil Neuraltech + variables RAG + tests/ | ✅ FAIT |
| BLOC 2 | Moteur RAG (rag_engine.py) + tests unitaires | ✅ FAIT |
| BLOC 3 | Routes KB (knowledge.py) : upload PDF/MD/TXT, liste, delete | ✅ FAIT |
| BLOC 4 | Injection contexte KB dans context_builder.py | ✅ FAIT |
| BLOC 5 | Agent SENTINEL (sentinel_service.py) + signal job_runner | ✅ FAIT |
| BLOC 6 | Routes proposals (approbation/rejet learning_proposals) | ✅ FAIT |
| BLOC 7 | Script simulation corpus 14 jours (simulate_day.py) | ✅ FAIT |

---
## 11. CHECKLIST VALIDATION V1

### Backend
- [ ] init_db() crée les 8 tables sans erreur au premier démarrage
- [ ] seed_agents() charge les 2 agents depuis agents_templates.json
- [ ] POST /api/conversations/{id}/messages crée un job et retourne job_id
- [ ] POST message retourne 409 si un job est déjà actif sur cette conversation
- [ ] Le job passe bien par tous les états (PENDING → ROUTING → AGENT_RUNNING → SYNTHESIZING → DONE)
- [ ] Phase 1 retourne un JSON valide avec agent_code correct (ANALYSTE, REDACTEUR ou BOSS)
- [ ] Phase 2 retourne un JSON valide avec response + pinned
- [ ] Fallback JSON routing malformé : Boss répond directement + log ERROR
- [ ] Fallback JSON synthesis malformé : réponse brute retournée + log WARNING
- [ ] Les tokens sont loggés dans model_decision_log (ROUTING + SYNTHESIS = 2 lignes min, 3 si agent appelé)
- [ ] company_profile : PUT crée ou met à jour (INSERT OR REPLACE id=1)
- [ ] GET /api/config ne retourne jamais la clé API en clair

### Frontend
- [ ] Polling toutes les secondes sur /api/jobs/{id}
- [ ] Indicateur "Le Boss analyse votre demande..." affiché pendant ROUTING
- [ ] Indicateur "[Agent] au travail..." affiché pendant AGENT_RUNNING
- [ ] Indicateur "Synthèse en cours..." affiché pendant SYNTHESIZING
- [ ] Éléments figés affichés dans le bloc droit après chaque réponse Boss
- [ ] Ajout manuel d'un élément épinglé fonctionne
- [ ] Désépinglage (soft-delete) fonctionne et retire l'élément de l'UI
- [ ] Nouvelle conversation : aucun pinned affiché (ardoise vierge)
- [ ] Formulaire settings : profil entreprise sauvegarde et recharge correctement
- [ ] Formulaire settings : config modèle sauvegarde (clé API masquée, jamais pré-remplie)

### Cas limites
- [ ] Message sans profil entreprise configuré → Boss fonctionne avec "Profil non configuré"
- [ ] Timeout OpenRouter → job passe en ERROR, message d'erreur affiché dans le chat
- [ ] JSON routing malformé → Boss répond directement, pas de crash
- [ ] Demande ambiguë → BOSS direct, pas de délégation à un agent
- [ ] Tentative d'envoyer un 2e message pendant un job actif → bloqué (UI désactivée + 409 API)

---
## 12. ROADMAP V2 (hors scope V1)
| Fonctionnalité | Priorité |
|---|---|
| Streaming des réponses (SSE) | P1 |
| UI d'édition des agents (clone + personnalisation) | P1 |
| Questionnaire d'onboarding → proposition équipe agents | P1 |
| Agent d'amélioration des contextes et prompts (SENTINEL) | **IN SCOPE V2** |
| Exécution parallèle d'agents | P2 |
| Multi-tenant (plusieurs entreprises, une instance) | P2 |
| Multi-utilisateurs par entreprise avec rôles | P2 |
| Analytics dashboard coûts/usage | P2 |
| API pour intégrations tierces | P3 |
| GDPR tooling (export, suppression) | P3 |
| SSO / authentification avancée | P3 |
| Hébergement modèle local (vision finale) | P3 |

---
## 13. RÈGLES DU PROJET
- Jamais de `print()` en production — `logger = logging.getLogger("bigbertha")`
- Jamais de hardcode de prompts agents dans le Python — tout dans `agents_templates.json` / DB
- Prompts Boss V1 : hardcodés dans `context_builder.py` (décision V1 — pas en DB)
- Jamais d'ORM — sqlite3 natif uniquement
- Jamais de framework JS — fetch natif uniquement
- Tous les chemins via `pathlib.Path`
- Un seul job actif par conversation à la fois (backend retourne 409 si déjà actif)
- `app_config['openrouter_api_key']` jamais retourné en clair dans les réponses API
- `.env` et `bigbertha.db` toujours dans `.gitignore`
