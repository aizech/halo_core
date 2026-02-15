"""Routing policy helpers for team member selection."""

from __future__ import annotations

from typing import Dict, List


def select_member_ids(
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
    if coordination_mode in ("", "always_delegate", "coordinated_rag"):
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
