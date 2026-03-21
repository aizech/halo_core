from __future__ import annotations

from unittest.mock import patch

import numpy as np

from services.routing_policy import (
    _build_skill_text,
    _cosine_similarity,
    select_member_ids,
)


def test_select_member_ids_direct_only_returns_empty() -> None:
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "direct_only",
    }

    selected = select_member_ids(config, "report summary", {})

    assert selected == []


def test_select_member_ids_delegate_on_complexity_matches_skills() -> None:
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "delegate_on_complexity",
    }
    member_configs = {
        "reports": {"skills": ["report"]},
        "infographic": {"skills": ["diagram"]},
    }

    with patch("services.routing_policy._embed_text", return_value=None):
        selected = select_member_ids(config, "please draft a report", member_configs)

    assert selected == ["reports"]


def test_select_member_ids_always_delegate_returns_all_members() -> None:
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "always_delegate",
    }

    selected = select_member_ids(config, None, {})

    assert selected == ["reports", "infographic"]


def test_select_member_ids_coordinated_rag_returns_all_members() -> None:
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "coordinated_rag",
    }

    selected = select_member_ids(config, "summarize sources", {})

    assert selected == ["reports", "infographic"]


def test_select_member_ids_delegate_on_complexity_matches_skills_case_insensitive() -> (
    None
):
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "delegate_on_complexity",
    }
    member_configs = {
        "reports": {"skills": ["Report"]},
        "infographic": {"skills": ["Diagram"]},
    }

    with patch("services.routing_policy._embed_text", return_value=None):
        selected = select_member_ids(config, "Please draft a REPORT", member_configs)

    assert selected == ["reports"]


def test_select_member_ids_unknown_mode_falls_back_to_all_members() -> None:
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "experimental_mode",
    }

    selected = select_member_ids(config, "any prompt", {})

    assert selected == ["reports", "infographic"]


def test_build_skill_text_combines_role_description_skills() -> None:
    config = {
        "role": "Data Analyst",
        "description": "Analyses datasets",
        "skills": ["statistics", "charts"],
    }
    text = _build_skill_text(config)
    assert "Data Analyst" in text
    assert "statistics" in text
    assert "charts" in text


def test_cosine_similarity_identical_vectors() -> None:
    v = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6


def test_cosine_similarity_orthogonal_vectors() -> None:
    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 1.0], dtype=np.float32)
    assert abs(_cosine_similarity(a, b)) < 1e-6


def test_select_member_ids_delegate_semantic_uses_embedding() -> None:
    """When _embed_text returns valid vectors, semantic scores determine winner."""
    config = {
        "members": ["analyst", "designer"],
        "coordination_mode": "delegate_on_complexity",
    }
    member_configs = {
        "analyst": {"skills": ["data analysis"], "role": "Analyst"},
        "designer": {"skills": ["visual design"], "role": "Designer"},
    }

    # analyst vector is close to prompt; designer is orthogonal
    prompt_vec = np.array([1.0, 0.0], dtype=np.float32)
    analyst_vec = np.array([0.9, 0.1], dtype=np.float32)
    designer_vec = np.array([0.0, 1.0], dtype=np.float32)

    skill_vecs = {
        "data analysis Analyst": analyst_vec,
        "visual design Designer": designer_vec,
    }

    def fake_embed(text: str):
        for key, vec in skill_vecs.items():
            if any(w in text for w in key.split()):
                return vec
        return prompt_vec

    with patch("services.routing_policy._embed_text", side_effect=fake_embed):
        selected = select_member_ids(config, "some prompt", member_configs)

    assert selected[0] == "analyst"
