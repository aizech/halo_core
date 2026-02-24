"""Master team factory for HALO based on JSON configuration."""

from __future__ import annotations

import logging
from typing import Dict, List

from agno.agent import Agent
from agno.team import Team

from services.agents_config import build_agent_instructions
from services.agent_factory import (
    build_mcp_tools,
    build_model,
    build_tools,
    normalize_model_id,
)
from services.routing_policy import select_member_ids
from services.settings import get_settings
from services.knowledge import get_agent_knowledge
from services.storage import get_agent_db

try:  # Optional tool kit
    from agno.tools.reasoning import ReasoningTools
except ImportError:  # pragma: no cover - optional dependency
    ReasoningTools = None


_SETTINGS = get_settings()
_LOGGER = logging.getLogger(__name__)


def build_agent_from_config(
    config: Dict[str, object],
    model,
    session_id: str | None = None,
    user_id: str | None = None,
) -> Agent | None:
    name = str(config.get("name") or config.get("id") or "Agent")
    instructions = build_agent_instructions(config)
    db = get_agent_db()
    knowledge = get_agent_knowledge()
    agent = Agent(
        name=name,
        instructions=instructions,
        model=model,
        markdown=True,
        debug_mode=True,
        session_id=session_id,
        user_id=user_id,
        db=db,
        add_history_to_context=db is not None,
        num_history_runs=3 if db is not None else None,
        enable_user_memories=db is not None,
        knowledge=knowledge,
        search_knowledge=knowledge is not None,
    )
    tools = build_tools(
        config.get("tools"),
        config.get("tool_settings"),
        logger=_LOGGER,
    )
    tools.extend(build_mcp_tools(config.get("mcp_servers"), logger=_LOGGER))
    if tools:
        agent.tools = tools
    return agent


def build_master_team_from_config(
    master_config: Dict[str, object],
    prompt: str | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
) -> Team | None:
    model_id = normalize_model_id(
        master_config.get("model") or master_config.get("model_id")
    )
    model = build_model(
        model_id,
        openai_api_key=_SETTINGS.openai_api_key,
        logger=_LOGGER,
    )
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
            member = build_agent_from_config(
                member_config, model, session_id=session_id, user_id=user_id
            )
            if member:
                member_map[member_id] = member
                member_configs[member_id] = member_config

    selected_member_ids = select_member_ids(master_config, prompt, member_configs)
    members = [
        member_map[member_id]
        for member_id in selected_member_ids
        if member_id in member_map
    ]

    coordination_mode = str(master_config.get("coordination_mode") or "").strip()
    is_coordinated_rag = coordination_mode == "coordinated_rag"

    instructions = build_agent_instructions(master_config)
    if is_coordinated_rag:
        rag_guidance = (
            "\n\nDu arbeitest im koordinierten RAG-Modus. "
            "Beantworte Fragen ausschließlich auf Basis der bereitgestellten Quellen. "
            "Zitiere jede Aussage inline im Format [Quelle]. "
            "Wenn keine passende Quelle vorhanden ist, sage das explizit."
        )
        instructions = (instructions or "") + rag_guidance

    tools = build_tools(
        master_config.get("tools"),
        master_config.get("tool_settings"),
        logger=_LOGGER,
    )
    tools.extend(build_mcp_tools(master_config.get("mcp_servers"), logger=_LOGGER))
    if ReasoningTools is not None:
        tools = [ReasoningTools(add_instructions=True), *tools]

    _LOGGER.info(
        "Building master team '%s' with members=%s model=%s",
        master_config.get("name") or master_config.get("id") or "HALO Master",
        selected_member_ids,
        model_id,
    )

    db = get_agent_db()
    knowledge = get_agent_knowledge()
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
        debug_mode=True,
        session_id=session_id,
        user_id=user_id,
        db=db,
        add_history_to_context=db is not None,
        num_history_runs=3 if db is not None else None,
        enable_user_memories=db is not None,
        knowledge=knowledge,
        search_knowledge=(knowledge is not None) or is_coordinated_rag,
    )
    team.selected_member_ids = selected_member_ids
    return team
