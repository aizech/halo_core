"""Routing policy helpers for team member selection."""

from __future__ import annotations

from typing import Dict, List, Tuple


def _score_member(member_config: Dict[str, object], prompt_lower: str) -> int:
    """Score a member based on skill keyword matches in prompt.

    Returns the count of matching skill keywords.
    """
    skills = member_config.get("skills")
    if not isinstance(skills, list):
        return 0

    score = 0
    for skill in skills:
        skill_str = str(skill).casefold().strip()
        if skill_str and skill_str in prompt_lower:
            score += 1
    return score


def select_member_ids(
    master_config: Dict[str, object],
    prompt: str | None,
    member_configs: Dict[str, Dict[str, object]],
    *,
    top_n: int | None = None,
) -> List[str]:
    """Select team member IDs based on coordination mode and prompt content.

    For delegate_on_complexity mode, members are ranked by skill-score
    (number of matching skill keywords in the prompt).

    Args:
        master_config: Team configuration with coordination_mode and members list
        prompt: The user prompt to analyze for skill matching
        member_configs: Dict mapping member IDs to their configurations
        top_n: Optional limit on number of members to return (for skill-scored results)

    Returns:
        List of selected member IDs, ordered by relevance for skill-scored modes
    """
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

    # Score each member and sort by score (descending)
    scored: List[Tuple[str, int]] = []
    for member_id in normalized_ids:
        member_config = member_configs.get(member_id)
        if not isinstance(member_config, dict):
            continue
        score = _score_member(member_config, prompt_lower)
        if score > 0:
            scored.append((member_id, score))

    # Sort by score descending, then by original order for ties
    scored.sort(key=lambda x: (-x[1], normalized_ids.index(x[0])))

    # Apply top_n limit if specified
    if top_n is not None and top_n > 0:
        scored = scored[:top_n]

    return [member_id for member_id, _ in scored]
