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

        config_defaults = [
            ("model_id", os.getenv("MODEL_ID", "anthropic/claude-sonnet-4-5")),
            ("host", os.getenv("HOST", "0.0.0.0")),
            ("port", os.getenv("PORT", "8000")),
            ("openrouter_api_key", os.getenv("OPENROUTER_API_KEY", "")),
            ("boss_routing_prompt", ""),
            ("boss_synthesis_prompt", ""),
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
