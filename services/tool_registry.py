"""Tool registry pattern for extensible tool building.

Instead of a monolithic if-chain, tools are registered as builder callables.
New tools can be added by extending TOOL_METADATA and TOOL_BUILDERS.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

_LOGGER = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """Metadata for a registered tool."""

    id: str
    display_name: str
    description: str = ""
    category: str = "general"
    requires_settings: bool = False
    settings_schema: Dict[str, Any] = field(default_factory=dict)


# Tool metadata for UI display and validation
TOOL_METADATA: Dict[str, ToolMetadata] = {
    "pubmed": ToolMetadata(
        id="pubmed",
        display_name="PubMed Search",
        description="Search medical literature in PubMed database",
        category="research",
        requires_settings=True,
        settings_schema={
            "email": {"type": "string", "label": "Email (optional)"},
            "max_results": {"type": "integer", "label": "Max Results", "default": 10},
            "enable_search_pubmed": {
                "type": "boolean",
                "label": "Enable Search",
                "default": True,
            },
        },
    ),
    "duckduckgo": ToolMetadata(
        id="duckduckgo",
        display_name="DuckDuckGo Search",
        description="Web search without API key requirement",
        category="search",
        requires_settings=True,
        settings_schema={
            "enable_search": {
                "type": "boolean",
                "label": "Enable Search",
                "default": True,
            },
            "enable_news": {"type": "boolean", "label": "Enable News", "default": True},
            "fixed_max_results": {"type": "integer", "label": "Max Results"},
            "timeout": {"type": "integer", "label": "Timeout (seconds)", "default": 10},
        },
    ),
    "arxiv": ToolMetadata(
        id="arxiv",
        display_name="arXiv Papers",
        description="Search academic papers on arXiv",
        category="research",
        requires_settings=True,
        settings_schema={
            "max_results": {"type": "integer", "label": "Max Results", "default": 5},
        },
    ),
    "website": ToolMetadata(
        id="website",
        display_name="Website Crawler",
        description="Crawl and extract content from websites",
        category="search",
        requires_settings=True,
        settings_schema={
            "max_pages": {"type": "integer", "label": "Max Pages", "default": 5},
            "timeout": {"type": "integer", "label": "Timeout (seconds)", "default": 10},
        },
    ),
    "youtube": ToolMetadata(
        id="youtube",
        display_name="YouTube",
        description="Fetch YouTube video data and captions",
        category="media",
        requires_settings=True,
        settings_schema={
            "fetch_captions": {
                "type": "boolean",
                "label": "Fetch Captions",
                "default": True,
            },
            "fetch_video_info": {
                "type": "boolean",
                "label": "Fetch Video Info",
                "default": True,
            },
        },
    ),
    "youtube_transcript": ToolMetadata(
        id="youtube_transcript",
        display_name="YouTube Transcript",
        description="Extract transcripts from YouTube videos",
        category="media",
        requires_settings=True,
        settings_schema={
            "languages": {
                "type": "list",
                "label": "Languages",
                "default": ["en", "de"],
            },
        },
    ),
    "wikipedia": ToolMetadata(
        id="wikipedia",
        display_name="Wikipedia Search",
        description="Search Wikipedia articles",
        category="reference",
        requires_settings=False,
    ),
    "hackernews": ToolMetadata(
        id="hackernews",
        display_name="Hacker News",
        description="Fetch stories from Hacker News",
        category="news",
        requires_settings=True,
        settings_schema={
            "enable_get_top_stories": {
                "type": "boolean",
                "label": "Top Stories",
                "default": True,
            },
        },
    ),
    "yfinance": ToolMetadata(
        id="yfinance",
        display_name="Yahoo Finance",
        description="Stock prices and financial data",
        category="finance",
        requires_settings=True,
        settings_schema={
            "stock_price": {"type": "boolean", "label": "Stock Price", "default": True},
            "analyst_recommendations": {
                "type": "boolean",
                "label": "Analyst Recs",
                "default": True,
            },
        },
    ),
    "calculator": ToolMetadata(
        id="calculator",
        display_name="Calculator",
        description="Perform mathematical calculations",
        category="utility",
        requires_settings=False,
    ),
    "mermaid": ToolMetadata(
        id="mermaid",
        display_name="Mermaid Diagrams",
        description="Generate Mermaid diagram code",
        category="visualization",
        requires_settings=False,
    ),
    "image": ToolMetadata(
        id="image",
        display_name="Image Generation",
        description="Generate images using GPT-Image",
        category="creative",
        requires_settings=True,
        settings_schema={
            "image_model": {
                "type": "string",
                "label": "Image Model",
                "default": "gpt-image-1.5",
            },
        },
    ),
    "websearch": ToolMetadata(
        id="websearch",
        display_name="Web Search",
        description="General web search (multiple backends)",
        category="search",
        requires_settings=True,
        settings_schema={
            "backend": {"type": "string", "label": "Backend"},
            "num_results": {"type": "integer", "label": "Number of Results"},
        },
    ),
    "dalle": ToolMetadata(
        id="dalle",
        display_name="DALL-E Image",
        description="Generate images using OpenAI DALL-E",
        category="creative",
        requires_settings=False,
    ),
    "exa": ToolMetadata(
        id="exa",
        display_name="Exa Search",
        description="AI-powered web search with Exa",
        category="search",
        requires_settings=True,
        settings_schema={
            "start_published_date": {"type": "string", "label": "Start Date"},
            "type": {"type": "string", "label": "Search Type", "default": "keyword"},
        },
    ),
    "tavily": ToolMetadata(
        id="tavily",
        display_name="Tavily Search",
        description="Web search optimized for AI agents",
        category="search",
        requires_settings=True,
        settings_schema={
            "search_depth": {
                "type": "string",
                "label": "Search Depth",
                "default": "basic",
            },
            "max_results": {"type": "integer", "label": "Max Results", "default": 5},
        },
    ),
    "gemini_image": ToolMetadata(
        id="gemini_image",
        display_name="Gemini Imagen",
        description="Generate images using Google Gemini Imagen",
        category="creative",
        requires_settings=False,
    ),
    "replicate": ToolMetadata(
        id="replicate",
        display_name="Replicate",
        description="Generate images using Replicate models",
        category="creative",
        requires_settings=True,
        settings_schema={
            "model": {
                "type": "string",
                "label": "Model",
                "default": "luma/photon-flash",
            },
        },
    ),
}


def _build_pubmed(settings: Dict[str, Any] | None) -> object:
    """Build PubMed tool with settings."""
    from agno.tools.pubmed import PubmedTools

    if isinstance(settings, dict):
        return PubmedTools(
            email=settings.get("email"),
            max_results=settings.get("max_results"),
            enable_search_pubmed=settings.get("enable_search_pubmed", True),
            all=settings.get("all", False),
        )
    return PubmedTools()


def _build_duckduckgo(settings: Dict[str, Any] | None) -> object | None:
    """Build DuckDuckGo tool with settings."""
    try:
        from agno.tools.duckduckgo import DuckDuckGoTools
    except ImportError:
        _LOGGER.warning("DuckDuckGo tool not available")
        return None

    if isinstance(settings, dict):
        return DuckDuckGoTools(
            enable_search=settings.get("enable_search", True),
            enable_news=settings.get("enable_news", True),
            fixed_max_results=settings.get("fixed_max_results"),
            timeout=settings.get("timeout", 10),
            verify_ssl=settings.get("verify_ssl", True),
        )
    return DuckDuckGoTools()


def _build_arxiv(settings: Dict[str, Any] | None) -> object | None:
    """Build arXiv tool with settings."""
    try:
        from agno.tools.arxiv import ArxivTools
    except ImportError:
        _LOGGER.warning("Arxiv tool not available")
        return None

    if isinstance(settings, dict):
        arxiv_kwargs = {
            "max_results": int(settings.get("max_results") or 5),
        }
        if settings.get("sort_by"):
            arxiv_kwargs["sort_by"] = settings.get("sort_by")
        try:
            return ArxivTools(**arxiv_kwargs)
        except TypeError:
            _LOGGER.warning(
                "Arxiv tool does not support configured settings; using defaults"
            )
            return ArxivTools()
    return ArxivTools()


def _build_website(settings: Dict[str, Any] | None) -> object | None:
    """Build Website tool with settings."""
    try:
        from agno.tools.website import WebsiteTools
    except ImportError:
        _LOGGER.warning("Website tool not available")
        return None

    if isinstance(settings, dict):
        allowed_domains_raw = settings.get("allowed_domains", [])
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
            "max_pages": max(1, min(20, int(settings.get("max_pages") or 5))),
            "timeout": max(1, min(120, int(settings.get("timeout") or 10))),
            "allowed_domains": allowed_domains,
        }
        try:
            return WebsiteTools(**website_kwargs)
        except TypeError:
            _LOGGER.warning(
                "Website tool does not support configured settings; using defaults"
            )
            return WebsiteTools()
    return WebsiteTools()


def _build_youtube(
    settings: Dict[str, Any] | None, *, transcript_mode: bool = False
) -> object:
    """Build YouTube tool with settings."""
    from agno.tools.youtube import YouTubeTools

    default_flags = {
        "enable_get_video_captions": True,
        "enable_get_video_data": not transcript_mode,
        "enable_get_video_timestamps": transcript_mode,
    }
    default_languages = ["en", "de"] if transcript_mode else []

    if isinstance(settings, dict):
        fetch_captions = bool(settings.get("fetch_captions", True))
        fetch_video_info = bool(
            settings.get("fetch_video_info", default_flags["enable_get_video_data"])
        )
        fetch_timestamps = bool(
            settings.get(
                "fetch_timestamps", default_flags["enable_get_video_timestamps"]
            )
        )

        languages_raw = settings.get("languages")
        languages = (
            [str(lang).strip() for lang in languages_raw if str(lang).strip()]
            if isinstance(languages_raw, list)
            else []
        )

        youtube_kwargs = {
            "enable_get_video_captions": fetch_captions,
            "enable_get_video_data": fetch_video_info,
            "enable_get_video_timestamps": fetch_timestamps,
        }
        if languages:
            youtube_kwargs["languages"] = languages
        elif default_languages:
            youtube_kwargs["languages"] = default_languages

        try:
            return YouTubeTools(**youtube_kwargs)
        except TypeError:
            _LOGGER.warning(
                "YouTube tool does not support fetch_* options; using no-arg init"
            )
            return YouTubeTools()

    try:
        kwargs = {**default_flags}
        if default_languages:
            kwargs["languages"] = default_languages
        return YouTubeTools(**kwargs)
    except TypeError:
        return YouTubeTools()


def _build_wikipedia(settings: Dict[str, Any] | None) -> object:
    """Build Wikipedia tool."""
    from agno.tools.wikipedia import WikipediaTools

    return WikipediaTools()


def _build_hackernews(settings: Dict[str, Any] | None) -> object | None:
    """Build HackerNews tool with settings."""
    try:
        from agno.tools.hackernews import HackerNewsTools
    except ImportError:
        _LOGGER.warning("HackerNews tool not available")
        return None

    if isinstance(settings, dict):
        return HackerNewsTools(
            enable_get_top_stories=settings.get("enable_get_top_stories", True),
            enable_get_user_details=settings.get("enable_get_user_details", True),
            all=settings.get("all", False),
        )
    return HackerNewsTools()


def _build_yfinance(settings: Dict[str, Any] | None) -> object | None:
    """Build YFinance tool with settings."""
    try:
        from agno.tools.yfinance import YFinanceTools
    except ImportError:
        _LOGGER.warning("YFinance tool not available")
        return None

    if isinstance(settings, dict):
        return YFinanceTools(
            stock_price=settings.get("stock_price", True),
            analyst_recommendations=settings.get("analyst_recommendations", True),
        )
    return YFinanceTools()


def _build_calculator(settings: Dict[str, Any] | None) -> object | None:
    """Build Calculator tool."""
    try:
        from agno.tools.calculator import CalculatorTools
    except ImportError:
        _LOGGER.warning("Calculator tool not available")
        return None

    return CalculatorTools()


def _build_mermaid(settings: Dict[str, Any] | None) -> object | None:
    """Build Mermaid tool."""
    try:
        from agno.tools.mermaid import MermaidTools
    except ImportError:
        _LOGGER.warning("Mermaid tool not available")
        return None

    return MermaidTools()


def _build_image(
    settings: Dict[str, Any] | None, *, openai_api_key: str | None
) -> object | None:
    """Build Image generation tool with settings."""
    from agno.tools.openai import OpenAITools

    if not openai_api_key:
        _LOGGER.warning("Cannot add image tool: OpenAI API key not configured")
        return None

    image_model = "gpt-image-1.5"
    if isinstance(settings, dict):
        image_model = str(settings.get("image_model", "gpt-image-1.5"))

    tool = OpenAITools(image_model=image_model, api_key=openai_api_key)
    _LOGGER.info("Added image generation tool with model: %s", image_model)
    return tool


def _build_dalle(settings: Dict[str, Any] | None) -> object | None:
    """Build DALL-E image generation tool."""
    try:
        from agno.tools.dalle import DalleTools

        return DalleTools()
    except ImportError:
        _LOGGER.warning("DALL-E tool not available")
        return None


def _build_exa(settings: Dict[str, Any] | None) -> object | None:
    """Build Exa search tool with settings."""
    try:
        from agno.tools.exa import ExaTools
    except ImportError:
        _LOGGER.warning("Exa tool not available")
        return None

    if isinstance(settings, dict):
        kwargs = {}
        if settings.get("start_published_date"):
            kwargs["start_published_date"] = settings["start_published_date"]
        if settings.get("type"):
            kwargs["type"] = settings["type"]
        try:
            return ExaTools(**kwargs)
        except TypeError:
            return ExaTools()
    return ExaTools()


def _build_tavily(settings: Dict[str, Any] | None) -> object | None:
    """Build Tavily search tool with settings."""
    try:
        from agno.tools.tavily import TavilyTools
    except ImportError:
        _LOGGER.warning("Tavily tool not available")
        return None

    if isinstance(settings, dict):
        kwargs = {}
        if settings.get("search_depth"):
            kwargs["search_depth"] = settings["search_depth"]
        if settings.get("max_results"):
            kwargs["max_results"] = settings["max_results"]
        try:
            return TavilyTools(**kwargs)
        except TypeError:
            return TavilyTools()
    return TavilyTools()


def _build_gemini_image(settings: Dict[str, Any] | None) -> object | None:
    """Build Gemini image generation tool."""
    try:
        from agno.tools.models.gemini import GeminiTools

        return GeminiTools()
    except ImportError:
        _LOGGER.warning("Gemini image tool not available")
        return None


def _build_replicate(settings: Dict[str, Any] | None) -> object | None:
    """Build Replicate image generation tool."""
    try:
        from agno.tools.replicate import ReplicateTools
    except ImportError:
        _LOGGER.warning("Replicate tool not available")
        return None

    model = "luma/photon-flash"
    if isinstance(settings, dict) and settings.get("model"):
        model = settings["model"]
    try:
        return ReplicateTools(model=model, enable_generate_media=True)
    except TypeError:
        return ReplicateTools()


def _build_websearch(settings: Dict[str, Any] | None) -> object:
    """Build WebSearch tool with settings."""
    from agno.tools.websearch import WebSearchTools

    if isinstance(settings, dict):
        websearch_kwargs = {
            "backend": settings.get("backend"),
            "num_results": settings.get("num_results"),
        }
        try:
            return WebSearchTools(**websearch_kwargs)
        except TypeError:
            _LOGGER.warning(
                "WebSearch tool does not support configured settings; using defaults"
            )
            return WebSearchTools()
    return WebSearchTools()


# Registry mapping tool IDs to builder functions
# Builders receive (settings, openai_api_key) and return a tool instance or None
ToolBuilder = Callable[[Dict[str, Any] | None, str | None], object | None]

TOOL_BUILDERS: Dict[str, ToolBuilder] = {
    "pubmed": lambda s, _: _build_pubmed(s),
    "duckduckgo": lambda s, _: _build_duckduckgo(s),
    "arxiv": lambda s, _: _build_arxiv(s),
    "website": lambda s, _: _build_website(s),
    "youtube": lambda s, _: _build_youtube(s, transcript_mode=False),
    "youtube_transcript": lambda s, _: _build_youtube(s, transcript_mode=True),
    "wikipedia": lambda s, _: _build_wikipedia(s),
    "hackernews": lambda s, _: _build_hackernews(s),
    "yfinance": lambda s, _: _build_yfinance(s),
    "calculator": lambda s, _: _build_calculator(s),
    "mermaid": lambda s, _: _build_mermaid(s),
    "image": lambda s, key: _build_image(s, openai_api_key=key),
    "websearch": lambda s, _: _build_websearch(s),
    "dalle": lambda s, _: _build_dalle(s),
    "exa": lambda s, _: _build_exa(s),
    "tavily": lambda s, _: _build_tavily(s),
    "gemini_image": lambda s, _: _build_gemini_image(s),
    "replicate": lambda s, _: _build_replicate(s),
}


def register_tool(
    tool_id: str, builder: ToolBuilder, metadata: ToolMetadata | None = None
) -> None:
    """Register a new tool builder dynamically.

    Args:
        tool_id: Unique identifier for the tool
        builder: Callable that takes (settings, openai_api_key) and returns a tool instance
        metadata: Optional metadata for UI display
    """
    TOOL_BUILDERS[tool_id] = builder
    if metadata:
        TOOL_METADATA[tool_id] = metadata
    _LOGGER.info("Registered tool: %s", tool_id)


def build_tool(
    tool_id: str,
    settings: Dict[str, Any] | None,
    *,
    openai_api_key: str | None = None,
) -> object | None:
    """Build a single tool instance by ID.

    Args:
        tool_id: The registered tool identifier
        settings: Tool-specific settings dict
        openai_api_key: API key for tools that require it (e.g., image generation)

    Returns:
        Tool instance or None if tool not registered or build failed
    """
    builder = TOOL_BUILDERS.get(tool_id)
    if builder is None:
        _LOGGER.warning("Unknown tool ID: %s", tool_id)
        return None

    try:
        return builder(settings, openai_api_key)
    except Exception:
        _LOGGER.exception("Failed to build tool: %s", tool_id)
        return None


def build_tools_from_registry(
    tool_ids: List[str],
    tool_settings: Dict[str, Any] | None,
    *,
    openai_api_key: str | None = None,
    logger: logging.Logger | None = None,
) -> List[object]:
    """Build multiple tools from the registry.

    Args:
        tool_ids: List of tool IDs to build
        tool_settings: Dict mapping tool IDs to their settings
        openai_api_key: API key for tools that require it
        logger: Optional logger for compatibility with existing code

    Returns:
        List of successfully built tool instances
    """
    if logger is None:
        logger = _LOGGER

    tools: List[object] = []
    if not isinstance(tool_ids, list):
        return tools

    tool_settings = tool_settings or {}

    for tool_id in tool_ids:
        if tool_id == "shell":
            logger.warning("Shell tool is disabled by default")
            continue

        settings = tool_settings.get(tool_id)
        tool = build_tool(tool_id, settings, openai_api_key=openai_api_key)
        if tool is not None:
            tools.append(tool)

    return tools


def get_available_tools() -> List[str]:
    """Return list of all registered tool IDs."""
    return list(TOOL_BUILDERS.keys())


def get_tool_metadata(tool_id: str) -> ToolMetadata | None:
    """Return metadata for a specific tool."""
    return TOOL_METADATA.get(tool_id)


def get_all_tool_metadata() -> Dict[str, ToolMetadata]:
    """Return all tool metadata for UI rendering."""
    return dict(TOOL_METADATA)
