"""Shared factories for Agno models and tools.

Tool building is delegated to tool_registry.py for extensibility.
This module focuses on model building and MCP tool assembly.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from agno.models.openai import OpenAIChat

from services.settings import get_settings

try:
    from agno.skills import Skills, LocalSkills
except ImportError:
    Skills = None
    LocalSkills = None

try:  # Optional MCP tool kit
    from agno.tools.mcp import MCPTools
except ImportError:  # pragma: no cover - optional dependency
    MCPTools = None

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

_SETTINGS = get_settings()


_TRANSPORT_ALIASES: Dict[str, str] = {
    "": "streamable-http",
    "http": "streamable-http",
    "streamable-http": "streamable-http",
    "sse": "sse",
    "stdio": "stdio",
}


def normalize_transport(raw: str) -> str:
    """Normalise a raw MCP transport string to a canonical value."""
    key = str(raw or "").strip().lower()
    return _TRANSPORT_ALIASES.get(key, key)


def normalize_model_id(raw: object, default_model_id: str | None = None) -> str:
    if default_model_id is None:
        default_model_id = _SETTINGS.default_model
    if not raw:
        return default_model_id
    model_id = str(raw)
    if ":" in model_id:
        return model_id
    return f"openai:{model_id}"


def build_model(model_id: str, *, openai_api_key: str | None, logger: logging.Logger):
    provider, name = model_id.split(":", 1)
    if provider == "openai":
        if not openai_api_key:
            logger.warning("Model not built: missing OpenAI API key")
            return None
        return OpenAIChat(id=name, api_key=openai_api_key)
    if provider == "google":
        if Gemini is None:
            logger.warning("Gemini model not available")
            return None
        return Gemini(id=name)
    if provider == "anthropic":
        if Claude is None:
            logger.warning("Claude model not available")
            return None
        return Claude(id=name)
    if provider == "groq":
        if Groq is None:
            logger.warning("Groq model not available")
            return None
        return Groq(id=name)
    logger.warning("Unsupported model provider: %s", provider)
    return None


def build_tools(
    tool_ids: object,
    tool_settings: Dict[str, Any] | None = None,
    *,
    logger: logging.Logger,
) -> List[object]:
    """Build tools using the tool registry.

    This is a compatibility wrapper around the registry-based tool builder.
    New tools should be registered in tool_registry.py rather than adding
    if-branches here.
    """
    from services.tool_registry import build_tools_from_registry

    return build_tools_from_registry(
        tool_ids if isinstance(tool_ids, list) else [],
        tool_settings,
        openai_api_key=_SETTINGS.openai_api_key,
        logger=logger,
    )


def build_mcp_tools(
    mcp_servers: object,
    *,
    logger: logging.Logger,
) -> List[object]:
    tools: List[object] = []
    if MCPTools is None:
        return tools
    if not isinstance(mcp_servers, list):
        return tools

    for item in mcp_servers:
        if not isinstance(item, dict):
            continue
        server_name = str(item.get("name") or "mcp-server").strip() or "mcp-server"
        if item.get("enabled", True) is False:
            logger.info("MCP server '%s' is disabled; skipping", server_name)
            continue

        transport = normalize_transport(str(item.get("transport") or ""))
        if transport not in {"streamable-http", "sse", "stdio"}:
            logger.warning(
                "MCP server '%s' skipped: unsupported transport: %s",
                server_name,
                transport,
            )
            continue

        url = str(item.get("url") or "").strip()
        command = str(item.get("command") or "").strip()
        if transport in {"streamable-http", "sse"} and not url:
            logger.warning("MCP server '%s' skipped: missing url", server_name)
            continue
        if transport == "stdio" and not command:
            logger.warning("MCP server '%s' skipped: missing command", server_name)
            continue

        allowed_tools_raw = item.get("allowed_tools", [])
        allowed_tools = (
            [
                str(tool_name).strip()
                for tool_name in allowed_tools_raw
                if str(tool_name).strip()
            ]
            if isinstance(allowed_tools_raw, list)
            else []
        )

        kwargs = {"transport": transport}
        if transport in {"streamable-http", "sse"}:
            kwargs["url"] = url
        if transport == "stdio":
            kwargs["command"] = command
        if allowed_tools:
            kwargs["tools"] = allowed_tools

        try:
            tools.append(MCPTools(**kwargs))
            logger.info(
                "MCP server '%s' attached (transport=%s)",
                server_name,
                transport,
            )
        except TypeError:
            logger.warning("MCPTools signature mismatch; retrying without tool filter")
            try:
                if transport in {"streamable-http", "sse"}:
                    tools.append(MCPTools(transport=transport, url=url))
                else:
                    tools.append(MCPTools(command=command))
                logger.info(
                    "MCP server '%s' attached without tool filter (transport=%s)",
                    server_name,
                    transport,
                )
            except Exception:
                logger.exception(
                    "Failed to build MCPTools for server '%s'", server_name
                )
        except Exception:
            logger.exception("Failed to build MCPTools for server '%s'", server_name)

    return tools


def get_skills_dir() -> Path | None:
    """Get the skills directory path from settings or default location."""
    skills_dir = getattr(_SETTINGS, "skills_dir", None)
    if skills_dir:
        return Path(skills_dir)
    default_dir = Path(__file__).parent.parent / "skills"
    if default_dir.exists():
        return default_dir
    return None


def build_skills(
    skill_names: List[str] | None = None,
    *,
    logger: logging.Logger,
) -> Skills | None:
    """Build Agno Skills from the skills directory.

    Args:
        skill_names: Optional list of specific skill names to load.
                    If None, loads all skills from the skills directory.

    Returns:
        Skills object or None if skills cannot be loaded.
    """
    if Skills is None or LocalSkills is None:
        logger.debug("Agno skills not available")
        return None

    skills_dir = get_skills_dir()
    if skills_dir is None or not skills_dir.exists():
        logger.debug("Skills directory not found")
        return None

    try:
        if skill_names:
            skill_paths = [skills_dir / name for name in skill_names]
            loaders = [LocalSkills(str(p)) for p in skill_paths if p.exists()]
            if not loaders:
                logger.debug(f"No valid skill paths found for: {skill_names}")
                return None
            skills = Skills(loaders=loaders)
        else:
            skills = Skills(loaders=[LocalSkills(str(skills_dir))])

        logger.info(f"Loaded skills from: {skills_dir}")
        return skills
    except Exception as e:
        logger.warning(f"Failed to load skills: {e}")
        return None
