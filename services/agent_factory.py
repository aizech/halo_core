"""Shared factories for Agno models and tools."""

from __future__ import annotations

import logging
from typing import Dict, List

from agno.models.openai import OpenAIChat
from agno.tools.pubmed import PubmedTools
from agno.tools.websearch import WebSearchTools
from agno.tools.youtube import YouTubeTools
from agno.tools.wikipedia import WikipediaTools

try:  # Optional MCP tool kit
    from agno.tools.mcp import MCPTools
except ImportError:  # pragma: no cover - optional dependency
    MCPTools = None

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
        if tool_id == "shell":
            logger.warning("Shell tool is disabled by default")
            continue
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
                websearch_kwargs = {
                    "backend": websearch_settings.get("backend"),
                    "num_results": websearch_settings.get("num_results"),
                }
                try:
                    tools.append(WebSearchTools(**websearch_kwargs))
                except TypeError:
                    logger.warning(
                        "WebSearch tool does not support configured settings; using defaults"
                    )
                    tools.append(WebSearchTools())
            else:
                tools.append(WebSearchTools())
        if tool_id in {"youtube", "youtube_transcript"}:
            settings_key = (
                "youtube_transcript" if tool_id == "youtube_transcript" else "youtube"
            )
            youtube_settings = tool_settings.get(settings_key)
            default_youtube_flags = {
                "enable_get_video_captions": True,
                "enable_get_video_data": tool_id != "youtube_transcript",
                "enable_get_video_timestamps": tool_id == "youtube_transcript",
            }
            default_languages = ["en", "de"] if tool_id == "youtube_transcript" else []
            if isinstance(youtube_settings, dict):
                fetch_captions = bool(youtube_settings.get("fetch_captions", True))
                fetch_video_info = bool(
                    youtube_settings.get(
                        "fetch_video_info",
                        default_youtube_flags["enable_get_video_data"],
                    )
                )
                fetch_timestamps = bool(
                    youtube_settings.get(
                        "fetch_timestamps",
                        default_youtube_flags["enable_get_video_timestamps"],
                    )
                )
                languages_raw = youtube_settings.get("languages")
                languages = (
                    [
                        str(language).strip()
                        for language in languages_raw
                        if str(language).strip()
                    ]
                    if isinstance(languages_raw, list)
                    else []
                )
                youtube_kwargs = {
                    "enable_get_video_captions": bool(
                        youtube_settings.get(
                            "enable_get_video_captions",
                            fetch_captions,
                        )
                    ),
                    "enable_get_video_data": bool(
                        youtube_settings.get(
                            "enable_get_video_data",
                            fetch_video_info,
                        )
                    ),
                    "enable_get_video_timestamps": bool(
                        youtube_settings.get(
                            "enable_get_video_timestamps",
                            fetch_timestamps,
                        )
                    ),
                }
                if languages:
                    youtube_kwargs["languages"] = languages
                elif default_languages:
                    youtube_kwargs["languages"] = default_languages
                try:
                    tools.append(YouTubeTools(**youtube_kwargs))
                except TypeError:
                    logger.warning(
                        "YouTube tool does not support configured settings; using defaults"
                    )
                    try:
                        fallback_kwargs = {**default_youtube_flags}
                        if default_languages:
                            fallback_kwargs["languages"] = default_languages
                        tools.append(YouTubeTools(**fallback_kwargs))
                    except TypeError:
                        logger.warning(
                            "YouTube tool does not support fetch_* options in this Agno version; using no-arg init"
                        )
                        tools.append(YouTubeTools())
            else:
                try:
                    default_kwargs = {**default_youtube_flags}
                    if default_languages:
                        default_kwargs["languages"] = default_languages
                    tools.append(YouTubeTools(**default_kwargs))
                except TypeError:
                    logger.warning(
                        "YouTube tool does not support fetch_* options in this Agno version; using no-arg init"
                    )
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
                arxiv_settings = tool_settings.get("arxiv")
                if isinstance(arxiv_settings, dict):
                    arxiv_kwargs = {
                        "max_results": int(arxiv_settings.get("max_results") or 5),
                        "sort_by": arxiv_settings.get("sort_by") or None,
                    }
                    try:
                        tools.append(ArxivTools(**arxiv_kwargs))
                    except TypeError:
                        logger.warning(
                            "Arxiv tool does not support configured settings; using defaults"
                        )
                        tools.append(ArxivTools())
                else:
                    tools.append(ArxivTools())
        if tool_id == "website":
            if WebsiteTools is None:
                logger.warning("Website tool not available")
            else:
                website_settings = tool_settings.get("website")
                if isinstance(website_settings, dict):
                    allowed_domains_raw = website_settings.get("allowed_domains", [])
                    allowed_domains = (
                        [
                            str(domain).strip()
                            for domain in allowed_domains_raw
                            if str(domain).strip()
                        ]
                        if isinstance(allowed_domains_raw, list)
                        else []
                    )
                    website_kwargs = {
                        "max_pages": max(
                            1,
                            min(20, int(website_settings.get("max_pages") or 5)),
                        ),
                        "timeout": max(
                            1,
                            min(120, int(website_settings.get("timeout") or 10)),
                        ),
                        "allowed_domains": allowed_domains,
                    }
                    try:
                        tools.append(WebsiteTools(**website_kwargs))
                    except TypeError:
                        logger.warning(
                            "Website tool does not support configured settings; using defaults"
                        )
                        tools.append(WebsiteTools())
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


def build_mcp_tools(
    mcp_servers: object,
    *,
    logger: logging.Logger,
) -> List[object]:
    tools: List[object] = []
    if MCPTools is None:
        return tools
    if not isinstance(mcp_servers, list):
        return tools

    for item in mcp_servers:
        if not isinstance(item, dict):
            continue
        server_name = str(item.get("name") or "mcp-server").strip() or "mcp-server"
        if item.get("enabled", True) is False:
            logger.info("MCP server '%s' is disabled; skipping", server_name)
            continue

        transport_raw = str(item.get("transport") or "streamable-http").strip().lower()
        transport = (
            "streamable-http"
            if transport_raw in {"", "http", "streamable-http"}
            else transport_raw
        )
        if transport not in {"streamable-http", "sse", "stdio"}:
            logger.warning(
                "MCP server '%s' skipped: unsupported transport: %s",
                server_name,
                transport,
            )
            continue

        url = str(item.get("url") or "").strip()
        command = str(item.get("command") or "").strip()
        if transport in {"streamable-http", "sse"} and not url:
            logger.warning("MCP server '%s' skipped: missing url", server_name)
            continue
        if transport == "stdio" and not command:
            logger.warning("MCP server '%s' skipped: missing command", server_name)
            continue

        allowed_tools_raw = item.get("allowed_tools", [])
        allowed_tools = (
            [
                str(tool_name).strip()
                for tool_name in allowed_tools_raw
                if str(tool_name).strip()
            ]
            if isinstance(allowed_tools_raw, list)
            else []
        )

        kwargs = {"transport": transport}
        if transport in {"streamable-http", "sse"}:
            kwargs["url"] = url
        if transport == "stdio":
            kwargs["command"] = command
        if allowed_tools:
            kwargs["tools"] = allowed_tools

        try:
            tools.append(MCPTools(**kwargs))
            logger.info(
                "MCP server '%s' attached (transport=%s)",
                server_name,
                transport,
            )
        except TypeError:
            logger.warning("MCPTools signature mismatch; retrying without tool filter")
            try:
                if transport in {"streamable-http", "sse"}:
                    tools.append(MCPTools(transport=transport, url=url))
                else:
                    tools.append(MCPTools(command=command))
                logger.info(
                    "MCP server '%s' attached without tool filter (transport=%s)",
                    server_name,
                    transport,
                )
            except Exception:
                logger.exception(
                    "Failed to build MCPTools for server '%s'", server_name
                )
        except Exception:
            logger.exception("Failed to build MCPTools for server '%s'", server_name)

    return tools
