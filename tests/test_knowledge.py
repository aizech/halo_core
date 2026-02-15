"""Tests for Agno Knowledge abstraction (Task 7)."""

from __future__ import annotations

import types

from services import knowledge, storage, halo_team


def test_get_agent_knowledge_returns_none_without_api_key(monkeypatch):
    """Without OpenAI API key, get_agent_knowledge() returns None."""
    monkeypatch.setattr(knowledge, "_KNOWLEDGE_INITIALIZED", False)
    monkeypatch.setattr(knowledge, "_KNOWLEDGE", None)
    monkeypatch.setattr(knowledge._SETTINGS, "openai_api_key", None)

    result = knowledge.get_agent_knowledge()
    assert result is None


def test_get_agent_knowledge_returns_knowledge_with_api_key(monkeypatch, tmp_path):
    """With OpenAI API key, get_agent_knowledge() returns a Knowledge instance."""
    monkeypatch.setattr(knowledge, "_KNOWLEDGE_INITIALIZED", False)
    monkeypatch.setattr(knowledge, "_KNOWLEDGE", None)
    monkeypatch.setattr(knowledge._SETTINGS, "openai_api_key", "test-key")
    monkeypatch.setattr(knowledge._SETTINGS, "data_dir", str(tmp_path))

    result = knowledge.get_agent_knowledge()
    assert result is not None
    from agno.knowledge.knowledge import Knowledge

    assert isinstance(result, Knowledge)


def test_get_agent_knowledge_is_cached(monkeypatch, tmp_path):
    """Subsequent calls return the same cached instance."""
    monkeypatch.setattr(knowledge, "_KNOWLEDGE_INITIALIZED", False)
    monkeypatch.setattr(knowledge, "_KNOWLEDGE", None)
    monkeypatch.setattr(knowledge._SETTINGS, "openai_api_key", "test-key")
    monkeypatch.setattr(knowledge._SETTINGS, "data_dir", str(tmp_path))

    k1 = knowledge.get_agent_knowledge()
    k2 = knowledge.get_agent_knowledge()
    assert k1 is k2


def test_knowledge_uses_correct_lancedb_path(monkeypatch, tmp_path):
    """Knowledge uses data_dir/lancedb as the vector DB URI."""
    monkeypatch.setattr(knowledge, "_KNOWLEDGE_INITIALIZED", False)
    monkeypatch.setattr(knowledge, "_KNOWLEDGE", None)
    monkeypatch.setattr(knowledge._SETTINGS, "openai_api_key", "test-key")
    monkeypatch.setattr(knowledge._SETTINGS, "data_dir", str(tmp_path))

    result = knowledge.get_agent_knowledge()
    assert result is not None
    vector_db = getattr(result, "vector_db", None)
    assert vector_db is not None
    uri = getattr(vector_db, "uri", None)
    assert uri is not None
    assert "lancedb" in str(uri)


def test_get_agent_knowledge_falls_back_to_vector_when_hybrid_fails(
    monkeypatch, tmp_path
):
    """Hybrid LanceDB init failure falls back to vector search instead of disabling knowledge."""
    monkeypatch.setattr(knowledge, "_KNOWLEDGE_INITIALIZED", False)
    monkeypatch.setattr(knowledge, "_KNOWLEDGE", None)
    monkeypatch.setattr(knowledge._SETTINGS, "openai_api_key", "test-key")
    monkeypatch.setattr(knowledge._SETTINGS, "data_dir", str(tmp_path))
    monkeypatch.setattr(knowledge, "os", types.SimpleNamespace(name="posix"))

    from agno.knowledge import knowledge as agno_knowledge_module
    from agno.vectordb import lancedb as lancedb_module
    from agno.vectordb.lancedb import SearchType

    attempted_search_types = []

    class DummyKnowledge:
        def __init__(self, name: str, description: str, vector_db) -> None:
            self.name = name
            self.description = description
            self.vector_db = vector_db

    monkeypatch.setattr(agno_knowledge_module, "Knowledge", DummyKnowledge)

    class DummyVectorDb:
        def __init__(self, uri: str, table_name: str, search_type, embedder) -> None:
            self.uri = uri
            self.table_name = table_name
            self.search_type = search_type

    def fake_lancedb(*, uri: str, table_name: str, search_type, embedder):
        attempted_search_types.append(search_type)
        if search_type == SearchType.hybrid:
            raise RuntimeError("hybrid unavailable")
        return DummyVectorDb(
            uri=uri,
            table_name=table_name,
            search_type=search_type,
            embedder=embedder,
        )

    monkeypatch.setattr(lancedb_module, "LanceDb", fake_lancedb)

    result = knowledge.get_agent_knowledge()
    assert result is not None
    assert attempted_search_types[0] == SearchType.hybrid
    assert attempted_search_types[1] == getattr(SearchType, "vector", SearchType.hybrid)
    vector_db = getattr(result, "vector_db", None)
    assert getattr(vector_db, "search_type", None) == attempted_search_types[1]


def test_team_gets_knowledge_when_available(monkeypatch, tmp_path):
    """Team receives knowledge= when API key is set."""
    monkeypatch.setattr(knowledge, "_KNOWLEDGE_INITIALIZED", False)
    monkeypatch.setattr(knowledge, "_KNOWLEDGE", None)
    monkeypatch.setattr(knowledge._SETTINGS, "openai_api_key", "test-key")
    monkeypatch.setattr(knowledge._SETTINGS, "data_dir", str(tmp_path))
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", None)
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": [],
        "instructions": "Test.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config)
    assert team is not None
    assert getattr(team, "knowledge", None) is not None
    assert getattr(team, "search_knowledge", False) is True


def test_team_no_knowledge_without_api_key(monkeypatch):
    """Team has no knowledge= when API key is not set."""
    monkeypatch.setattr(knowledge, "_KNOWLEDGE_INITIALIZED", False)
    monkeypatch.setattr(knowledge, "_KNOWLEDGE", None)
    # Patch the shared Settings object used by knowledge.py to have no API key
    # for knowledge init, but halo_team still needs one for model creation.
    # Use a fake get_agent_knowledge that always returns None.
    monkeypatch.setattr(halo_team, "get_agent_knowledge", lambda: None)
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", None)
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": [],
        "instructions": "Test.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config)
    assert team is not None
    assert getattr(team, "knowledge", None) is None
    assert getattr(team, "search_knowledge", True) is False
