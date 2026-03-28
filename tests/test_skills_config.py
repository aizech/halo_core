"""Tests for skills configuration and skill_refs validation."""

import pytest
from pathlib import Path

from services.agents_config import load_agent_configs


@pytest.fixture
def skills_dir() -> Path:
    """Return path to skills directory."""
    return Path(__file__).parent.parent / "skills"


@pytest.fixture
def skills(skills_dir: Path) -> dict[str, Path]:
    """Return dict of skill_name -> skill_path for all skills."""
    if not skills_dir.exists():
        return {}
    return {
        d.name: d
        for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    }


@pytest.fixture
def agent_configs() -> dict:
    """Load all agent configs."""
    return load_agent_configs()


class TestSkillRefsValidation:
    """Tests for skill_refs in agent configurations."""

    def test_skills_directory_exists(self, skills_dir: Path) -> None:
        """Skills directory should exist."""
        assert skills_dir.exists(), f"Skills directory not found: {skills_dir}"

    def test_skills_exist(self, skills: dict) -> None:
        """At least one skill should exist."""
        assert len(skills) > 0, "No skills found"

    def test_all_skill_refs_point_to_existing_skills(
        self, agent_configs: dict, skills: dict
    ) -> None:
        """All skill_refs in agent configs should point to existing skills."""
        errors: list[str] = []

        for agent_id, config in agent_configs.items():
            skill_refs = config.get("skill_refs", [])
            for skill_ref in skill_refs:
                if skill_ref not in skills:
                    errors.append(
                        f"Agent '{agent_id}' references non-existent skill: '{skill_ref}'"
                    )

        assert not errors, "\n".join(errors)

    def test_each_skill_has_skill_md(self, skills: dict) -> None:
        """Each skill should have a SKILL.md file."""
        errors = []
        for skill_name, skill_path in skills.items():
            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                errors.append(f"Skill '{skill_name}' missing SKILL.md")
        assert not errors, "\n".join(errors)

    def test_medical_agents_have_skill_refs(self, agent_configs: dict) -> None:
        """Medical agents should have skill_refs configured."""
        medical_agents = [
            "chief_doctor",
            "radiologist",
            "pharmacist",
            "medical_researcher",
            "medical_scribe",
            "cardiologist",
            "medical_team",
        ]
        for agent_id in medical_agents:
            config = agent_configs.get(agent_id)
            if config:
                skill_refs = config.get("skill_refs", [])
                assert (
                    len(skill_refs) > 0
                ), f"Medical agent '{agent_id}' should have skill_refs"


class TestSkillMetadata:
    """Tests for skill metadata in SKILL.md files."""

    def test_skill_md_has_valid_frontmatter(self, skills: dict) -> None:
        """Each SKILL.md should have valid YAML frontmatter with name and description."""
        import re

        errors = []
        for skill_name, skill_path in skills.items():
            skill_md = skill_path / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")

            # Check for frontmatter
            if not content.startswith("---"):
                errors.append(f"Skill '{skill_name}' missing frontmatter")
                continue

            # Extract frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not frontmatter_match:
                errors.append(f"Skill '{skill_name}' has invalid frontmatter")
                continue

            frontmatter = frontmatter_match.group(1)

            # Check required fields
            if "name:" not in frontmatter:
                errors.append(f"Skill '{skill_name}' missing 'name' in frontmatter")
            if "description:" not in frontmatter:
                errors.append(
                    f"Skill '{skill_name}' missing 'description' in frontmatter"
                )

        assert not errors, "\n".join(errors)
