"""Shared factories for Agno models and tools."""

from __future__ import annotations

import logging
from typing import Dict, List

from agno.models.openai import OpenAIChat
from agno.tools.pubmed import PubmedTools
from agno.tools.wikipedia import WikipediaTools

try:  # Optional Mermaid tool
    from agno.tools.mermaid import MermaidTools
except ImportError:  # pragma: no cover - optional dependency
    MermaidTools = None

try:  # Optional model providers
    from agno.models.google import Gemini
except ImportError:  # pragma: no cover - optional dependency
    Gemini = None

try:  # Optional model providers
    from agno.models.anthropic import Claude
except ImportError:  # pragma: no cover - optional dependency
    Claude = None

try:  # Optional model providers
    from agno.models.groq import Groq
except ImportError:  # pragma: no cover - optional dependency
    Groq = None


def normalize_model_id(raw: object, default_model_id: str = "openai:gpt-5.2") -> str:
    if not raw:
        return default_model_id
    model_id = str(raw)
    if ":" in model_id:
        return model_id
    return f"openai:{model_id}"


def build_model(model_id: str, *, openai_api_key: str | None, logger: logging.Logger):
    provider, name = model_id.split(":", 1)
    if provider == "openai":
        if not openai_api_key:
            logger.warning("Model not built: missing OpenAI API key")
            return None
        return OpenAIChat(id=name, api_key=openai_api_key)
    if provider == "google":
        if Gemini is None:
            logger.warning("Gemini model not available")
            return None
        return Gemini(id=name)
    if provider == "anthropic":
        if Claude is None:
            logger.warning("Claude model not available")
            return None
        return Claude(id=name)
    if provider == "groq":
        if Groq is None:
            logger.warning("Groq model not available")
            return None
        return Groq(id=name)
    logger.warning("Unsupported model provider: %s", provider)
    return None


def build_tools(
    tool_ids: object,
    tool_settings: Dict[str, object] | None = None,
    *,
    logger: logging.Logger,
) -> List[object]:
    tools: List[object] = []
    if not isinstance(tool_ids, list):
        return tools
    tool_settings = tool_settings or {}
    for tool_id in tool_ids:
        if tool_id == "pubmed":
            pubmed_settings = tool_settings.get("pubmed")
            if isinstance(pubmed_settings, dict):
                tools.append(
                    PubmedTools(
                        email=pubmed_settings.get("email"),
                        max_results=pubmed_settings.get("max_results"),
                        enable_search_pubmed=pubmed_settings.get(
                            "enable_search_pubmed", True
                        ),
                        all=pubmed_settings.get("all", False),
                    )
                )
            else:
                tools.append(PubmedTools())
        if tool_id == "wikipedia":
            tools.append(WikipediaTools())
        if tool_id == "mermaid":
            if MermaidTools is None:
                logger.warning("Mermaid tool not available")
            else:
                tools.append(MermaidTools())
    return tools
