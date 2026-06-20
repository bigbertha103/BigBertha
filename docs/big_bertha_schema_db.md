# Schéma de base de données — Big Bertha (V1)

Document figé. SQLite, sqlite3 natif, zéro ORM. Toutes les tables sont créées
via `CREATE TABLE IF NOT EXISTS` dans `init_db()`.

---

## 1. conversations

Une conversation regroupe l'historique d'échanges avec un utilisateur.
Nouvelle conversation = ardoise vierge (pinned_context et historique repartent à zéro).

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| title | TEXT | — | NULL | titre affiché dans l'UI (heuristique 60 chars sur 1er message — voir big_bertha_system_prompts.md §5) |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage création |
| updated_at | TEXT | NOT NULL | datetime('now') | dernière activité, mis à jour par l'app à chaque nouveau message |

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 2. agents

Catalogue des agents disponibles. Seedée au démarrage depuis `agents_templates.json`.
Extensible en V2 sans migration : ajouter un agent = une ligne en plus.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant interne |
| code | TEXT | NOT NULL, UNIQUE | — | identifiant stable utilisé dans le JSON de routing du Boss (ex: 'ANALYSTE') |
| name | TEXT | NOT NULL | — | nom affiché |
| description | TEXT | — | NULL | description du rôle, injectée dans {AGENTS_DISPONIBLES} du prompt Boss Phase 1 |
| system_prompt | TEXT | NOT NULL | — | prompt système de l'agent (statique, pas de placeholder) |
| is_active | INTEGER | NOT NULL, CHECK (0,1) | 1 | permet de désactiver un agent sans le supprimer |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Justification** : `code` est séparé de `id` pour que le JSON de routing référence un identifiant stable ('ANALYSTE') et non un id numérique qui pourrait changer entre environnements.

---

## 3. messages

Le fil de conversation tel que vu par l'utilisateur. Les appels internes aux agents ne sont **pas** dans cette table.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | rattachement |
| role | TEXT | NOT NULL, CHECK ('user','boss') | — | qui parle |
| content | TEXT | NOT NULL | — | contenu du message |
| job_id | INTEGER | FK → jobs(id) | NULL | pour role='boss', le job qui a produit cette réponse ; NULL pour role='user' |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
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

**Note :** pas de colonne `agent_code` — la trace de ce que l'agent a reçu et renvoyé est dans `jobs` (agent_input/agent_output). Ajouter un role='agent' aurait pollué le fil de conversation côté UI.

---

## 4. jobs

Cœur du tracking. Une ligne par message utilisateur, trace l'intégralité du cycle de vie.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant, pollé via /api/jobs/{id} |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | rattachement |
| user_message_id | INTEGER | NOT NULL, FK → messages(id) | — | le message qui a déclenché ce job |
| status | TEXT | NOT NULL, CHECK (cf. liste) | 'PENDING' | état courant |
| selected_agent_id | INTEGER | FK → agents(id) | NULL | rempli après ROUTING |
| routing_output | TEXT | — | NULL | JSON brut produit par Boss Phase 1 |
| agent_input | TEXT | — | NULL | tâche envoyée à l'agent (champ task du routing) |
| agent_output | TEXT | — | NULL | résultat brut renvoyé par l'agent |
| final_response | TEXT | — | NULL | réponse finale composée par Boss Phase 2 |
| error_message | TEXT | — | NULL | rempli si status='ERROR' |
| created_at | TEXT | NOT NULL | datetime('now') | création du job |
| updated_at | TEXT | NOT NULL | datetime('now') | mis à jour à chaque changement de statut |
| completed_at | TEXT | — | NULL | rempli quand status passe à DONE ou ERROR |

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
```

**Justification :** 4 colonnes séparées (routing_output, agent_input, agent_output, final_response) plutôt qu'un blob JSON — debug et requêtes sans parsing JSON.

---

## 5. pinned_context

Éléments épinglés, scopés par conversation. Deux sources possibles.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | scope |
| content | TEXT | NOT NULL | — | contenu épinglé |
| source | TEXT | NOT NULL, CHECK ('boss','user') | — | qui a épinglé |
| job_id | INTEGER | FK → jobs(id) | NULL | si source='boss', le job de la Phase 2 concernée |
| is_active | INTEGER | NOT NULL, CHECK (0,1) | 1 | soft-delete : désépingler sans perdre l'historique |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
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
```

---

## 6. company_profile

Une seule ligne. Contexte entreprise injecté dans chaque appel LLM via `{PROFIL_ENTREPRISE}`.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY, CHECK (id = 1) | — | force une ligne unique |
| name | TEXT | NOT NULL | — | nom de l'entreprise cliente |
| sector | TEXT | — | NULL | secteur d'activité |
| tone | TEXT | — | NULL | ton de communication attendu |
| business_rules | TEXT | — | NULL | règles métier libres |
| updated_at | TEXT | NOT NULL | datetime('now') | dernière modification |

```sql
CREATE TABLE IF NOT EXISTS company_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    sector TEXT,
    tone TEXT,
    business_rules TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Unicité** : `CHECK (id = 1)` + `PRIMARY KEY` interdit toute ligne dont l'id n'est pas 1. L'app fait toujours `INSERT OR IGNORE ... (id=1)` puis `UPDATE ... WHERE id = 1`.

---

## 7. model_decision_log

Une ligne par appel LLM. 3 lignes par message utilisateur (routing, appel agent, synthèse).

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| job_id | INTEGER | NOT NULL, FK → jobs(id) | — | rattachement |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | dénormalisé pour requêtes coût par conversation sans jointure |
| phase | TEXT | NOT NULL, CHECK ('ROUTING','AGENT_CALL','SYNTHESIS') | — | quelle phase |
| agent_id | INTEGER | FK → agents(id) | NULL | rempli uniquement pour phase='AGENT_CALL' |
| model_name | TEXT | NOT NULL | — | modèle OpenRouter (TEXT libre, pas de CHECK — catalogue évolutif) |
| input_tokens | INTEGER | NOT NULL | 0 | tokens en entrée |
| output_tokens | INTEGER | NOT NULL | 0 | tokens en sortie |
| duration_ms | INTEGER | NOT NULL | 0 | durée de l'appel |
| cost_usd | REAL | — | NULL | coût si renvoyé par OpenRouter |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
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
```

**Requêtes coût :** coût total conversation → `SUM(cost_usd) WHERE conversation_id = ?` | par agent → `GROUP BY agent_id` | par phase → `GROUP BY phase`

---

## 8. app_config

Clé/valeur pour la config applicative.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| key | TEXT | PRIMARY KEY | — | nom de la clé |
| value | TEXT | — | NULL | valeur (toujours TEXT, parsing à la charge de l'app) |
| updated_at | TEXT | NOT NULL | datetime('now') | dernière modification |

```sql
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## Index

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

---

## Seed data

```sql
INSERT OR IGNORE INTO agents (code, name, description, system_prompt, is_active)
SELECT code, name, description, system_prompt, is_active
FROM json_each(readfile('backend/data/agents_templates.json'));
-- NB : seed via Python dans database.py — voir seed_agents()

INSERT OR IGNORE INTO app_config (key, value) VALUES ('boss_routing_prompt', '');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('boss_synthesis_prompt', '');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('model_id', 'anthropic/claude-sonnet-4-5');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('openrouter_api_key', '');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('host', '0.0.0.0');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('port', '8000');
```

---

## Choix et décisions

**Ordre de création des tables.** Référence mutuelle entre `jobs` et `messages`. SQLite ne vérifie pas l'existence de la table cible au `CREATE TABLE` — l'ordre n'a pas d'importance. Flux réel : message user créé (job_id NULL) → job créé → message boss créé (job_id renseigné).

**Traçabilité des phases.** 4 colonnes texte séparées dans `jobs` plutôt qu'un blob JSON — zéro parsing pour le debug.

**Distinction des types de message.** `messages` ne porte que `user` et `boss` — les agents ne parlent pas directement à l'utilisateur. Leur trace est dans `jobs.agent_input` / `jobs.agent_output` et dans `model_decision_log`.

**Soft-delete sur pinned_context.** `is_active` plutôt que DELETE pur — cohérent avec la décision "pas de limite d'historique, on garde tout" en V1.

**Dénormalisation de `conversation_id` dans model_decision_log.** Permet les requêtes de coût par conversation sans jointure sur `jobs`. Redondance assumée contre performance sur une table à fort volume (3 lignes/message).

**model_name en TEXT libre sans CHECK.** Le catalogue OpenRouter évolue fréquemment — un CHECK forcerait une migration à chaque nouveau modèle.

**Unicité de company_profile.** `PRIMARY KEY CHECK (id = 1)` porte la contrainte au niveau du schéma, sans logique applicative.
