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
            FakeChunk(response="Hallo Welt", event="RunResponse"),
        ]


def test_stream_team_skips_duplicate_team_events():
    result = main._stream_agent_response(FakeTeamAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Statt eines einzelnen"


def test_stream_team_only_output():
    result = main._stream_agent_response(FakeTeamOnlyAgent(), "payload")

    assert result is not None
    assert result.get("response") == "Hallo Welt"


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
