# Contrat API — Big Bertha (V1)

Document figé. Backend FastAPI + SQLite, zéro ORM. Contrat de développement direct pour Cascade.

Amendements v1.1 (issus du wireframe Bloc 5) :
- A1 : `GET /api/jobs/{id}` expose `agent_code` dès `AGENT_RUNNING` (pas seulement à `DONE`)
- A2 : `PATCH /api/conversations/{id}` ajouté (route 4.16 — édition du titre)

---

## Convention de codes HTTP (appliquée à toutes les routes)

| Code | Usage |
|---|---|
| 200 | Lecture ou écriture réussie avec corps de réponse |
| 201 | Création de ressource, corps de la ressource créée retourné |
| 202 | Traitement asynchrone déclenché (job), corps minimal retourné |
| 204 | Suppression réussie, pas de corps |
| 404 | Ressource introuvable |
| 422 | Corps de requête invalide ou champ manquant |
| 500 | Erreur serveur non gérée (implicite) |

---

## Décisions D1-D5

**D1 — DELETE /api/conversations/{id} : hard delete en cascade.**
Le schéma ne porte pas de champ `is_deleted` — seul `pinned_context` a un flag soft-delete pour un usage différent (désépinglage réversible). Ajouter un soft-delete de conversation modifierait un schéma déjà validé. Hard delete en cascade = option cohérente et la plus simple pour V1.

**D2 — GET /api/conversations : retour intégral, sans pagination.**
Outil B2B à usage interne, volumétrie modeste en V1. Pagination non justifiée tant que le volume réel n'est pas mesuré.

**D3 — POST /api/conversations/{id}/messages : réponse = `{"job_id": ...}` uniquement.**
Le frontend connaît déjà le message qu'il vient d'envoyer — il peut l'afficher immédiatement sans attendre l'écho. Le seul élément qu'il n'a pas encore, c'est le job_id à poller.

**D4 — GET /api/jobs/{job_id} quand status=DONE : `final_response` + `agent_code`, sans `routing_rationale`.**
`agent_code` a une valeur d'usage réelle (afficher "Traité par : Analyste" dans l'UI, debug léger) pour un coût nul. `routing_rationale` est un détail de raisonnement interne du Boss — si un besoin de debug plus poussé apparaît, une route dédiée peut être ajoutée sans toucher celle-ci.

**D5 — PUT /api/config : mise à jour partielle, clé par clé.**
Le body ne contient que les clés à modifier ; les clés absentes restent inchangées. Cohérent avec la structure clé/valeur de `app_config`. Évite le piège d'un remplacement complet silencieux.

---

## Notes d'implémentation pour Bloc 6

**Job asynchrone (route 4.5)** : le déclenchement du traitement après création du job se fait via `BackgroundTasks` de FastAPI. La route retourne `job_id` avant que le traitement commence.

**agent_code en 4.6** : ne pas dériver de `selected_agent_id` (NULL quand Boss répond directement). Toujours extraire de `routing_output` :
```python
import json
routing = json.loads(job["routing_output"])
agent_code = routing.get("agent_code")  # "ANALYSTE", "REDACTEUR", ou "BOSS"
```

**Boss prompts en V1** : `boss_routing_prompt` et `boss_synthesis_prompt` dans `app_config` sont des placeholders V2. En V1, les prompts Boss sont des constantes Python dans `context_builder.py` (textes de `docs/big_bertha_system_prompts.md` §1 et §2). Ne pas lire depuis app_config.

**company_profile au démarrage** : aucune ligne créée par le seed. Au premier lancement, GET /api/company-profile retourne 404. Le frontend doit rediriger vers la page de configuration initiale.

---

## 4.1 — POST /api/conversations

Crée une conversation. `title` optionnel.

**Request**
```json
{ "title": "Benchmark concurrents Auvergne-Rhône-Alpes" }
```
`title` peut être omis ou `null`.

**Response — 201**
```json
{
  "id": 3,
  "title": "Benchmark concurrents Auvergne-Rhône-Alpes",
  "created_at": "2026-06-20T10:00:00",
  "updated_at": "2026-06-20T10:00:00"
}
```

**Codes HTTP** : 201 succès · 422 si `title` présent mais pas une chaîne.

**Comportement** : `INSERT INTO conversations (title) VALUES (?)`. `created_at` et `updated_at` posés par le DEFAULT SQL.

**Cas limites** : `title` absent ou `null` → conversation créée avec `title = NULL` ; chaîne vide `""` → acceptée ; aucune limite de longueur.

---

## 4.2 — GET /api/conversations

Liste toutes les conversations, triées par activité récente.

**Response — 200**
```json
[
  {
    "id": 3,
    "title": "Benchmark concurrents Auvergne-Rhône-Alpes",
    "created_at": "2026-06-19T09:00:00",
    "updated_at": "2026-06-20T10:00:00"
  },
  {
    "id": 1,
    "title": null,
    "created_at": "2026-06-18T14:00:00",
    "updated_at": "2026-06-18T14:05:00"
  }
]
```

**Codes HTTP** : 200 toujours (même liste vide).

**Comportement** : `SELECT * FROM conversations ORDER BY updated_at DESC`. Pas de pagination.

**Cas limites** : aucune conversation → `[]`.

---

## 4.3 — DELETE /api/conversations/{id}

Supprime une conversation et tout son contenu (hard delete cascade).

**Response — 204** : pas de corps.

**Codes HTTP** : 204 succès · 404 si la conversation n'existe pas.

**Comportement** : transaction unique, dans cet ordre :
```sql
DELETE FROM model_decision_log WHERE conversation_id = ?;
DELETE FROM pinned_context     WHERE conversation_id = ?;
DELETE FROM jobs               WHERE conversation_id = ?;
DELETE FROM messages           WHERE conversation_id = ?;
DELETE FROM conversations      WHERE id = ?;
```

**Cas limites** : `id` introuvable → 404 ; second DELETE sur le même `id` → 404 (non idempotent) ; aucune confirmation gérée côté API — c'est au frontend de confirmer avec l'utilisateur avant l'appel.

---

## 4.4 — GET /api/conversations/{id}/messages

Historique complet d'une conversation (messages `user` et `boss`).

**Response — 200**
```json
[
  {
    "id": 10,
    "role": "user",
    "content": "Bonjour, comment ça marche ?",
    "job_id": null,
    "created_at": "2026-06-20T10:00:00"
  },
  {
    "id": 11,
    "role": "boss",
    "content": "Bonjour, ravi de vous accompagner...",
    "job_id": 7,
    "created_at": "2026-06-20T10:00:04"
  }
]
```

**Codes HTTP** : 200 succès · 404 si la conversation n'existe pas.

**Comportement** : vérifier l'existence de la conversation (sinon 404), puis `SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC`.

**Cas limites** : conversation existante sans message → `[]` (pas 404) ; path param non numérique → 422.

---

## 4.5 — POST /api/conversations/{id}/messages

Reçoit le message utilisateur, crée le message et le job, retourne immédiatement.

**Request**
```json
{ "content": "Peux-tu me faire un benchmark des 3 principaux concurrents ?" }
```

**Response — 202**
```json
{ "job_id": 42 }
```

**Codes HTTP** : 202 succès · 404 si la conversation n'existe pas · 422 si `content` est absent ou vide.

**Comportement**, dans l'ordre :
1. Vérifier l'existence de la conversation (sinon 404).
2. Valider `content` (non vide après `strip()`, sinon 422).
3. `INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', ?)`.
4. `INSERT INTO jobs (conversation_id, user_message_id, status) VALUES (?, ?, 'PENDING')`.
5. `UPDATE conversations SET updated_at = datetime('now') WHERE id = ?`.
6. Déclencher le traitement asynchrone via `BackgroundTasks` FastAPI (voir notes d'implémentation).
7. Retourner `{"job_id": ...}` sans attendre la fin du traitement.

**Cas limites** : `content` absent ou vide (après strip) → 422 ; conversation introuvable → 404 ; appels simultanés → aucun verrou applicatif en V1.

---

## 4.6 — GET /api/jobs/{job_id}

État courant du job, contenu variable selon `status`.

**Response — 200, états PENDING · ROUTING** (routing non encore terminé)
```json
{ "id": 42, "status": "ROUTING" }
```

**Response — 200, états AGENT_RUNNING · SYNTHESIZING** (amendement A1 — routing terminé, agent connu)
```json
{ "id": 42, "status": "AGENT_RUNNING", "agent_code": "ANALYSTE" }
```

**Response — 200, status=DONE**
```json
{
  "id": 42,
  "status": "DONE",
  "final_response": "## Benchmark concurrentiel...",
  "agent_code": "ANALYSTE"
}
```

**Response — 200, status=ERROR**
```json
{
  "id": 42,
  "status": "ERROR",
  "error_message": "Le service LLM n'a pas répondu."
}
```

**Codes HTTP** : 200 si le job existe · 404 si `job_id` introuvable.

**Comportement** : `SELECT * FROM jobs WHERE id = ?`. Construction de la réponse :
- `PENDING`, `ROUTING` → `id` + `status` uniquement (`routing_output` pas encore écrit).
- `AGENT_RUNNING`, `SYNTHESIZING` → ajoute `agent_code` (extrait de `routing_output` — voir notes d'implémentation).
- `DONE` → ajoute `final_response` + `agent_code`.
- `ERROR` → ajoute `error_message`.

**⚠️ Point critique** : `agent_code` n'est **pas** une jointure sur `selected_agent_id` (NULL quand Boss répond directement, "BOSS" n'étant pas une ligne de la table `agents`). Toujours extraire depuis `routing_output` — voir notes d'implémentation.

**Cas limites** : `job_id` introuvable → 404 ; job `ERROR` sans `error_message` (bug applicatif théorique) → retourner `error_message: null`.

---

## 4.7 — GET /api/conversations/{id}/pinned

Éléments figés actifs d'une conversation.

**Response — 200**
```json
[
  {
    "id": 5,
    "content": "Toujours utiliser la raison sociale complète 'Dupont Industries SA'.",
    "source": "user",
    "created_at": "2026-06-20T10:05:00"
  }
]
```

**Codes HTTP** : 200 succès · 404 si la conversation n'existe pas.

**Comportement** : vérifier l'existence de la conversation, puis `SELECT id, content, source, created_at FROM pinned_context WHERE conversation_id = ? AND is_active = 1 ORDER BY created_at ASC`.

**Cas limites** : aucun élément actif → `[]`.

---

## 4.8 — POST /api/conversations/{id}/pinned

Épingle manuellement un élément (`source = 'user'`). Pas de limite de nombre.

**Request**
```json
{ "content": "Le budget client ne doit jamais dépasser 15 000 € HT." }
```

**Response — 201**
```json
{
  "id": 6,
  "content": "Le budget client ne doit jamais dépasser 15 000 € HT.",
  "source": "user",
  "created_at": "2026-06-20T10:06:00"
}
```

**Codes HTTP** : 201 succès · 404 si la conversation n'existe pas · 422 si `content` absent ou vide.

**Comportement** : `INSERT INTO pinned_context (conversation_id, content, source, is_active) VALUES (?, ?, 'user', 1)`.

**Cas limites** : `content` vide → 422 ; aucune limite de nombre d'éléments — le plafond de 2/tour du Boss Phase 2 s'applique uniquement à l'épinglage automatique, pas à l'épinglage manuel délibéré de l'utilisateur.

---

## 4.9 — DELETE /api/pinned/{id}

Désépingle un élément (soft delete : `is_active = 0`).

**Response — 204** : pas de corps.

**Codes HTTP** : 204 succès · 404 si `id` introuvable.

**Comportement** : `UPDATE pinned_context SET is_active = 0 WHERE id = ?`. Vérifier le nombre de lignes affectées pour distinguer "trouvé" de "introuvable".

**Cas limites** : élément déjà `is_active = 0` → 204 (idempotent — la ligne existe, seul son flag change) ; `id` totalement inexistant → 404.

---

## 4.10 — GET /api/agents

Liste des agents actifs, sans le `system_prompt`.

**Response — 200**
```json
[
  {
    "id": 1,
    "code": "ANALYSTE",
    "name": "Analyste",
    "description": "Recherche, synthèse et analyse d'information",
    "is_active": 1,
    "created_at": "2026-06-15T08:00:00"
  },
  {
    "id": 2,
    "code": "REDACTEUR",
    "name": "Rédacteur",
    "description": "Rédaction de documents professionnels",
    "is_active": 1,
    "created_at": "2026-06-15T08:00:00"
  }
]
```

**Codes HTTP** : 200 toujours.

**Comportement** : `SELECT id, code, name, description, is_active, created_at FROM agents WHERE is_active = 1`. `system_prompt` exclu au niveau SQL, pas filtré après coup.

**Cas limites** : aucun agent actif → `[]` (théorique, le seed garantit les deux agents au démarrage).

---

## 4.11 — GET /api/company-profile

Retourne le profil entreprise (ligne unique `id = 1`).

**Response — 200**
```json
{
  "id": 1,
  "name": "Cabinet Moreau Conseil",
  "sector": "Conseil en stratégie et management",
  "tone": "Professionnel, structuré, direct. Jamais familier.",
  "business_rules": "Toujours structurer les livrables avec des titres clairs. Citer explicitement les hypothèses posées. Ne jamais s'engager sur des chiffres sans les sourcer. Terminer toute analyse par des recommandations actionnables.",
  "updated_at": "2026-06-15T08:00:00"
}
```

**Codes HTTP** : 200 si la ligne existe · 404 si jamais configurée.

**Comportement** : `SELECT * FROM company_profile WHERE id = 1`.

**Cas limites** : profil jamais configuré → 404 (le frontend doit rediriger vers l'écran de configuration initiale — voir notes d'implémentation).

---

## 4.12 — PUT /api/company-profile

Crée ou remplace intégralement le profil entreprise (upsert sur `id = 1`).

**Request**
```json
{
  "name": "Cabinet Moreau Conseil",
  "sector": "Conseil en stratégie et management",
  "tone": "Professionnel, structuré, direct. Jamais familier.",
  "business_rules": "Toujours structurer les livrables avec des titres clairs."
}
```

**Response — 200** : la ligne mise à jour, même format que 4.11.

**Codes HTTP** : 200 succès · 422 si `name` absent (`NOT NULL`).

**Comportement** :
```sql
INSERT OR REPLACE INTO company_profile (id, name, sector, tone, business_rules, updated_at)
VALUES (1, ?, ?, ?, ?, datetime('now'));
```

**⚠️ Piège** : `INSERT OR REPLACE` remplace la ligne entière — un champ absent du body est écrasé à `NULL`. Le frontend doit toujours envoyer l'objet complet (GET → modifier → PUT), jamais un diff partiel. Différent de 4.14 qui est volontairement partielle.

---

## 4.13 — GET /api/config

Retourne les clés de configuration non sensibles.

**Response — 200**
```json
{
  "model_id": "anthropic/claude-sonnet-4-5",
  "host": "0.0.0.0",
  "port": "8000"
}
```

**Codes HTTP** : 200 toujours.

**Comportement** : `SELECT key, value FROM app_config WHERE key IN ('model_id', 'host', 'port')`. `openrouter_api_key` exclu structurellement par la clause WHERE.

**Cas limites** : une clé non encore configurée → absente de l'objet de réponse (pas de `null`) — pour que le frontend distingue "non configuré" de "configuré à vide".

---

## 4.14 — PUT /api/config

Met à jour une ou plusieurs clés (mise à jour partielle, D5).

**Request** (exemple deux clés)
```json
{
  "model_id": "anthropic/claude-opus-4-8",
  "openrouter_api_key": "sk-..."
}
```

**Response — 200** : uniquement les clés effectivement mises à jour.
```json
{
  "model_id": "anthropic/claude-opus-4-8",
  "openrouter_api_key": "sk-..."
}
```

**Codes HTTP** : 200 succès · 422 si body vide ou contient une clé hors whitelist.

**Comportement** : whitelist V1 = `model_id`, `host`, `port`, `openrouter_api_key`. Pour chaque clé du body dans la whitelist :
```sql
INSERT OR REPLACE INTO app_config (key, value, updated_at) VALUES (?, ?, datetime('now'));
```
Clés absentes du body → inchangées en base.

**Cas limites** : clé non reconnue dans le body → 422 (rejet de la requête entière, pas d'ignorance silencieuse — une faute de frappe frontend doit être visible) ; valeur non-string (ex: `port` en nombre) → coercition en TEXT acceptée ; body vide `{}` → 422.

---

## 4.16 — PATCH /api/conversations/{id}  *(amendement A2)*

Met à jour le titre d'une conversation.

**Request**
```json
{ "title": "Benchmark concurrents AURA 2024" }
```
`title` peut être `null` pour remettre la conversation sans titre.

**Response — 200**
```json
{
  "id": 3,
  "title": "Benchmark concurrents AURA 2024",
  "created_at": "2026-06-20T10:00:00",
  "updated_at": "2026-06-20T10:00:00"
}
```

**Codes HTTP** : 200 succès · 404 si la conversation n'existe pas · 422 si `title` présent mais pas une chaîne ou null.

**Comportement** :
```sql
UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?;
```
Vérifier l'existence avant UPDATE (sinon 404).

**Cas limites** : `title = null` → accepté, efface le titre ; `title = ""` → accepté (chaîne vide, pas de validation métier en V1) ; champ `title` absent du body → 422 (body doit toujours contenir `title`).

---

## 4.15 — GET /api/logs

Dernières lignes du fichier de log applicatif.

**Response — 200**
```json
[
  "2026-06-20 10:00:01 INFO Job 42 started",
  "2026-06-20 10:00:04 INFO Job 42 status=DONE"
]
```

**Codes HTTP** : 200 toujours, y compris si le fichier n'existe pas.

**Comportement** : lire `backend/data/bigbertha.log`, retourner les 50 dernières lignes. Une ligne de log = un élément du tableau.

**Cas limites** : fichier absent → `[]` ; fichier vide → `[]` ; moins de 50 lignes → retourner tout ; caractères non-UTF8 → décoder avec remplacement plutôt que faire échouer la route.
