# RAG Integration Spec — Big Bertha V2
> Document de référence pour l'implémentation. Lire EN ENTIER avant de coder.
> Source : décisions prises dans la session de conception V2 (2026-06-20).

---

## 1. CONTEXTE

On intègre un moteur RAG (Retrieval-Augmented Generation) dans Big Bertha pour que
les agents aient accès à une base de connaissance documentaire persistante.

Source du moteur RAG : https://github.com/tezcatlypoca/local-llm/tree/rag
- On récupère UNIQUEMENT `src/rag.py` (moteur pur Python, framework-agnostique)
- Les routes Flask de ce repo sont JETÉES — on réécrit en FastAPI
- On remplace les dépendances lourdes (voir section 3)

---

## 2. ARCHITECTURE SINGLETON

### Pattern retenu
Le `RAGManager` est un singleton module-level dans `backend/services/rag_engine.py`.
Il est initialisé UNE FOIS au démarrage dans le `lifespan` de `main.py`.
Il est importé directement par `context_builder.py` et `sentinel_service.py`.

```python
# backend/services/rag_engine.py
_manager: RAGManager | None = None

def init_rag(collection_name: str = "bigbertha_prod") -> RAGManager:
    global _manager
    # initialise ChromaDB + fastembed
    _manager = RAGManager(collection_name=collection_name)
    return _manager

def get_rag() -> RAGManager | None:
    return _manager  # retourne None si non initialisé — jamais d'exception
```

```python
# backend/main.py — dans lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage Big Bertha — init DB + seed + RAG")
    init_db()
    seed_agents()
    collection = os.getenv("RAG_COLLECTION_NAME", "bigbertha_prod")
    try:
        init_rag(collection_name=collection)
        logger.info("RAG initialisé — collection : %s", collection)
    except Exception as exc:
        logger.error("RAG init échoué — mode dégradé : %s", exc)
    yield
    logger.info("Arrêt Big Bertha")
```

### Règle absolue : fallback garanti
Partout où `get_rag()` est appelé :
```python
rag = get_rag()
if rag is None:
    return ""  # section KB omise, pas d'exception
```

---

## 3. DÉPENDANCES

### Nouvelles dépendances à ajouter à requirements.txt
```
chromadb>=0.5.0
fastembed>=0.2.0
pypdf>=4.3.1
python-docx>=1.1.2
python-multipart>=0.0.9
```

### Ce qu'on NE prend PAS du repo source
- `torch`, `torchvision`, `torchaudio` → remplacés par `fastembed` (ONNX, ~50 Mo)
- `sentence-transformers` → remplacé par `fastembed`
- `transformers`, `accelerate` → inutiles sans torch
- `faiss-cpu` → doublon, ChromaDB gère la recherche
- `langchain`, `langchain-community` → remplacés par TextSplitter maison (30 lignes)
- `tiktoken`, `unstructured` → inutiles
- `Flask`, `flask-cors` → on est en FastAPI

### Embedding function à utiliser
```python
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
ef = DefaultEmbeddingFunction()
```
Note : `FastEmbedEmbeddingFunction` a été supprimée dans ChromaDB >= 1.x.
`DefaultEmbeddingFunction` utilise `all-MiniLM-L6-v2` via `onnxruntime` (transitive dep de chromadb).
Même modèle, même qualité, zéro dépendance supplémentaire. `fastembed` n'est PAS requis.

---

## 4. RÈGLES ASYNC

ChromaDB et fastembed sont synchrones. FastAPI est async. Règle impérative :

```python
import anyio

# Dans toute route FastAPI ou service appelé depuis job_runner :
result = await anyio.to_thread.run_sync(rag.search, query, top_k)
```

Cette règle s'applique à TOUTES les opérations RAG dans :
- `backend/routers/knowledge.py` (routes)
- `backend/services/context_builder.py` (injection contexte)
- `backend/services/sentinel_service.py` (analyse SENTINEL)

`job_runner.py` est déjà async — les appels RAG qu'il fait indirectement via
`context_builder.py` bénéficient de cette protection.

---

## 5. VARIABLES D'ENVIRONNEMENT

À ajouter dans `.env.example` :
```
# RAG
RAG_COLLECTION_NAME=bigbertha_prod
RAG_PERSIST_DIR=backend/data/chroma_db
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_CHUNK_SIZE=400
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3
```

Ces variables sont lues directement depuis `os.getenv()` dans `rag_engine.py`.
Elles NE SONT PAS exposées dans les routes API ni dans l'UI (settings infrastructure, pas user).

`backend/data/chroma_db/` doit être dans `.gitignore`.

---

## 6. SCHÉMA DB V2 — 4 nouvelles tables

À ajouter dans `database.py → init_db()`, après les tables existantes.
Toutes avec `CREATE TABLE IF NOT EXISTS` — idempotent, ne casse pas la V1.

```sql
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('txt','md','pdf','docx','py')),
    content_hash TEXT NOT NULL UNIQUE,
    chroma_doc_ids TEXT NOT NULL DEFAULT '[]',
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PROCESSING'
        CHECK (status IN ('PROCESSING','INDEXED','ERROR')),
    error_message TEXT,
    test_session_id INTEGER,
    simulated_date TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (test_session_id) REFERENCES test_sessions(id)
);

CREATE TABLE IF NOT EXISTS learning_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sentinel_report_id INTEGER NOT NULL,
    proposal_type TEXT NOT NULL
        CHECK (proposal_type IN ('UPDATE_AGENT_PROMPT','UPDATE_COMPANY_RULE','ARCHIVE_DOCUMENT')),
    target TEXT NOT NULL,
    content TEXT NOT NULL,
    previous_value TEXT,
    rationale TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (sentinel_report_id) REFERENCES sentinel_reports(id)
);

CREATE TABLE IF NOT EXISTS test_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0,1)),
    chroma_collection TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS sentinel_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_baseline INTEGER NOT NULL DEFAULT 0 CHECK (is_baseline IN (0,1)),
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    metrics TEXT NOT NULL DEFAULT '{}',
    observations TEXT NOT NULL DEFAULT '[]',
    delta_vs_baseline TEXT,
    jobs_analyzed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Nouveaux index
```sql
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status
    ON knowledge_documents(status, is_active);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_session
    ON knowledge_documents(test_session_id);
CREATE INDEX IF NOT EXISTS idx_learning_proposals_status
    ON learning_proposals(status);
CREATE INDEX IF NOT EXISTS idx_sentinel_reports_baseline
    ON sentinel_reports(is_baseline);
```

### Nouvelles clés app_config (seed dans init_db)
```sql
INSERT OR IGNORE INTO app_config (key, value) VALUES ('sentinel_suggestion_pending', '0');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('active_test_session_id', '');
```

---

## 7. PROFIL ENTREPRISE — NEURALTECH CONSULTING

Remplacer le seed "Cabinet Moreau Conseil" par ce profil dès BLOC 1.
À insérer dans `init_db()` via `INSERT OR IGNORE INTO company_profile`.

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

---

## 8. INJECTION DE CONTEXTE KB

### Section injectée dans les prompts Boss et Agent
```
## Base documentaire

{KB_CONTEXT}

(extraits des documents les plus pertinents pour cette demande — ne pas halluciner de sources)
```

### Règle d'injection
- `build_routing_payload` : injecté après `{ELEMENTS_FIGES}`, avant les messages
- `build_agent_payload` : injecté dans `user_content`, entre profil entreprise et tâche
- Si KB vide ou RAG None → section entièrement omise (pas de placeholder vide)
- `top_k` lu depuis `os.getenv("RAG_TOP_K", "3")`

### Format des chunks retournés
```python
def get_context_for_query(query: str, top_k: int = 3) -> str:
    results = self.search(query, top_k)
    if not results:
        return ""
    parts = []
    for r in results:
        source = r.get("metadata", {}).get("filename", "document")
        parts.append(f"[Source : {source}]\n{r['document']}")
    return "\n\n---\n\n".join(parts)
```

---

## 9. SENTINEL — FORMAT JSON STRICT

Le SENTINEL doit retourner UNIQUEMENT ce JSON, sans texte avant/après :

```json
{
  "score": 72,
  "metrics": {
    "routing_coherence": 0.85,
    "pinned_rate": 0.3,
    "boss_direct_rate": 0.15,
    "kb_citation_rate": 0.6
  },
  "observations": [
    "Le RÉDACTEUR est sollicité majoritairement pour des briefs techniques.",
    "Le taux d'épinglage est élevé — les utilisateurs retiennent des contraintes récurrentes."
  ],
  "delta_vs_baseline": {
    "score_delta": +12,
    "routing_coherence_delta": +0.1,
    "summary": "Amélioration notable de la cohérence du routing depuis le baseline."
  },
  "proposals": [
    {
      "proposal_type": "UPDATE_AGENT_PROMPT",
      "target": "REDACTEUR",
      "content": "Nouveau system_prompt complet ici...",
      "rationale": "Le RÉDACTEUR produit systématiquement des sections 'Limites' — les intégrer dans le prompt par défaut.",
      "previous_value": null
    }
  ]
}
```

### Règles proposals
- `proposal_type` : UNIQUEMENT `UPDATE_AGENT_PROMPT`, `UPDATE_COMPANY_RULE`, `ARCHIVE_DOCUMENT`
- `target` :
  - `UPDATE_AGENT_PROMPT` → code agent (`ANALYSTE`, `REDACTEUR`, etc.)
  - `UPDATE_COMPANY_RULE` → `"company_profile"`
  - `ARCHIVE_DOCUMENT` → id du document en string (`"42"`)
- `content` : nouvelle valeur complète (pas un diff, la valeur entière)
- `previous_value` : toujours `null` dans la proposal, rempli au moment de l'APPROVED
- Maximum 3 proposals par rapport
- `delta_vs_baseline` : `null` si ce rapport EST le baseline

---

## 10. SIGNAL SENTINEL — LOGIQUE DANS JOB_RUNNER

Après chaque job DONE, dans `job_runner.py` :

```python
def _check_sentinel_signal(db: sqlite3.Connection, conversation_id: int) -> None:
    # Condition 1 : trop de pinned dans cette conversation
    pinned_count = db.execute(
        "SELECT COUNT(*) as cnt FROM pinned_context WHERE conversation_id = ? AND is_active = 1",
        (conversation_id,)
    ).fetchone()["cnt"]

    # Condition 2 : BOSS direct > 40% sur les 20 derniers jobs (indique routing incohérent)
    rows = db.execute(
        "SELECT routing_output FROM jobs WHERE status='DONE' ORDER BY id DESC LIMIT 20"
    ).fetchall()
    boss_count = sum(
        1 for r in rows
        if r["routing_output"] and '"agent_code": "BOSS"' in r["routing_output"]
    )
    boss_rate = boss_count / max(len(rows), 1)

    if pinned_count >= 8 or boss_rate > 0.40:
        db.execute(
            "UPDATE app_config SET value='1', updated_at=datetime('now') WHERE key='sentinel_suggestion_pending'"
        )
        db.commit()
```

Dans `context_builder.py`, dans `BOSS_ROUTING_PROMPT`, ajouter conditionnellement :

```python
config = load_config()
if config.get("sentinel_suggestion_pending") == "1":
    sentinel_hint = "\n\n(Note système : un bilan de l'équipe est disponible si l'utilisateur le demande.)"
else:
    sentinel_hint = ""
```

---

## 11. COLLECTIONS CHROMADB

| Contexte | Nom de collection |
|---|---|
| Production | `bigbertha_prod` |
| Session test N | `bigbertha_test_{session_id}` |

`init_rag()` prend `collection_name` en paramètre.
En mode test actif (`app_config['active_test_session_id']` non vide) :
- Les imports de documents utilisent la collection test
- Les recherches de contexte utilisent la collection test
- La collection prod reste intacte

---

## 12. COLLECTIONS CHROMADB — SUPPRESSION

Lors d'un DELETE document :
1. Lire `knowledge_documents.chroma_doc_ids` (JSON array)
2. `collection.delete(ids=chroma_doc_ids)`
3. `UPDATE knowledge_documents SET is_active=0`

Lors d'un reset session test :
1. Récupérer `test_sessions.chroma_collection`
2. `client.delete_collection(name=chroma_collection)`
3. Supprimer tous `knowledge_documents WHERE test_session_id = ?`

---

## 13. STRUCTURE FICHIERS V2

```
BigBertha/
├── docs/
│   ├── rag_integration_spec.md    ← ce fichier
│   └── (existants...)
├── backend/
│   ├── services/
│   │   ├── rag_engine.py          ← NOUVEAU — moteur singleton
│   │   ├── sentinel_service.py    ← NOUVEAU — agent SENTINEL
│   │   └── (existants...)
│   ├── routers/
│   │   ├── knowledge.py           ← NOUVEAU — routes KB
│   │   └── (existants...)
│   └── data/
│       ├── bigbertha.db
│       └── chroma_db/             ← NOUVEAU (gitignored)
└── tests/
    ├── __init__.py                ← NOUVEAU
    ├── test_rag_engine.py         ← NOUVEAU — test standalone moteur
    ├── simulate_day.py            ← NOUVEAU — script simulation test
    └── corpus/
        ├── manifest.json          ← NOUVEAU — plan de test 14 jours
        └── (documents .md/.txt)   ← NOUVEAU
```

---

## 14. CRITÈRES DE VALIDATION PAR BLOC

| Bloc | Critère GO |
|---|---|
| BLOC 1 | 12 tables en DB, profil Neuraltech visible via GET /api/company-profile |
| BLOC 2 | `python -m pytest tests/test_rag_engine.py` passe, chroma_db/ créé |
| BLOC 3 | Import PDF + MD + TXT via UI → listés avec statut INDEXED |
| BLOC 4 | Question sur sujet importé → réponse cite le document |
| BLOC 5 | Après 15+ jobs → rapport SENTINEL avec score + proposals valides |
| BLOC 6 | Proposal APPROVED → system_prompt agent mis à jour en DB |
| BLOC 7 | `simulate_day.py --day 1` → docs importés + messages envoyés + reset propre |
