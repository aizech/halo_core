from services import pipelines


def test_generate_chat_reply_delegates_to_agents(monkeypatch):
    captured = {}

    def fake_reply(prompt, sources, notes, contexts):
        captured["prompt"] = prompt
        captured["sources"] = sources
        captured["notes"] = notes
        captured["contexts"] = contexts
        return "antwort"

    monkeypatch.setattr("services.agents.generate_grounded_reply", fake_reply)

    result = pipelines.generate_chat_reply("Hallo?", ["A"], ["note"], ["ctx"])

    assert result == "antwort"
    assert captured["sources"] == ["A"]
    assert captured["contexts"] == ["ctx"]


def test_generate_studio_artifact_delegates(monkeypatch):
    def fake_output(template, instructions, sources, agent_config=None):
        return f"{template}|{instructions}|{sources}|{agent_config}"

    monkeypatch.setattr("services.agents.render_studio_output", fake_output)

    result = pipelines.generate_studio_artifact("Quiz", "Anweisungen", ["1"], {"instructions": "test"})

    assert "Quiz" in result
