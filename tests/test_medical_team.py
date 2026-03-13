"""Tests for medical team agent configurations."""

import json
from pathlib import Path

import pytest

from services.agents_config import AgentConfig, load_agent_configs


class TestMedicalAgentConfigs:
    """Tests for medical AI agent configurations."""

    @pytest.fixture
    def agents_dir(self):
        """Path to agents directory."""
        return Path(__file__).parent.parent / "services" / "agents"

    @pytest.fixture
    def medical_agents(self, agents_dir):
        """List of medical agent config files."""
        medical_ids = [
            "chief_doctor",
            "radiologist",
            "cardiologist",
            "pharmacist",
            "medical_researcher",
            "medical_scribe",
            "medical_team",
        ]
        return {aid: agents_dir / f"{aid}.json" for aid in medical_ids}

    def test_medical_agent_files_exist(self, medical_agents):
        """All medical agent config files should exist."""
        for agent_id, path in medical_agents.items():
            assert path.exists(), f"Missing config file for {agent_id}"

    def test_medical_agent_configs_valid_json(self, medical_agents):
        """All medical agent configs should be valid JSON."""
        for agent_id, path in medical_agents.items():
            content = path.read_text(encoding="utf-8")
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {agent_id}: {e}")

    def test_medical_agent_configs_validate(self, medical_agents):
        """All medical agent configs should validate against AgentConfig."""
        for agent_id, path in medical_agents.items():
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
            try:
                config = AgentConfig(**data)
                assert config.id == agent_id
            except Exception as e:
                pytest.fail(f"Validation failed for {agent_id}: {e}")

    def test_chief_doctor_config(self, medical_agents):
        """Chief doctor config should have correct fields."""
        path = medical_agents["chief_doctor"]
        data = json.loads(path.read_text(encoding="utf-8"))
        config = AgentConfig(**data)

        assert config.type == "agent"
        assert "diagnosis" in config.skills
        assert "pubmed" in config.tools

    def test_radiologist_config(self, medical_agents):
        """Radiologist config should have correct fields."""
        path = medical_agents["radiologist"]
        data = json.loads(path.read_text(encoding="utf-8"))
        config = AgentConfig(**data)

        assert config.type == "agent"
        assert "imaging_interpretation" in config.skills

    def test_cardiologist_config(self, medical_agents):
        """Cardiologist config should have correct fields."""
        path = medical_agents["cardiologist"]
        data = json.loads(path.read_text(encoding="utf-8"))
        config = AgentConfig(**data)

        assert config.type == "agent"
        assert "cardiovascular_assessment" in config.skills

    def test_pharmacist_config(self, medical_agents):
        """Pharmacist config should have correct fields."""
        path = medical_agents["pharmacist"]
        data = json.loads(path.read_text(encoding="utf-8"))
        config = AgentConfig(**data)

        assert config.type == "agent"
        assert "drug_interactions" in config.skills

    def test_medical_researcher_config(self, medical_agents):
        """Medical researcher config should have correct fields."""
        path = medical_agents["medical_researcher"]
        data = json.loads(path.read_text(encoding="utf-8"))
        config = AgentConfig(**data)

        assert config.type == "agent"
        assert "systematic_review" in config.skills
        assert "pubmed" in config.tools

    def test_medical_scribe_config(self, medical_agents):
        """Medical scribe config should have correct fields."""
        path = medical_agents["medical_scribe"]
        data = json.loads(path.read_text(encoding="utf-8"))
        config = AgentConfig(**data)

        assert config.type == "agent"
        assert "clinical_documentation" in config.skills

    def test_medical_team_config(self, medical_agents):
        """Medical team config should have correct fields."""
        path = medical_agents["medical_team"]
        data = json.loads(path.read_text(encoding="utf-8"))
        config = AgentConfig(**data)

        assert config.type == "team"
        assert "chief_doctor" in config.members
        assert "radiologist" in config.members
        assert "cardiologist" in config.members
        assert "pharmacist" in config.members
        assert config.coordination_mode == "delegate_on_complexity"

    def test_medical_team_members_are_agents(self, medical_agents):
        """Medical team members should all be agent type."""
        team_path = medical_agents["medical_team"]
        team_data = json.loads(team_path.read_text(encoding="utf-8"))
        members = team_data.get("members", [])

        for member_id in members:
            member_path = medical_agents.get(member_id)
            if member_path and member_path.exists():
                member_data = json.loads(member_path.read_text(encoding="utf-8"))
                assert (
                    member_data.get("type") == "agent"
                ), f"Member {member_id} should be type 'agent'"

    def test_load_agent_configs_includes_medical(self):
        """load_agent_configs should include all medical agents."""
        configs = load_agent_configs()

        medical_ids = [
            "chief_doctor",
            "radiologist",
            "cardiologist",
            "pharmacist",
            "medical_researcher",
            "medical_scribe",
            "medical_team",
        ]

        for agent_id in medical_ids:
            assert agent_id in configs, f"Missing {agent_id} in loaded configs"


class TestMedicalTeamRouting:
    """Tests for medical team routing behavior."""

    def test_medical_team_has_coordination_mode(self):
        """Medical team should have coordination_mode set."""
        configs = load_agent_configs()
        team_config = configs.get("medical_team")

        assert team_config is not None
        assert team_config.get("coordination_mode") == "delegate_on_complexity"

    def test_medical_team_members_have_skills(self):
        """All medical team members should have skills defined."""
        configs = load_agent_configs()
        team_config = configs.get("medical_team")
        assert team_config is not None

        members = team_config.get("members", [])
        for member_id in members:
            member_config = configs.get(member_id)
            assert member_config is not None
            skills = member_config.get("skills", [])
            assert len(skills) > 0, f"Member {member_id} should have skills defined"


class TestMedicalStudioTemplates:
    """Tests for medical studio templates."""

    @pytest.fixture
    def templates_path(self):
        """Path to studio templates."""
        return Path(__file__).parent.parent / "templates" / "studio_templates.json"

    @pytest.fixture
    def templates(self, templates_path):
        """Load studio templates."""
        content = templates_path.read_text(encoding="utf-8")
        data = json.loads(content)
        return data.get("templates", [])

    def test_medical_templates_exist(self, templates):
        """Medical templates should exist."""
        medical_template_ids = [
            "medical_diagnosis",
            "clinical_case_report",
            "drug_interaction_check",
            "radiology_report",
            "evidence_summary",
            "treatment_protocol",
            "cardiac_risk_assessment",
        ]

        template_ids = {t.get("id") for t in templates}
        for tid in medical_template_ids:
            assert tid in template_ids, f"Missing medical template: {tid}"

    def test_medical_templates_have_team_binding(self, templates):
        """Medical templates should have team_id binding."""
        medical_templates = [
            t
            for t in templates
            if t.get("id")
            in {
                "medical_diagnosis",
                "clinical_case_report",
                "drug_interaction_check",
                "radiology_report",
                "evidence_summary",
                "treatment_protocol",
                "cardiac_risk_assessment",
            }
        ]

        for template in medical_templates:
            assert (
                template.get("team_id") == "medical_team"
            ), f"Template {template.get('id')} should bind to medical_team"

    def test_medical_templates_have_agent_binding(self, templates):
        """Medical templates should have agent_id binding."""
        expected_bindings = {
            "medical_diagnosis": "chief_doctor",
            "clinical_case_report": "medical_scribe",
            "drug_interaction_check": "pharmacist",
            "radiology_report": "radiologist",
            "evidence_summary": "medical_researcher",
            "treatment_protocol": "chief_doctor",
            "cardiac_risk_assessment": "cardiologist",
        }

        template_map = {t.get("id"): t for t in templates}

        for template_id, expected_agent in expected_bindings.items():
            template = template_map.get(template_id)
            assert template is not None, f"Missing template {template_id}"
            assert (
                template.get("agent_id") == expected_agent
            ), f"Template {template_id} should bind to agent {expected_agent}"
