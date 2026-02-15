from __future__ import annotations

from dataclasses import dataclass

from app import main


@dataclass
class FakeChunk:
    content: str | None = None
    response: str | None = None
    event: str | None = None
    tool: object = None
    tools: object = None


class FakeTeamAgent:
    """Simulates Agno Team streaming: each token emitted twice (TeamRunContent + RunContent)."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        tokens = ["Statt", " eines", " einzelnen"]
        chunks = []
        for token in tokens:
            chunks.append(FakeChunk(content=token, event="TeamRunContent"))
            chunks.append(FakeChunk(content=token, event="RunContent"))
        return chunks


class FakeTeamOnlyAgent:
    """Simulates team-only output when no member responses are emitted."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="Hallo", event="TeamRunContent"),
            FakeChunk(content=" Welt", event="TeamRunContent"),
        ]


class FakeFinalContentCompletedAgent:
    """Simulates final authoritative text delivered via content on completed event."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="fragment", event="RunContent"),
            FakeChunk(content="Clean final from content", event="RunContentCompleted"),
            FakeChunk(content="late-noise", event="RunContent"),
        ]


class FakeSingleAgent:
    """Simulates a single agent: each token emitted once (RunContent only)."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="Die", event="RunContent"),
            FakeChunk(content=" ZEIT", event="RunContent"),
        ]


class FakeCumulativeContentAgent:
    """Simulates cumulative RunContent events that include the full response so far."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="Hallo", event="RunContent"),
            FakeChunk(content="Hallo Welt", event="RunContent"),
        ]


class FakeMixedAgent:
    """Simulates content tokens followed by a final full response event."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="Hallo", event="RunContent"),
            FakeChunk(content=" Welt", event="RunContent"),
            FakeChunk(response="Hallo Welt", event="RunCompleted"),
        ]


class FakeToolCallAgent:
    """Simulates tool call started events with tool payloads."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        tool = {"name": "search", "args": {"q": "halo"}}
        return [
            FakeChunk(event="ToolCallStarted", tool=tool),
            FakeChunk(response="done", event="RunCompleted"),
        ]


class FakeEnumEvent:
    def __init__(self, value: str):
        self.value = value


class FakeToolCallEnumEventAgent:
    """Simulates enum-like event objects (event.value) for tool-call events."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        tool = {"name": "search", "args": {"q": "halo"}}
        return [
            FakeChunk(event=FakeEnumEvent("RunEvent.ToolCallStarted"), tool=tool),
            FakeChunk(response="done", event="RunCompleted"),
        ]


class FakeMemberThenTeamAgent:
    """Simulates noisy member output followed by clean team output."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="unsauber", event="RunContent"),
            FakeChunk(content="Sauber", event="TeamRunContent"),
            FakeChunk(content=" Antwort", event="TeamRunContent"),
            FakeChunk(response="Sauber Antwort", event="TeamRunCompleted"),
        ]


class FakeNoisyTokensThenFinalResponseAgent:
    """Simulates malformed token stream followed by canonical final response event."""

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="beschreibtclean", event="RunContent"),
            FakeChunk(content=", reliable", event="RunContent"),
            FakeChunk(response="beschreibt clean, reliable", event="RunCompleted"),
        ]


def test_stream_team_skips_duplicate_team_events():
    result = main._stream_agent_response(FakeTeamAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Statt eines einzelnen"


def test_stream_team_only_output():
    result = main._stream_agent_response(FakeTeamOnlyAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Hallo Welt"


def test_stream_tool_call_started_updates_tools():
    result = main._stream_agent_response(FakeToolCallAgent(), "payload")

    assert result is not None
    tools = result.get("tools") or []
    assert any(
        getattr(tool, "get", None) and tool.get("name") == "search" for tool in tools
    )


def test_stream_tool_call_started_enum_event_updates_tools():
    result = main._stream_agent_response(FakeToolCallEnumEventAgent(), "payload")

    assert result is not None
    tools = result.get("tools") or []
    assert any(
        getattr(tool, "get", None) and tool.get("name") == "search" for tool in tools
    )


def test_stream_single_agent_appends_tokens():
    result = main._stream_agent_response(FakeSingleAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Die ZEIT"


def test_stream_cumulative_content_replaces():
    result = main._stream_agent_response(FakeCumulativeContentAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Hallo Welt"


def test_stream_content_then_response_replaces():
    result = main._stream_agent_response(FakeMixedAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Hallo Welt"


def test_stream_prefers_team_output_after_member_chunks():
    result = main._stream_agent_response(FakeMemberThenTeamAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Sauber Antwort"


def test_stream_final_response_event_is_authoritative():
    result = main._stream_agent_response(FakeNoisyTokensThenFinalResponseAgent(), "payload")

    assert result is not None
    assert result.get("response") == "beschreibt clean, reliable"


class FakeContentAfterFinalAgent:
    """Simulates content chunks arriving AFTER the RunCompleted event.

    This is the exact scenario that caused the UI corruption bug:
    the safety-net _emit_response() would overwrite the clean final
    response with the corrupted _merge_text accumulation.
    """

    def run(self, payload, stream=True, stream_intermediate_steps=True):
        return [
            FakeChunk(content="partial", event="RunContent"),
            FakeChunk(content=" text", event="RunContent"),
            FakeChunk(response="Clean final response", event="RunCompleted"),
            # These arrive after the final event and must be ignored:
            FakeChunk(content="partial text", event="RunContent"),
            FakeChunk(content="Clean final response", event="RunContent"),
        ]


def test_stream_ignores_content_after_final_event():
    """Content chunks after RunCompleted must not corrupt the response."""
    emitted: list[str] = []

    def _on_response(value: str) -> None:
        emitted.append(value)

    result = main._stream_agent_response(
        FakeContentAfterFinalAgent(),
        "payload",
        response_container=None,
        tool_calls_container=None,
    )

    assert result is not None
    assert result.get("response") == "Clean final response"


def test_stream_ui_callback_receives_clean_final():
    """The on_response callback must receive the clean final text, not corrupted merge."""
    emitted: list[str] = []

    from services.streaming_adapter import stream_agent_response

    stream_agent_response(
        FakeContentAfterFinalAgent(),
        "payload",
        on_response=lambda v: emitted.append(v),
    )

    # The last emitted value should be the clean final response
    assert emitted[-1] == "Clean final response"
    # There should be exactly one emit (from the RunCompleted event),
    # not a second safety-net emit
    assert emitted.count("Clean final response") == 1


def test_stream_final_content_completed_is_authoritative():
    result = main._stream_agent_response(FakeFinalContentCompletedAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Clean final from content"
