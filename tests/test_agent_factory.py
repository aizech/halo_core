from __future__ import annotations

import logging

from services import agent_factory


def test_build_tools_includes_websearch_with_settings(monkeypatch):
    class DummyWebSearchTools:
        def __init__(self, backend=None, num_results=None):
            self.backend = backend
            self.num_results = num_results

    monkeypatch.setattr(agent_factory, "WebSearchTools", DummyWebSearchTools)

    tools = agent_factory.build_tools(
        ["websearch"],
        {"websearch": {"backend": "duckduckgo", "num_results": 5}},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyWebSearchTools)
    assert tools[0].backend == "duckduckgo"
    assert tools[0].num_results == 5


def test_build_tools_websearch_falls_back_when_settings_unsupported(monkeypatch):
    class DummyWebSearchTools:
        def __init__(self, backend=None, num_results=None):
            if backend is not None or num_results is not None:
                raise TypeError("unexpected keyword")
            self.used_defaults = True

    monkeypatch.setattr(agent_factory, "WebSearchTools", DummyWebSearchTools)

    tools = agent_factory.build_tools(
        ["websearch"],
        {"websearch": {"backend": "duckduckgo", "num_results": 5}},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyWebSearchTools)
    assert tools[0].used_defaults is True


def test_build_tools_includes_youtube_with_settings(monkeypatch):
    class DummyYouTubeTools:
        def __init__(
            self,
            fetch_captions=True,
            fetch_video_info=True,
            fetch_timestamps=False,
        ):
            self.fetch_captions = fetch_captions
            self.fetch_video_info = fetch_video_info
            self.fetch_timestamps = fetch_timestamps

    monkeypatch.setattr(agent_factory, "YouTubeTools", DummyYouTubeTools)

    tools = agent_factory.build_tools(
        ["youtube"],
        {
            "youtube": {
                "fetch_captions": True,
                "fetch_video_info": False,
                "fetch_timestamps": True,
            }
        },
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyYouTubeTools)
    assert tools[0].fetch_captions is True
    assert tools[0].fetch_video_info is False
    assert tools[0].fetch_timestamps is True


def test_build_tools_includes_duckduckgo_with_settings(monkeypatch):
    class DummyDuckDuckGoTools:
        def __init__(
            self,
            enable_search=True,
            enable_news=True,
            fixed_max_results=None,
            timeout=10,
            verify_ssl=True,
        ):
            self.enable_search = enable_search
            self.enable_news = enable_news
            self.fixed_max_results = fixed_max_results
            self.timeout = timeout
            self.verify_ssl = verify_ssl

    monkeypatch.setattr(agent_factory, "DuckDuckGoTools", DummyDuckDuckGoTools)

    tools = agent_factory.build_tools(
        ["duckduckgo"],
        {
            "duckduckgo": {
                "enable_search": True,
                "enable_news": False,
                "fixed_max_results": 7,
                "timeout": 12,
                "verify_ssl": False,
            }
        },
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyDuckDuckGoTools)
    assert tools[0].enable_search is True
    assert tools[0].enable_news is False
    assert tools[0].fixed_max_results == 7
    assert tools[0].timeout == 12
    assert tools[0].verify_ssl is False


def test_build_tools_includes_arxiv_tool(monkeypatch):
    class DummyArxivTools:
        pass

    monkeypatch.setattr(agent_factory, "ArxivTools", DummyArxivTools)

    tools = agent_factory.build_tools(
        ["arxiv"],
        {},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyArxivTools)


def test_build_tools_includes_arxiv_tool_with_settings(monkeypatch):
    class DummyArxivTools:
        def __init__(self, max_results=5, sort_by=None):
            self.max_results = max_results
            self.sort_by = sort_by

    monkeypatch.setattr(agent_factory, "ArxivTools", DummyArxivTools)

    tools = agent_factory.build_tools(
        ["arxiv"],
        {"arxiv": {"max_results": 12, "sort_by": "relevance"}},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyArxivTools)
    assert tools[0].max_results == 12
    assert tools[0].sort_by == "relevance"


def test_build_tools_includes_website_tool(monkeypatch):
    class DummyWebsiteTools:
        pass

    monkeypatch.setattr(agent_factory, "WebsiteTools", DummyWebsiteTools)

    tools = agent_factory.build_tools(
        ["website"],
        {},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyWebsiteTools)


def test_build_tools_includes_website_tool_with_guardrails(monkeypatch):
    class DummyWebsiteTools:
        def __init__(self, max_pages=5, timeout=10, allowed_domains=None):
            self.max_pages = max_pages
            self.timeout = timeout
            self.allowed_domains = allowed_domains or []

    monkeypatch.setattr(agent_factory, "WebsiteTools", DummyWebsiteTools)

    tools = agent_factory.build_tools(
        ["website"],
        {
            "website": {
                "max_pages": 99,
                "timeout": 999,
                "allowed_domains": ["example.com", "", " docs.example.com "],
            }
        },
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyWebsiteTools)
    assert tools[0].max_pages == 20
    assert tools[0].timeout == 120
    assert tools[0].allowed_domains == ["example.com", "docs.example.com"]


def test_build_tools_ignores_shell_by_default(monkeypatch):
    class DummyCalculatorTools:
        pass

    monkeypatch.setattr(agent_factory, "CalculatorTools", DummyCalculatorTools)

    tools = agent_factory.build_tools(
        ["shell", "calculator"],
        {},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyCalculatorTools)


def test_build_mcp_tools_includes_streamable_http_server(monkeypatch):
    class DummyMCPTools:
        def __init__(self, transport=None, url=None, tools=None):
            self.transport = transport
            self.url = url
            self.tools = tools

    monkeypatch.setattr(agent_factory, "MCPTools", DummyMCPTools)

    tools = agent_factory.build_mcp_tools(
        [
            {
                "name": "docs",
                "transport": "streamable-http",
                "url": "https://docs.example.com/mcp",
                "allowed_tools": ["search_docs"],
            }
        ],
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyMCPTools)
    assert tools[0].transport == "streamable-http"
    assert tools[0].url == "https://docs.example.com/mcp"
    assert tools[0].tools == ["search_docs"]


def test_build_mcp_tools_skips_unsupported_transport(monkeypatch):
    class DummyMCPTools:
        def __init__(self, transport=None, url=None, tools=None):
            self.transport = transport
            self.url = url
            self.tools = tools

    monkeypatch.setattr(agent_factory, "MCPTools", DummyMCPTools)

    tools = agent_factory.build_mcp_tools(
        [
            {
                "name": "stdio_server",
                "transport": "stdio",
                "url": "http://ignored.example",
            }
        ],
        logger=logging.getLogger(__name__),
    )

    assert tools == []


def test_build_tools_includes_hackernews_with_settings(monkeypatch):
    class DummyHackerNewsTools:
        def __init__(
            self,
            enable_get_top_stories=True,
            enable_get_user_details=True,
            all=False,
        ):
            self.enable_get_top_stories = enable_get_top_stories
            self.enable_get_user_details = enable_get_user_details
            self.all = all

    monkeypatch.setattr(agent_factory, "HackerNewsTools", DummyHackerNewsTools)

    tools = agent_factory.build_tools(
        ["hackernews"],
        {
            "hackernews": {
                "enable_get_top_stories": False,
                "enable_get_user_details": True,
                "all": True,
            }
        },
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyHackerNewsTools)
    assert tools[0].enable_get_top_stories is False
    assert tools[0].enable_get_user_details is True
    assert tools[0].all is True


def test_build_tools_includes_yfinance_with_settings(monkeypatch):
    class DummyYFinanceTools:
        def __init__(self, stock_price=True, analyst_recommendations=True):
            self.stock_price = stock_price
            self.analyst_recommendations = analyst_recommendations

    monkeypatch.setattr(agent_factory, "YFinanceTools", DummyYFinanceTools)

    tools = agent_factory.build_tools(
        ["yfinance"],
        {"yfinance": {"stock_price": True, "analyst_recommendations": False}},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyYFinanceTools)
    assert tools[0].stock_price is True
    assert tools[0].analyst_recommendations is False


def test_build_tools_includes_calculator_tool(monkeypatch):
    class DummyCalculatorTools:
        pass

    monkeypatch.setattr(agent_factory, "CalculatorTools", DummyCalculatorTools)

    tools = agent_factory.build_tools(
        ["calculator"],
        {},
        logger=logging.getLogger(__name__),
    )

    assert len(tools) == 1
    assert isinstance(tools[0], DummyCalculatorTools)
