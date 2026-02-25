"""Tests for services/chat_runtime.py (Task 9)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


from services.chat_runtime import (
    ChatTurnInput,
    ChatTurnResult,
    run_chat_turn,
)
from services import chat_runtime


@dataclass
class FakeChunk:
    content: str | None = None
    response: str | None = None
    event: str | None = None
    tool: object = None
    tools: object = None


class FakeAgent:
    """Minimal fake agent for testing."""

    name = "FakeAgent"

    def run(
        self, payload, stream=True, stream_events=True, stream_intermediate_steps=True
    ):
        return [
            FakeChunk(content="Hello", event="RunContent"),
            FakeChunk(response="Hello World", event="RunCompleted"),
        ]


class FakeEmptyAgent:
    """Agent that returns no content."""

    name = "FakeEmptyAgent"

    def run(
        self, payload, stream=True, stream_events=True, stream_intermediate_steps=True
    ):
        return []


class FakeNamedTool:
    name = "search_knowledge_base"


class FakeMember:
    def __init__(self, name: str):
        self.name = name


class FakeTeamAgent(FakeAgent):
    name = "FakeTeam"

    def __init__(self):
        self.tools = [FakeNamedTool()]
        self.members = [FakeMember("Research"), FakeMember("Synthesis")]
        self.selected_member_ids = ["research", "synthesis"]


def test_chat_turn_input_defaults():
    turn = ChatTurnInput(prompt="test")
    assert turn.prompt == "test"
    assert turn.sources == []
    assert turn.notes == []
    assert turn.session_id is None
    assert turn.agent_config is None
    assert turn.stream_events is True


def test_chat_turn_result_defaults():
    result = ChatTurnResult()
    assert result.response == ""
    assert result.tool_calls is None
    assert result.trace is None
    assert result.used_fallback is False


def test_run_chat_turn_with_streaming(monkeypatch):
    """run_chat_turn returns streamed response when agent streams successfully."""
    captured_responses: List[str] = []

    def _on_response(value: str) -> None:
        captured_responses.append(value)

    turn = ChatTurnInput(
        prompt="test question",
        sources=["source1"],
        notes=[],
        on_response=_on_response,
    )

    # Mock agent creation to return our fake agent
    monkeypatch.setattr(chat_runtime, "create_chat_agent", lambda t: FakeAgent())
    # Mock payload build to skip retrieval
    monkeypatch.setattr(
        chat_runtime,
        "build_chat_payload",
        lambda t: ("fake payload", [{"meta": {"title": "source1", "page": "2"}}]),
    )
    # Mock get_last_trace
    monkeypatch.setattr(
        chat_runtime.agents, "get_last_trace", lambda: {"agent_name": "test"}
    )

    # Mock stream_chat_response_async to bypass async/streaming details in this test
    async def mock_stream(*args, **kwargs):
        # Simulate on_response callback which is tested here
        if "turn" in kwargs and kwargs["turn"].on_response:
            kwargs["turn"].on_response("Hello ")
            kwargs["turn"].on_response("World")
        elif len(args) > 2 and args[2].on_response:
            args[2].on_response("Hello ")
            args[2].on_response("World")

        return {"response": "Hello World", "tool_calls": None}

    monkeypatch.setattr(chat_runtime, "stream_chat_response", mock_stream)

    result = run_chat_turn(turn)

    assert result.response == "Hello World\n\n[Quelle: source1, Seite 2]"
    assert result.used_fallback is False
    assert result.trace is not None
    assert result.trace.get("agent_name") == "test"
    telemetry = (
        result.trace.get("telemetry") if isinstance(result.trace, dict) else None
    )
    assert isinstance(telemetry, dict)
    assert telemetry.get("knowledge_hits") == 1
    assert telemetry.get("stream_result") == "ok"
    assert telemetry.get("used_fallback") is False
    assert len(captured_responses) > 0


def test_run_chat_turn_fallback_on_empty_stream(monkeypatch):
    """run_chat_turn uses fallback when streaming returns empty response."""
    turn = ChatTurnInput(
        prompt="test question",
        sources=["source1"],
        notes=[],
    )

    monkeypatch.setattr(chat_runtime, "create_chat_agent", lambda t: FakeEmptyAgent())
    monkeypatch.setattr(
        chat_runtime,
        "build_chat_payload",
        lambda t: ("fake payload", [{"meta": {"title": "source1", "page": "9"}}]),
    )
    monkeypatch.setattr(chat_runtime.agents, "get_last_trace", lambda: None)
    monkeypatch.setattr(
        chat_runtime, "_fallback_reply", lambda t, c: "fallback response"
    )

    async def mock_stream_empty(*args, **kwargs):
        return {"response": ""}

    monkeypatch.setattr(chat_runtime, "stream_chat_response", mock_stream_empty)

    result = run_chat_turn(turn)

    assert result.response == "fallback response\n\n[Quelle: source1, Seite 9]"
    assert result.used_fallback is True
    assert result.trace is not None
    telemetry = (
        result.trace.get("telemetry") if isinstance(result.trace, dict) else None
    )
    assert isinstance(telemetry, dict)
    assert telemetry.get("stream_result") == "empty"


def test_mcp_lifecycle_management_success(monkeypatch):
    """Test that MCP lifecycle correctly enters and exits context managers."""
    import asyncio

    class DummyMCPTool:
        def __init__(self, name):
            self.name = name
            self.entered = False
            self.exited = False

        async def __aenter__(self):
            self.entered = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            self.exited = True
            return False

    mcp1 = DummyMCPTool("mcp1")
    # Need to make it look like an MCPTools object for the type check filter
    mcp1.__class__.__name__ = "MCPTools"

    class FakeTeam:
        tools = [mcp1]

    agent = FakeTeam()

    async def run_test():
        # Simulate stream_chat_response behavior
        async with await chat_runtime._manage_mcp_lifecycle(agent):
            assert mcp1.entered is True
            assert mcp1.exited is False

    asyncio.run(run_test())

    assert mcp1.entered is True
    assert mcp1.exited is True


def test_mcp_lifecycle_management_exception(monkeypatch):
    """Test that MCP lifecycle correctly exits even if an exception occurs."""
    import asyncio

    class DummyMCPTool:
        def __init__(self, name):
            self.name = name
            self.entered = False
            self.exited = False

        async def __aenter__(self):
            self.entered = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            self.exited = True
            return False

    mcp1 = DummyMCPTool("mcp1")
    mcp1.__class__.__name__ = "MCPTools"

    class FakeTeam:
        tools = [mcp1]

    agent = FakeTeam()

    async def run_test():
        try:
            async with await chat_runtime._manage_mcp_lifecycle(agent):
                assert mcp1.entered is True
                raise ValueError("Test error during stream")
        except ValueError:
            pass

    asyncio.run(run_test())

    assert mcp1.entered is True
    assert mcp1.exited is True


def test_mcp_circuit_breaker_logic(monkeypatch):
    """Test that repeatedly failing MCP servers trigger the circuit breaker."""
    import asyncio
    import time
    from services import chat_runtime

    # Reset breaker state for test isolation
    chat_runtime._MCP_CIRCUIT_BREAKER_FAILURES.clear()

    class FailingMCPTool:
        def __init__(self, name):
            self.name = name
            self.attempts = 0

        async def __aenter__(self):
            self.attempts += 1
            raise ConnectionError("Simulated connection failure")

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    mcp_fail = FailingMCPTool("failing_server")
    mcp_fail.__class__.__name__ = "MCPTools"

    class FakeTeam:
        tools = [mcp_fail]

    agent = FakeTeam()

    async def run_test():
        # Attempt 1: fails, sets failures=1
        async with await chat_runtime._manage_mcp_lifecycle(agent):
            pass

        # Attempt 2: fails, sets failures=2
        async with await chat_runtime._manage_mcp_lifecycle(agent):
            pass

        # Attempt 3: fails, sets failures=3
        async with await chat_runtime._manage_mcp_lifecycle(agent):
            pass

        # Total attempts so far = 3 attempts * 2 retries each = 6 attempts
        assert mcp_fail.attempts == 6

        # Attempt 4: circuit breaker is open, should skip connection attempt entirely
        async with await chat_runtime._manage_mcp_lifecycle(agent):
            pass

        # Attempts remain 6, proving circuit breaker skipped it
        assert mcp_fail.attempts == 6

        # Simulate time passing to trigger circuit breaker reset
        base_time = time.time()
        monkeypatch.setattr(time, "time", lambda: base_time + 301)

        # Attempt 5: breaker expired, should try again
        async with await chat_runtime._manage_mcp_lifecycle(agent):
            pass

        # Attempts went up by 2 (the standard retries)
        assert mcp_fail.attempts == 8

    asyncio.run(run_test())
    chat_runtime._MCP_CIRCUIT_BREAKER_FAILURES.clear()


def test_run_chat_turn_fallback_on_none_stream(monkeypatch):
    """run_chat_turn uses fallback when stream_chat_response returns None."""
    turn = ChatTurnInput(
        prompt="test question",
        sources=[],
        notes=[],
    )

    monkeypatch.setattr(chat_runtime, "create_chat_agent", lambda t: FakeAgent())
    monkeypatch.setattr(
        chat_runtime, "build_chat_payload", lambda t: ("fake payload", [])
    )
    monkeypatch.setattr(chat_runtime, "stream_chat_response", lambda a, p, t: None)
    monkeypatch.setattr(chat_runtime.agents, "get_last_trace", lambda: None)
    monkeypatch.setattr(
        chat_runtime, "_fallback_reply", lambda t, c: "fallback response"
    )

    result = run_chat_turn(turn)

    assert result.response == "fallback response"
    assert result.used_fallback is True
    assert result.trace is not None
    telemetry = (
        result.trace.get("telemetry") if isinstance(result.trace, dict) else None
    )
    assert isinstance(telemetry, dict)
    assert telemetry.get("stream_result") == "none"
    assert telemetry.get("used_fallback") is True


def test_run_chat_turn_trace_contains_structured_telemetry(monkeypatch):
    turn = ChatTurnInput(
        prompt="Welche Kernaussage steht in den Quellen?",
        sources=["A.pdf", "B.pdf"],
        notes=[],
        agent_config={"model": "openai:gpt-5.2"},
    )

    monkeypatch.setattr(chat_runtime, "create_chat_agent", lambda t: FakeTeamAgent())
    monkeypatch.setattr(
        chat_runtime,
        "build_chat_payload",
        lambda t: (
            "fake payload",
            [
                {"meta": {"title": "A.pdf", "page": "3"}},
                {"meta": {"title": "B.pdf", "page": "7"}},
            ],
        ),
    )
    monkeypatch.setattr(
        chat_runtime.agents, "get_last_trace", lambda: {"agent_name": "base"}
    )

    result = run_chat_turn(turn)

    assert result.trace is not None
    telemetry = (
        result.trace.get("telemetry") if isinstance(result.trace, dict) else None
    )
    assert isinstance(telemetry, dict)
    assert telemetry.get("model") == "openai:gpt-5.2"
    assert telemetry.get("selected_members") == ["research", "synthesis"]
    assert telemetry.get("tools") == ["search_knowledge_base"]
    assert telemetry.get("knowledge_hits") == 2
    assert telemetry.get("knowledge_sources") == ["A.pdf", "B.pdf"]


def test_apply_citation_policy_single_source_uses_one_citation_with_page():
    response = (
        "Antwort mit mehrfachen Zitaten [Quelle].\n" "Noch ein Satz [Source: Some Doc]."
    )
    contexts = [{"meta": {"title": "source1", "page_number": "4"}}]

    normalized = chat_runtime._apply_citation_policy(response, ["source1"], contexts)

    assert normalized.endswith("[Quelle: source1, Seite 4]")
    assert normalized.count("[Quelle:") == 1


def test_apply_citation_policy_multiple_sources_appends_markdown_quellen_list():
    response = "Kurzantwort in Markdown."
    contexts = [
        {"meta": {"title": "A.pdf", "chunk_index": "0"}},
        {"meta": {"title": "B.pdf", "page": "12"}},
    ]

    normalized = chat_runtime._apply_citation_policy(
        response,
        ["A.pdf", "B.pdf"],
        contexts,
    )

    assert "### Quellen" in normalized
    assert "[Quelle: A.pdf, Seite 1]" in normalized
    assert "[Quelle: B.pdf, Seite 12]" in normalized


def test_create_chat_agent_passes_user_id(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_build_chat_agent(
        agent_config, *, prompt=None, session_id=None, user_id=None
    ):
        captured["agent_config"] = agent_config
        captured["prompt"] = prompt
        captured["session_id"] = session_id
        captured["user_id"] = user_id
        return "agent"

    monkeypatch.setattr(chat_runtime.agents, "build_chat_agent", _fake_build_chat_agent)

    turn = ChatTurnInput(
        prompt="hello",
        session_id="s1",
        user_id="u1",
        agent_config={"id": "chat"},
    )

    agent = chat_runtime.create_chat_agent(turn)

    assert agent == "agent"
    assert captured["prompt"] == "hello"
    assert captured["session_id"] == "s1"
    assert captured["user_id"] == "u1"
