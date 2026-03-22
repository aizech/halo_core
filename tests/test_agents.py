"""Tests for services/agents.py — session isolation after P2-E singleton removal."""

from __future__ import annotations

from unittest.mock import MagicMock


def _make_fake_agent():
    agent = MagicMock()
    agent.run = MagicMock(return_value=MagicMock(content="ok"))
    return agent


class TestFallbackAgentIsolation:
    """Verify _get_fallback_agent returns a fresh instance each call (no shared singleton)."""

    def test_fallback_agent_returns_new_instance_each_call(self, monkeypatch) -> None:
        from services import agents

        fake1 = _make_fake_agent()
        fake2 = _make_fake_agent()
        call_count = 0

        def mock_build(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return fake1 if call_count == 1 else fake2

        monkeypatch.setattr(agents, "_build_agent", mock_build)

        a1 = agents._get_fallback_agent()
        a2 = agents._get_fallback_agent()

        assert (
            a1 is not a2
        ), "Each call should produce a distinct agent (no shared singleton)"
        assert call_count == 2

    def test_no_module_level_agent_singleton(self) -> None:
        import services.agents as agents_module

        assert not hasattr(
            agents_module, "_AGENT"
        ), "_AGENT module-level singleton must not exist after P2-E refactor"

    def test_no_module_level_last_trace(self) -> None:
        import services.agents as agents_module

        assert not hasattr(
            agents_module, "_LAST_TRACE"
        ), "_LAST_TRACE module-level singleton must not exist after P2-E refactor"

    def test_build_chat_agent_with_no_config_uses_fallback(self, monkeypatch) -> None:
        from services import agents

        fallback = _make_fake_agent()
        monkeypatch.setattr(agents, "_build_agent", lambda *a, **kw: fallback)

        result = agents.build_chat_agent(agent_config=None)

        assert (
            result is fallback
        ), "build_chat_agent(None) should delegate to _get_fallback_agent"

    def test_get_fallback_agent_builds_fresh_every_call(self, monkeypatch) -> None:
        from services import agents

        built = []

        def mock_build(*args, **kwargs):
            a = _make_fake_agent()
            built.append(a)
            return a

        monkeypatch.setattr(agents, "_build_agent", mock_build)

        agents._get_fallback_agent()
        agents._get_fallback_agent()

        assert (
            len(built) == 2
        ), "_get_fallback_agent must call _build_agent fresh each time"
        assert (
            built[0] is not built[1]
        ), "each call must produce a distinct agent instance"


class TestSettingsDefaultModel:
    """Verify settings.default_model is used when no agent-specific model is set."""

    def test_settings_has_default_model(self) -> None:
        from services.settings import get_settings

        s = get_settings()
        assert hasattr(s, "default_model")
        assert isinstance(s.default_model, str)
        assert (
            ":" in s.default_model
        ), "default_model should be in 'provider:name' format"

    def test_settings_has_default_chat_instructions(self) -> None:
        from services.settings import get_settings

        s = get_settings()
        assert hasattr(s, "default_chat_instructions")
        assert isinstance(s.default_chat_instructions, str)
        assert len(s.default_chat_instructions) > 0

    def test_normalize_model_id_uses_settings_default(self, monkeypatch) -> None:
        from services import agent_factory

        monkeypatch.setattr(
            agent_factory._SETTINGS, "default_model", "openai:gpt-test-sentinel"
        )

        result = agent_factory.normalize_model_id(None)

        assert result == "openai:gpt-test-sentinel"

    def test_normalize_model_id_respects_explicit_default(self) -> None:
        from services import agent_factory

        result = agent_factory.normalize_model_id(
            None, default_model_id="anthropic:claude-3"
        )

        assert result == "anthropic:claude-3"
