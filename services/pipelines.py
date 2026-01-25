"""Pipelines bridging Streamlit UI with Agno agents."""

from __future__ import annotations

from typing import Dict, List

from services import agents


def generate_chat_reply(
    user_prompt: str,
    sources: List[str],
    notes: List[dict],
    contexts: List[dict],
) -> str:
    return agents.generate_grounded_reply(user_prompt, sources, notes, contexts)


def generate_studio_artifact(
    template_name: str,
    instructions: str,
    sources: List[str],
    agent_config: Dict[str, str] | None = None,
) -> str:
    return agents.render_studio_output(
        template_name, instructions, sources, agent_config
    )
