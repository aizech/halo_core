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
