"""Shared factories for Agno models and tools."""

from __future__ import annotations

import logging
from typing import Dict, List

from agno.models.openai import OpenAIChat
from agno.tools.pubmed import PubmedTools
from agno.tools.websearch import WebSearchTools
from agno.tools.youtube import YouTubeTools
from agno.tools.wikipedia import WikipediaTools

try:  # Optional tool kit
    from agno.tools.arxiv import ArxivTools
except ImportError:  # pragma: no cover - optional dependency
    ArxivTools = None

try:  # Optional tool kit
    from agno.tools.duckduckgo import DuckDuckGoTools
except ImportError:  # pragma: no cover - optional dependency
    DuckDuckGoTools = None

try:  # Optional tool kit
    from agno.tools.website import WebsiteTools
except ImportError:  # pragma: no cover - optional dependency
    WebsiteTools = None

try:  # Optional tool kit
    from agno.tools.hackernews import HackerNewsTools
except ImportError:  # pragma: no cover - optional dependency
    HackerNewsTools = None

try:  # Optional tool kit
    from agno.tools.yfinance import YFinanceTools
except ImportError:  # pragma: no cover - optional dependency
    YFinanceTools = None

try:  # Optional tool kit
    from agno.tools.calculator import CalculatorTools
except ImportError:  # pragma: no cover - optional dependency
    CalculatorTools = None

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
        if tool_id == "websearch":
            websearch_settings = tool_settings.get("websearch")
            if isinstance(websearch_settings, dict):
                tools.append(
                    WebSearchTools(
                        backend=websearch_settings.get("backend"),
                        num_results=websearch_settings.get("num_results"),
                    )
                )
            else:
                tools.append(WebSearchTools())
        if tool_id == "youtube":
            youtube_settings = tool_settings.get("youtube")
            if isinstance(youtube_settings, dict):
                tools.append(
                    YouTubeTools(
                        fetch_captions=youtube_settings.get("fetch_captions", True),
                        fetch_video_info=youtube_settings.get("fetch_video_info", True),
                        fetch_timestamps=youtube_settings.get(
                            "fetch_timestamps", False
                        ),
                    )
                )
            else:
                tools.append(YouTubeTools())
        if tool_id == "duckduckgo":
            if DuckDuckGoTools is None:
                logger.warning("DuckDuckGo tool not available")
            else:
                duckduckgo_settings = tool_settings.get("duckduckgo")
                if isinstance(duckduckgo_settings, dict):
                    tools.append(
                        DuckDuckGoTools(
                            enable_search=duckduckgo_settings.get(
                                "enable_search", True
                            ),
                            enable_news=duckduckgo_settings.get("enable_news", True),
                            fixed_max_results=duckduckgo_settings.get(
                                "fixed_max_results"
                            ),
                            timeout=duckduckgo_settings.get("timeout", 10),
                            verify_ssl=duckduckgo_settings.get("verify_ssl", True),
                        )
                    )
                else:
                    tools.append(DuckDuckGoTools())
        if tool_id == "arxiv":
            if ArxivTools is None:
                logger.warning("Arxiv tool not available")
            else:
                tools.append(ArxivTools())
        if tool_id == "website":
            if WebsiteTools is None:
                logger.warning("Website tool not available")
            else:
                tools.append(WebsiteTools())
        if tool_id == "hackernews":
            if HackerNewsTools is None:
                logger.warning("HackerNews tool not available")
            else:
                hackernews_settings = tool_settings.get("hackernews")
                if isinstance(hackernews_settings, dict):
                    tools.append(
                        HackerNewsTools(
                            enable_get_top_stories=hackernews_settings.get(
                                "enable_get_top_stories", True
                            ),
                            enable_get_user_details=hackernews_settings.get(
                                "enable_get_user_details", True
                            ),
                            all=hackernews_settings.get("all", False),
                        )
                    )
                else:
                    tools.append(HackerNewsTools())
        if tool_id == "yfinance":
            if YFinanceTools is None:
                logger.warning("YFinance tool not available")
            else:
                yfinance_settings = tool_settings.get("yfinance")
                if isinstance(yfinance_settings, dict):
                    tools.append(
                        YFinanceTools(
                            stock_price=yfinance_settings.get("stock_price", True),
                            analyst_recommendations=yfinance_settings.get(
                                "analyst_recommendations", True
                            ),
                        )
                    )
                else:
                    tools.append(YFinanceTools())
        if tool_id == "calculator":
            if CalculatorTools is None:
                logger.warning("Calculator tool not available")
            else:
                tools.append(CalculatorTools())
        if tool_id == "wikipedia":
            tools.append(WikipediaTools())
        if tool_id == "mermaid":
            if MermaidTools is None:
                logger.warning("Mermaid tool not available")
            else:
                tools.append(MermaidTools())
    return tools
