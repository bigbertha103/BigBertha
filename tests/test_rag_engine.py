import shutil
import tempfile
from pathlib import Path

import pytest

from backend.services.rag_engine import RAGManager


@pytest.fixture(scope="module")
def rag_env():
    tmp_dir = tempfile.mkdtemp(prefix="bigbertha_rag_test_")
    txt_file = Path(tmp_dir) / "sample.txt"
    txt_file.write_text(
        "Neuraltech Consulting est un cabinet spécialisé en intelligence artificielle.\n\n"
        "Nos experts accompagnent les entreprises dans leurs projets RAG, LLM et agents IA.\n\n"
        "Nous distinguons toujours ce qui est production-ready de ce qui est expérimental.\n\n"
        "Chaque mission se structure en quatre étapes : contexte, analyse, recommandations, prochaines étapes.",
        encoding="utf-8",
    )
    manager = RAGManager(
        collection_name="test_collection",
        persist_dir=str(Path(tmp_dir) / "chroma"),
        embedding_model="all-MiniLM-L6-v2",
    )
    yield manager, txt_file, tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_add_document(rag_env):
    manager, txt_file, _ = rag_env
    ids = manager.add_document(txt_file)
    assert len(ids) > 0, "add_document doit retourner au moins un chunk_id"


def test_collection_count(rag_env):
    manager, _, _ = rag_env
    info = manager.get_collection_info()
    assert info["count"] > 0, "La collection doit contenir au moins un document après add_document"


def test_search_returns_results(rag_env):
    manager, _, _ = rag_env
    results = manager.search("intelligence artificielle", top_k=3)
    assert len(results) > 0, "search() doit retourner au moins un résultat"
    first = results[0]
    assert "document" in first
    assert "metadata" in first
    assert "distance" in first


def test_get_context_for_query(rag_env):
    manager, _, _ = rag_env
    context = manager.get_context_for_query("agents IA et RAG")
    assert context != "", "get_context_for_query() ne doit pas retourner une chaîne vide"
    assert "[Source :" in context, "Le contexte doit contenir la balise [Source :]"


def test_search_empty_collection():
    tmp_dir = tempfile.mkdtemp(prefix="bigbertha_empty_test_")
    try:
        manager = RAGManager(
            collection_name="empty_collection",
            persist_dir=str(Path(tmp_dir) / "chroma"),
            embedding_model="all-MiniLM-L6-v2",
        )
        results = manager.search("quelque chose", top_k=3)
        assert results == [], "search() sur collection vide doit retourner []"
        context = manager.get_context_for_query("quelque chose")
        assert context == "", "get_context_for_query() sur collection vide doit retourner ''"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
