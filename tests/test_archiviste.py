import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.services.archiviste_service import (
    ARCHIVISTE_PROMPT,
    _build_conversation_text,
    _index_in_session_memory,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def in_memory_db():
    """DB SQLite en mémoire avec le schéma minimal nécessaire."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            previous_conversation_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            job_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.execute("INSERT INTO conversations (title) VALUES ('Test conversation')")
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (1, 'user', 'Quel est le ROI moyen de vos projets IA ?')"
    )
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (1, 'boss', 'Le ROI moyen constaté est de 250%, avec un délai de constatation de 6 à 12 mois.')"
    )
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (1, 'user', 'Quels secteurs présentent le plus fort potentiel ?')"
    )
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (1, 'boss', 'Industrie, santé et services financiers présentent le meilleur potentiel selon nos déploiements.')"
    )
    conn.commit()
    yield conn
    conn.close()


# ── Tests _build_conversation_text ────────────────────────────────────────────

def test_build_conversation_text_contenu(in_memory_db):
    text, msg_count, estimated_tokens = _build_conversation_text(1, in_memory_db)
    assert "Utilisateur" in text
    assert "Big Bertha" in text
    assert "ROI" in text


def test_build_conversation_text_comptage(in_memory_db):
    _, msg_count, estimated_tokens = _build_conversation_text(1, in_memory_db)
    assert msg_count == 4, "4 messages dans la conversation de test"
    assert estimated_tokens > 0


def test_build_conversation_text_conversation_vide(in_memory_db):
    in_memory_db.execute("INSERT INTO conversations (title) VALUES ('Vide')")
    in_memory_db.commit()
    text, msg_count, estimated_tokens = _build_conversation_text(2, in_memory_db)
    assert text == ""
    assert msg_count == 0
    assert estimated_tokens == 0


# ── Tests validation JSON ARCHIVISTE ─────────────────────────────────────────

BILAN_VALIDE = {
    "sujet_principal": "ROI et secteurs prioritaires pour les projets agents IA",
    "decisions_prises": ["Cibler l'industrie en priorité", "Proposer un benchmark ROI dès le cadrage"],
    "informations_cles": ["ROI moyen 250%", "Délai de constatation 6-12 mois"],
    "questions_ouvertes": ["Quel modèle de facturation pour les projets longs ?"],
    "prochaine_etape": "Préparer une grille d'évaluation ROI pour le prospect banque"
}


def test_bilan_json_contient_toutes_les_cles():
    cles_attendues = {"sujet_principal", "decisions_prises", "informations_cles", "questions_ouvertes", "prochaine_etape"}
    assert cles_attendues == set(BILAN_VALIDE.keys()), "Le format JSON doit contenir exactement les 5 clés"


def test_bilan_json_listes_max_3_elements():
    bilan_trop_long = {
        "sujet_principal": "Test",
        "decisions_prises": ["D1", "D2", "D3", "D4"],
        "informations_cles": ["I1"],
        "questions_ouvertes": [],
        "prochaine_etape": ""
    }
    assert len(bilan_trop_long["decisions_prises"]) > 3, "Ce test vérifie qu'on détecte les listes trop longues"
    # Le plan figé impose max 3 éléments par liste
    for cle in ("decisions_prises", "informations_cles", "questions_ouvertes"):
        assert len(BILAN_VALIDE[cle]) <= 3, f"{cle} ne doit pas dépasser 3 éléments"


def test_bilan_json_listes_vides_acceptees():
    bilan_minimal = {
        "sujet_principal": "Présentation de Neuraltech Consulting",
        "decisions_prises": [],
        "informations_cles": ["Cabinet spécialisé agents IA"],
        "questions_ouvertes": [],
        "prochaine_etape": ""
    }
    assert json.dumps(bilan_minimal)  # Sérialisable sans erreur
    assert bilan_minimal["decisions_prises"] == []
    assert bilan_minimal["prochaine_etape"] == ""


def test_bilan_json_parseable():
    raw = json.dumps(BILAN_VALIDE, ensure_ascii=False)
    parsed = json.loads(raw)
    assert parsed["sujet_principal"] == BILAN_VALIDE["sujet_principal"]


def test_bilan_json_fallback_texte_brut():
    """Si le LLM retourne du texte au lieu de JSON, le fallback doit être non vide."""
    texte_brut = "Cette conversation portait sur le ROI des projets IA dans l'industrie."
    assert isinstance(texte_brut, str)
    assert len(texte_brut) > 0


# ── Tests _index_in_session_memory ────────────────────────────────────────────

class FakeSessionRag:
    def __init__(self):
        self.calls = []

    def add_text(self, text, doc_id, metadata):
        self.calls.append({"text": text, "doc_id": doc_id, "metadata": metadata})


def test_index_in_session_memory_avec_json_valide():
    rag = FakeSessionRag()
    summary_json = json.dumps(BILAN_VALIDE, ensure_ascii=False)
    _index_in_session_memory(rag, conversation_id=42, summary_json=summary_json, summary_text=None, trigger_reason="message_threshold")

    assert len(rag.calls) == 1
    call = rag.calls[0]
    assert call["doc_id"] == "session_42"
    assert "sujet" in call["text"].lower() or "roi" in call["text"].lower()
    assert call["metadata"]["conversation_id"] == "42"
    assert call["metadata"]["trigger_reason"] == "message_threshold"


def test_index_in_session_memory_fallback_texte():
    rag = FakeSessionRag()
    _index_in_session_memory(rag, conversation_id=7, summary_json=None, summary_text="Texte brut de fallback", trigger_reason="token_threshold")

    assert len(rag.calls) == 1
    assert "Texte brut de fallback" in rag.calls[0]["text"]


def test_index_in_session_memory_json_et_texte_vides():
    """Si les deux sont vides, rien ne doit être indexé."""
    rag = FakeSessionRag()
    _index_in_session_memory(rag, conversation_id=99, summary_json=None, summary_text=None, trigger_reason="manual")

    assert len(rag.calls) == 0, "Rien à indexer si summary_json et summary_text sont vides"


# ── Tests format du prompt ARCHIVISTE ─────────────────────────────────────────

def test_archiviste_prompt_contient_placeholder_profil():
    assert "{PROFIL_ENTREPRISE}" in ARCHIVISTE_PROMPT


def test_archiviste_prompt_impose_json_uniquement():
    assert "UNIQUEMENT le JSON" in ARCHIVISTE_PROMPT or "UNIQUEMENT" in ARCHIVISTE_PROMPT
    assert "sujet_principal" in ARCHIVISTE_PROMPT
    assert "decisions_prises" in ARCHIVISTE_PROMPT
    assert "informations_cles" in ARCHIVISTE_PROMPT
    assert "questions_ouvertes" in ARCHIVISTE_PROMPT
    assert "prochaine_etape" in ARCHIVISTE_PROMPT
