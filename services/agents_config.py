"""Load and persist per-agent configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from services.settings import get_settings

_SETTINGS = get_settings()


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str = ""
    description: str = ""
    role: str = ""
    instructions: str | List[str] = ""
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    mcp_calls: List[str] = Field(default_factory=list)
    mcp_servers: List[Dict[str, Any]] = Field(default_factory=list)
    model: str | None = None
    coordination_mode: str | None = None
    stream_events: bool = True
    memory_scope: str | None = None
    enabled: bool = True
    members: List[str] = Field(default_factory=list)
    tool_settings: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("instructions")
    @classmethod
    def _validate_instructions(cls, value: str | List[str]) -> str | List[str]:
        if isinstance(value, str):
            return value
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value
        raise ValueError("instructions must be a string or list of strings")

    @field_validator("skills", "tools", "mcp_calls", "members")
    @classmethod
    def _validate_string_list(cls, value: List[str]) -> List[str]:
        if all(isinstance(item, str) for item in value):
            return value
        raise ValueError("must be a list of strings")

    @field_validator("mcp_servers", mode="before")
    @classmethod
    def _validate_mcp_servers(cls, value: object) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError("must be a list")

        seen_names: set[str] = set()
        validated: List[Dict[str, Any]] = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, str):
                command = item.strip()
                if not command:
                    continue
                item = {
                    "name": f"command-{index}",
                    "enabled": False,
                    "transport": "streamable-http",
                    "url": "",
                    "command": command,
                }
            if not isinstance(item, dict):
                raise ValueError("mcp_servers entries must be objects")

            normalized = dict(item)
            name = str(normalized.get("name") or "").strip()
            if not name:
                raise ValueError("mcp_servers.name is required")
            lowered = name.lower()
            if lowered in seen_names:
                raise ValueError(f"duplicate mcp server name: {name}")
            seen_names.add(lowered)

            enabled = bool(normalized.get("enabled", True))
            normalized["enabled"] = enabled

            transport_raw = str(
                normalized.get("transport") or "streamable-http"
            ).strip()
            transport = (
                "streamable-http"
                if transport_raw.lower() in {"", "http", "streamable-http"}
                else transport_raw
            )
            if transport != "streamable-http":
                raise ValueError("mcp_servers.transport must be streamable-http")
            normalized["transport"] = transport

            url = str(normalized.get("url") or "").strip()
            if enabled and not url:
                # Auto-disable servers without URL instead of failing
                normalized["enabled"] = False
            normalized["url"] = url

            allowed_tools = normalized.get("allowed_tools", [])
            if not isinstance(allowed_tools, list) or any(
                not isinstance(tool, str) for tool in allowed_tools
            ):
                raise ValueError("mcp_servers.allowed_tools must be a list of strings")
            normalized["allowed_tools"] = [
                tool.strip() for tool in allowed_tools if tool.strip()
            ]

            validated.append(normalized)

        return validated


def _normalize_instructions(value: object) -> str:
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def _validate_agent_config(payload: Dict[str, object], path: Path) -> Dict[str, object]:
    try:
        validated = AgentConfig.model_validate(payload)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        )
        raise ValueError(f"Invalid agent config '{path.name}': {details}") from exc
    normalized = validated.model_dump(exclude_none=True, exclude_unset=True)
    normalized["instructions"] = _normalize_instructions(normalized.get("instructions"))
    return normalized


DEFAULT_CHAT_INSTRUCTIONS = (
    "Du bist ein Assistent, der Fragen nur mit den bereitgestellten Quellen beantwortet. "
    "Zitiere Quellen inline im Format [Quelle]."
)

DEFAULT_MCP_SERVERS = [
    {
        "name": "airbnb",
        "enabled": False,
        "transport": "streamable-http",
        "url": "",
        "command": "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
    }
]


def _agent_dir() -> Path:
    return Path(_SETTINGS.data_dir) / "agents"


def _migration_marker() -> Path:
    return _agent_dir() / ".migrated_v1"


def _load_templates() -> List[dict]:
    templates_path = Path(_SETTINGS.templates_dir) / "studio_templates.json"
    if not templates_path.exists():
        return []
    with templates_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("templates", []) if isinstance(data, dict) else []


def _default_chat_config() -> Dict[str, object]:
    return {
        "id": "chat",
        "name": "HALO Master",
        "description": "Beantwortet Nutzerfragen basierend auf den ausgewählten Quellen.",
        "role": "assistant",
        "instructions": DEFAULT_CHAT_INSTRUCTIONS,
        "members": ["reports", "infographic"],
        "tools": [],
        "mcp_servers": list(DEFAULT_MCP_SERVERS),
        "model": "openai:gpt-5.2",
        "stream_events": True,
        "enabled": True,
    }


def _default_web_research_config() -> Dict[str, object]:
    return {
        "id": "web_research",
        "name": "Web Research Agent",
        "description": "Recherchiert im Web, in arXiv und auf Websites ohne API-Key.",
        "role": "research_agent",
        "instructions": (
            "Nutze DuckDuckGo, arXiv und Website-Quellen für die Recherche. "
            "Antworte prägnant und nenne immer die Quelle mit Link."
        ),
        "tools": ["duckduckgo", "arxiv", "website"],
        "tool_settings": {
            "duckduckgo": {
                "enable_search": True,
                "enable_news": True,
                "fixed_max_results": 5,
                "timeout": 10,
                "verify_ssl": True,
            }
        },
        "enabled": True,
    }


def _default_configs() -> List[Dict[str, object]]:
    defaults = [
        _default_chat_config(),
        _default_pubmed_config(),
        _default_web_research_config(),
    ]
    for template in _load_templates():
        defaults.append(_default_template_config(template))
    return defaults


def _default_pubmed_config() -> Dict[str, object]:
    return {
        "id": "pubmed",
        "name": "PubMed Agent",
        "description": "Sucht medizinische Studien in PubMed.",
        "role": "research_agent",
        "instructions": (
            "Suche relevante Paper in PubMed und fasse die wichtigsten Erkenntnisse zusammen. "
            "Nenne Titel, Jahr und PMID, wenn vorhanden."
        ),
        "tools": ["pubmed"],
        "enabled": True,
    }


def _default_template_config(template: dict) -> Dict[str, object]:
    agent_cfg = template.get("agent", {}) if isinstance(template, dict) else {}
    return {
        "id": template.get("id", "template"),
        "name": template.get("title", "Studio Agent"),
        "description": template.get("description", ""),
        "role": "studio_agent",
        "instructions": agent_cfg.get("instructions", ""),
        "tools": [],
        "enabled": True,
    }


def ensure_default_agent_configs() -> None:
    agent_dir = _agent_dir()
    agent_dir.mkdir(parents=True, exist_ok=True)
    existing = {path.stem for path in agent_dir.glob("*.json")}
    for payload in _default_configs():
        agent_id = str(payload.get("id", "agent"))
        if agent_id in existing:
            continue
        path = agent_dir / f"{agent_id}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)


def migrate_agent_configs() -> None:
    marker = _migration_marker()
    if marker.exists():
        return
    ensure_default_agent_configs()
    marker.write_text("migrated", encoding="utf-8")


def load_agent_configs() -> Dict[str, Dict[str, object]]:
    migrate_agent_configs()
    configs: Dict[str, Dict[str, object]] = {}
    defaults_by_id = {
        str(payload.get("id", "agent")): payload for payload in _default_configs()
    }
    for path in _agent_dir().glob("*.json"):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        agent_id = str(payload.get("id", path.stem))
        payload.setdefault("id", agent_id)
        payload = _validate_agent_config(payload, path)
        defaults = defaults_by_id.get(agent_id)
        if isinstance(defaults, dict):
            merged = {**defaults, **payload, "id": agent_id}
            merged = _validate_agent_config(merged, path)
            if merged != payload:
                save_agent_config(agent_id, merged)
            payload = merged
        configs[agent_id] = payload
    return configs


def save_agent_config(agent_id: str, payload: Dict[str, object]) -> None:
    agent_dir = _agent_dir()
    agent_dir.mkdir(parents=True, exist_ok=True)
    payload = {**payload, "id": agent_id}
    path = agent_dir / f"{agent_id}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def build_agent_instructions(config: Dict[str, object]) -> str:
    role = str(config.get("role") or "").strip()
    description = str(config.get("description") or "").strip()
    instructions = str(config.get("instructions") or "").strip()
    tools = config.get("tools")
    tool_notice = ""
    if isinstance(tools, list) and tools:
        tool_names = ", ".join(str(tool) for tool in tools)
        tool_notice = (
            "Du darfst die konfigurierten Tools nutzen, um externe Informationen zu "
            f"suchen ({tool_names}). Wenn du Tools nutzt, gib die Quelle an."
        )
        if "wikipedia" in [str(tool).lower() for tool in tools]:
            tool_notice = (
                f"{tool_notice} Wenn du Wikipedia nutzt, gib einen klickbaren "
                "Wikipedia-Link in der Antwort an."
            )
    header_lines = []
    if role:
        header_lines.append(f"Rolle: {role}")
    if description:
        header_lines.append(f"Beschreibung: {description}")
    if header_lines:
        header = "\n".join(header_lines)
        combined = "\n\n".join(
            part for part in (header, instructions, tool_notice) if part
        )
        return combined.strip()
    combined = "\n\n".join(part for part in (instructions, tool_notice) if part)
    return combined
