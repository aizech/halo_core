"""Agno Knowledge abstraction wrapping the existing LanceDB store.

When the OpenAI API key is available, returns a ``Knowledge`` instance backed
by the same LanceDB directory and table used by ``retrieval.py``.  Agents and
teams can then use ``knowledge=`` and ``search_knowledge=True`` natively.

Falls back to ``None`` when dependencies are missing or the API key is not set,
so callers can keep using the manual ``retrieval.query_similar`` path.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from services.settings import get_settings

_logger = logging.getLogger(__name__)
_SETTINGS = get_settings()

_KNOWLEDGE: Optional[object] = None
_KNOWLEDGE_INITIALIZED = False


def get_agent_knowledge() -> object | None:
    """Return a shared Agno ``Knowledge`` instance or ``None``.

    The instance reuses the same LanceDB directory (``data/lancedb``) and table
    (``sources``) that ``retrieval.py`` already populates, so no data migration
    is needed.
    """
    global _KNOWLEDGE, _KNOWLEDGE_INITIALIZED
    if _KNOWLEDGE_INITIALIZED:
        return _KNOWLEDGE
    _KNOWLEDGE_INITIALIZED = True

    api_key = _SETTINGS.openai_api_key
    if not api_key:
        _logger.info(
            "No OpenAI API key; Agno Knowledge disabled (using manual RAG fallback)."
        )
        return None

    try:
        from agno.knowledge.knowledge import Knowledge
        from agno.vectordb.lancedb import LanceDb, SearchType
        from agno.knowledge.embedder.openai import OpenAIEmbedder

        db_uri = str(Path(_SETTINGS.data_dir) / "lancedb")
        Path(db_uri).mkdir(parents=True, exist_ok=True)

        search_type = SearchType.hybrid
        if os.name == "nt":
            # Hybrid search uses LanceDB FTS indices. On Windows (especially
            # synced folders like OneDrive), index directory mutations can fail
            # with WinError 5 (access denied). Prefer pure vector search there.
            search_type = getattr(SearchType, "vector", SearchType.hybrid)

        vector_db = LanceDb(
            uri=db_uri,
            table_name="sources",
            search_type=search_type,
            embedder=OpenAIEmbedder(id="text-embedding-3-small", api_key=api_key),
        )

        _KNOWLEDGE = Knowledge(
            name="halo_sources",
            description="Indexed source documents for grounded chat and studio outputs.",
            vector_db=vector_db,
        )
        _logger.info(
            "Agno Knowledge initialized (LanceDB at %s, table=sources).", db_uri
        )
    except Exception as exc:
        _logger.warning("Failed to initialize Agno Knowledge: %s", exc)
        _KNOWLEDGE = None

    return _KNOWLEDGE
