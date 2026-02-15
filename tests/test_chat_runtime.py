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

    result = run_chat_turn(turn)

    assert result.response == "fallback response\n\n[Quelle: source1, Seite 9]"
    assert result.used_fallback is True
    assert result.trace is not None
    telemetry = (
        result.trace.get("telemetry") if isinstance(result.trace, dict) else None
    )
    assert isinstance(telemetry, dict)
    assert telemetry.get("stream_result") == "empty"
    assert telemetry.get("used_fallback") is True


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
