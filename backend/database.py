import sqlite3
import json
import os
import logging
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bigbertha.db"
AGENTS_JSON = Path(__file__).parent / "data" / "agents_templates.json"

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
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

CREATE TABLE IF NOT EXISTS test_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0,1)),
    chroma_collection TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('txt','md','pdf','docx','doc','py')),
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

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status
    ON knowledge_documents(status, is_active);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_session
    ON knowledge_documents(test_session_id);

CREATE INDEX IF NOT EXISTS idx_learning_proposals_status
    ON learning_proposals(status);

CREATE INDEX IF NOT EXISTS idx_sentinel_reports_baseline
    ON sentinel_reports(is_baseline);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info("Base de données initialisée.")
    finally:
        conn.close()


def load_config() -> dict:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT key, value FROM app_config WHERE key IN ('model_id', 'host', 'port', 'openrouter_api_key')"
        ).fetchall()
        return {row["key"]: row["value"] for row in rows}
    finally:
        conn.close()


def get_config_value(key: str, default: str = "") -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT value FROM app_config WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row and row["value"] is not None else default
    finally:
        conn.close()


def seed_agents() -> None:
    if not AGENTS_JSON.exists():
        logger.warning("agents_templates.json introuvable — seed ignoré.")
        return

    with open(AGENTS_JSON, encoding="utf-8") as f:
        agents = json.load(f)

    conn = get_connection()
    try:
        for agent in agents:
            conn.execute(
                """INSERT OR IGNORE INTO agents (code, name, description, system_prompt, is_active)
                   VALUES (:code, :name, :description, :system_prompt, :is_active)""",
                agent,
            )

        conn.execute(
            """INSERT OR IGNORE INTO company_profile (id, name, sector, tone, business_rules)
               VALUES (1, ?, ?, ?, ?)""",
            (
                "Neuraltech Consulting",
                "Conseil en intelligence artificielle et agents IA",
                "Professionnel, précis, orienté résultats. Pédagogue sans être condescendant. Langue : Français exclusivement, termes techniques anglais acceptés quand standard (RAG, LLM, fine-tuning...).",
                "- Toujours contextualiser les recommandations IA par rapport au besoin métier client\n- Citer les limites et risques des solutions proposées\n- Distinguer ce qui est production-ready de ce qui est expérimental\n- Structurer les livrables : contexte → analyse → recommandations → prochaines étapes\n- Ne jamais promettre de performances LLM sans benchmark sur les données réelles du client",
            ),
        )

        config_defaults = [
            ("model_id", os.getenv("MODEL_ID", "mistralai/mistral-nemo")),
            ("host", os.getenv("HOST", "0.0.0.0")),
            ("port", os.getenv("PORT", "8000")),
            ("openrouter_api_key", os.getenv("OPENROUTER_API_KEY", "")),
            ("boss_routing_prompt", ""),
            ("boss_synthesis_prompt", ""),
            ("sentinel_suggestion_pending", "0"),
            ("active_test_session_id", ""),
        ]
        for key, value in config_defaults:
            conn.execute(
                "INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)",
                (key, value),
            )

        conn.commit()
        logger.info("Seed agents et app_config effectué.")
    finally:
        conn.close()
