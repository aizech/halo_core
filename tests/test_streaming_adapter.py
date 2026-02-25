"""Tests for services/streaming_adapter.py."""

from __future__ import annotations


from services import streaming_adapter


def test_stream_agent_response_collects_mcp_telemetry():
    """Test that stream_agent_response extracts MCP tool events into mcp_events telemetry."""

    class MockTool:
        def __init__(self, name):
            self.name = name
            self.type = "function"

    class MockChunk:
        def __init__(self, event, tool_name, metrics=None):
            self.event = event
            self.tool = MockTool(tool_name)
            self.metrics = metrics

    class FinalChunk:
        def __init__(self):
            self.event = "RunCompleted"
            self.response = "Final"
            self.content = "Final"

    class MockStream:
        def __iter__(self):
            yield MockChunk("ToolCallStarted", "mcp_tool_a", {"time_started": 123})
            yield MockChunk("ToolCallCompleted", "mcp_tool_a", {"time_elapsed": 0.5})
            yield FinalChunk()

    class MockAgent:
        def run(self, payload, **kwargs):
            return MockStream()

    agent = MockAgent()
    result = streaming_adapter.stream_agent_response(agent, "test payload")

    assert result is not None
    mcp_events = result.get("mcp_events")
    assert isinstance(mcp_events, list)
    assert len(mcp_events) == 2

    assert mcp_events[0]["event"] == "toolcallstarted"
    assert mcp_events[0]["tool"]["name"] == "mcp_tool_a"
    assert mcp_events[0]["metrics"] == {"time_started": 123}

    assert mcp_events[1]["event"] == "toolcallcompleted"
    assert mcp_events[1]["tool"]["name"] == "mcp_tool_a"
    assert mcp_events[1]["metrics"] == {"time_elapsed": 0.5}
