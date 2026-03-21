"""Routing policy helpers for team member selection."""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

_LOGGER = logging.getLogger(__name__)


def _cosine_similarity(a: object, b: object) -> float:
    """Return cosine similarity between two numpy float32 arrays."""
    try:
        import numpy as np

        a_arr = np.asarray(a, dtype=np.float32)
        b_arr = np.asarray(b, dtype=np.float32)
        norm_a = float(np.linalg.norm(a_arr))
        norm_b = float(np.linalg.norm(b_arr))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
    except Exception:
        return 0.0


def _embed_text(text: str) -> object | None:
    """Return an embedding vector for *text*, or None on any error."""
    try:
        from services.retrieval import _embed  # type: ignore[import]

        return _embed(text)
    except Exception:
        return None


def _build_skill_text(member_config: Dict[str, object]) -> str:
    """Concatenate a member's skills, role, and description into a single string."""
    parts: List[str] = []
    for key in ("role", "description", "name"):
        value = member_config.get(key)
        if value and isinstance(value, str):
            parts.append(value.strip())
    skills = member_config.get("skills")
    if isinstance(skills, list):
        parts.extend(str(s).strip() for s in skills if s)
    return " ".join(parts)


def _score_member_semantic(
    member_config: Dict[str, object],
    prompt_vec: object,
) -> float:
    """Return cosine similarity between the prompt and the member's skill text."""
    skill_text = _build_skill_text(member_config)
    if not skill_text:
        return 0.0
    skill_vec = _embed_text(skill_text)
    if skill_vec is None:
        return 0.0
    return _cosine_similarity(prompt_vec, skill_vec)


def _score_member_keyword(member_config: Dict[str, object], prompt_lower: str) -> int:
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

    For ``delegate_on_complexity`` mode, members are ranked by semantic
    similarity between the prompt embedding and each member's skill/role text.
    Falls back to keyword substring scoring when embeddings are unavailable.

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

    # Attempt semantic scoring first; fall back to keyword matching on failure
    prompt_vec = _embed_text(prompt)
    use_semantic = prompt_vec is not None

    if use_semantic:
        _LOGGER.debug(
            "Using semantic embedding routing for %d members", len(normalized_ids)
        )
        scored_float: List[Tuple[str, float]] = []
        for member_id in normalized_ids:
            member_config = member_configs.get(member_id)
            if not isinstance(member_config, dict):
                continue
            sim = _score_member_semantic(member_config, prompt_vec)
            if sim > 0.0:
                scored_float.append((member_id, sim))
        scored_float.sort(key=lambda x: (-x[1], normalized_ids.index(x[0])))
        if top_n is not None and top_n > 0:
            scored_float = scored_float[:top_n]
        return [member_id for member_id, _ in scored_float]

    _LOGGER.debug("Embeddings unavailable; falling back to keyword routing")
    prompt_lower = prompt.casefold()
    scored_int: List[Tuple[str, int]] = []
    for member_id in normalized_ids:
        member_config = member_configs.get(member_id)
        if not isinstance(member_config, dict):
            continue
        score = _score_member_keyword(member_config, prompt_lower)
        if score > 0:
            scored_int.append((member_id, score))
    scored_int.sort(key=lambda x: (-x[1], normalized_ids.index(x[0])))
    if top_n is not None and top_n > 0:
        scored_int = scored_int[:top_n]
    return [member_id for member_id, _ in scored_int]
