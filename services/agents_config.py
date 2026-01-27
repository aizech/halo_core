"""Load and persist per-agent configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from services.settings import get_settings

_SETTINGS = get_settings()


DEFAULT_CHAT_INSTRUCTIONS = (
    "Du bist ein Assistent, der Fragen nur mit den bereitgestellten Quellen beantwortet. "
    "Zitiere Quellen inline im Format [Quelle]."
)


def _agent_dir() -> Path:
    return Path(__file__).resolve().parent / "agents"


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
        "members": ["reports"],
        "tools": [],
        "model": "openai:gpt-5.2",
        "enabled": True,
    }


def _default_configs() -> List[Dict[str, object]]:
    defaults = [_default_chat_config(), _default_pubmed_config()]
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


def load_agent_configs() -> Dict[str, Dict[str, object]]:
    ensure_default_agent_configs()
    configs: Dict[str, Dict[str, object]] = {}
    defaults_by_id = {
        str(payload.get("id", "agent")): payload for payload in _default_configs()
    }
    for path in _agent_dir().glob("*.json"):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        agent_id = str(payload.get("id", path.stem))
        payload.setdefault("id", agent_id)
        defaults = defaults_by_id.get(agent_id)
        if isinstance(defaults, dict):
            merged = {**defaults, **payload, "id": agent_id}
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
