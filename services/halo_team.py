"""Master team factory for HALO based on JSON configuration."""

from __future__ import annotations

import logging
from typing import Dict, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.pubmed import PubmedTools
from agno.tools.wikipedia import WikipediaTools

try:  # Optional Mermaid tool
    from agno.tools.mermaid import MermaidTools
except ImportError:  # pragma: no cover - optional dependency
    MermaidTools = None

from services.agents_config import build_agent_instructions
from services.settings import get_settings

try:  # Optional model providers
    from agno.models.google import Gemini
except ImportError:  # pragma: no cover - optional dependency
    Gemini = None

try:  # Optional model providers
    from agno.models.anthropic import Claude
except ImportError:  # pragma: no cover - optional dependency
    Claude = None

try:  # Optional model providers
    from agno.models.groq import Groq
except ImportError:  # pragma: no cover - optional dependency
    Groq = None

try:  # Optional tool kit
    from agno.tools.reasoning import ReasoningTools
except ImportError:  # pragma: no cover - optional dependency
    ReasoningTools = None


_SETTINGS = get_settings()
_LOGGER = logging.getLogger(__name__)


def _normalize_model_id(raw: object) -> str:
    if not raw:
        return "openai:gpt-5.2"
    model_id = str(raw)
    if ":" in model_id:
        return model_id
    return f"openai:{model_id}"


def _build_model(model_id: str):
    provider, name = model_id.split(":", 1)
    if provider == "openai":
        api_key = _SETTINGS.openai_api_key
        if not api_key:
            _LOGGER.warning("Team not built: missing OpenAI API key")
            return None
        return OpenAIChat(id=name, api_key=api_key)
    if provider == "google":
        if Gemini is None:
            _LOGGER.warning("Gemini model not available")
            return None
        return Gemini(id=name)
    if provider == "anthropic":
        if Claude is None:
            _LOGGER.warning("Claude model not available")
            return None
        return Claude(id=name)
    if provider == "groq":
        if Groq is None:
            _LOGGER.warning("Groq model not available")
            return None
        return Groq(id=name)
    _LOGGER.warning("Unsupported model provider: %s", provider)
    return None


def build_tools(
    tool_ids: object, tool_settings: Dict[str, object] | None = None
) -> List[object]:
    tools: List[object] = []
    if not isinstance(tool_ids, list):
        return tools
    tool_settings = tool_settings or {}
    for tool_id in tool_ids:
        if tool_id == "pubmed":
            pubmed_settings = tool_settings.get("pubmed")
            if isinstance(pubmed_settings, dict):
                tools.append(
                    PubmedTools(
                        email=pubmed_settings.get("email"),
                        max_results=pubmed_settings.get("max_results"),
                        enable_search_pubmed=pubmed_settings.get(
                            "enable_search_pubmed", True
                        ),
                        all=pubmed_settings.get("all", False),
                    )
                )
            else:
                tools.append(PubmedTools())
        if tool_id == "wikipedia":
            tools.append(WikipediaTools())
        if tool_id == "mermaid":
            if MermaidTools is None:
                _LOGGER.warning("Mermaid tool not available")
            else:
                tools.append(MermaidTools())
    return tools


def build_agent_from_config(config: Dict[str, object], model) -> Agent | None:
    name = str(config.get("name") or config.get("id") or "Agent")
    instructions = build_agent_instructions(config)
    agent = Agent(name=name, instructions=instructions, model=model, markdown=True)
    tools = build_tools(config.get("tools"), config.get("tool_settings"))
    if tools:
        agent.tools = tools
    return agent


def _select_member_ids(
    master_config: Dict[str, object],
    prompt: str | None,
    member_configs: Dict[str, Dict[str, object]],
) -> List[str]:
    coordination_mode = str(master_config.get("coordination_mode") or "").strip()
    member_ids = master_config.get("members") or []
    if not isinstance(member_ids, list):
        return []
    normalized_ids = [str(member_id) for member_id in member_ids]
    if coordination_mode == "direct_only":
        return []
    if coordination_mode in ("", "always_delegate"):
        return normalized_ids
    if coordination_mode != "delegate_on_complexity":
        return normalized_ids
    if not prompt:
        return []
    prompt_lower = prompt.casefold()
    selected: List[str] = []
    for member_id in normalized_ids:
        member_config = member_configs.get(member_id)
        if not isinstance(member_config, dict):
            continue
        skills = member_config.get("skills")
        if not isinstance(skills, list):
            continue
        if any(str(skill).casefold() in prompt_lower for skill in skills):
            selected.append(member_id)
    return selected


def build_master_team_from_config(
    master_config: Dict[str, object],
    prompt: str | None = None,
) -> Team | None:
    model_id = _normalize_model_id(
        master_config.get("model") or master_config.get("model_id")
    )
    model = _build_model(model_id)
    if model is None:
        return None

    member_ids = master_config.get("members") or []
    members: List[Agent] = []
    member_map: Dict[str, Agent] = {}
    member_configs: Dict[str, Dict[str, object]] = {}
    if isinstance(member_ids, list):
        from services.agents_config import load_agent_configs

        all_configs = load_agent_configs()
        for agent_id in member_ids:
            member_id = str(agent_id)
            member_config = all_configs.get(member_id)
            if not isinstance(member_config, dict):
                continue
            if member_config.get("enabled", True) is False:
                continue
            member = build_agent_from_config(member_config, model)
            if member:
                member_map[member_id] = member
                member_configs[member_id] = member_config

    selected_member_ids = _select_member_ids(master_config, prompt, member_configs)
    members = [
        member_map[member_id]
        for member_id in selected_member_ids
        if member_id in member_map
    ]

    instructions = build_agent_instructions(master_config)
    tools = build_tools(master_config.get("tools"), master_config.get("tool_settings"))
    if ReasoningTools is not None:
        tools = [ReasoningTools(add_instructions=True), *tools]

    _LOGGER.info(
        "Building master team '%s' with members=%s model=%s",
        master_config.get("name") or master_config.get("id") or "HALO Master",
        selected_member_ids,
        model_id,
    )

    team = Team(
        name=str(master_config.get("name") or "HALO Master"),
        model=model,
        members=members,
        tools=tools,
        instructions=instructions,
        respond_directly=True,
        show_members_responses=True,
        delegate_to_all_members=False,
        determine_input_for_members=True,
        markdown=True,
    )
    team.selected_member_ids = selected_member_ids
    return team
