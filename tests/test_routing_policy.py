from __future__ import annotations

from services.routing_policy import select_member_ids


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


def test_select_member_ids_delegate_on_complexity_matches_skills_case_insensitive() -> None:
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "delegate_on_complexity",
    }
    member_configs = {
        "reports": {"skills": ["Report"]},
        "infographic": {"skills": ["Diagram"]},
    }

    selected = select_member_ids(config, "Please draft a REPORT", member_configs)

    assert selected == ["reports"]


def test_select_member_ids_unknown_mode_falls_back_to_all_members() -> None:
    config = {
        "members": ["reports", "infographic"],
        "coordination_mode": "experimental_mode",
    }

    selected = select_member_ids(config, "any prompt", {})

    assert selected == ["reports", "infographic"]
