# HALO Core Skills

This directory contains Agno Skills that extend agent capabilities with domain-specific expertise.

## What are Skills?

Skills provide agents with structured domain expertise through:
- **Instructions**: Detailed guidance on when and how to apply the skill
- **Scripts**: Optional executable code templates
- **References**: Supporting documentation

Skills use lazy loading - agents only load skill instructions when needed, saving tokens.

## Adding a New Skill

### 1. Create Skill Directory

```bash
mkdir skills/<skill-name>
```

### 2. Create SKILL.md

```markdown
---
name: <skill-name>
description: Brief description of what this skill does
metadata:
  version: "1.0.0"
  author: "HALO Core"
  tags: ["tag1", "tag2"]
---

# Skill Title

Use this skill when [scenario].

## When to Use

- Scenario A
- Scenario B

## Process

1. Step one
2. Step two
3. Step three

## Best Practices

- Practice A
- Practice B
```

### 3. Add skill_refs to Agent Config

Edit `services/agents/<agent>.json`:

```json
{
  "skill_refs": ["<skill-name>"]
}
```

### 4. Verify

Run the skill validation test:

```bash
pytest tests/test_skills_config.py -v
```

## Skill Structure

```
skills/
├── SKILL.md           # Required: Instructions with YAML frontmatter
├── scripts/           # Optional: Executable scripts
│   └── helper.py
└── references/       # Optional: Supporting documentation
    └── guide.md
```

## Available Skills

| Skill | Description | Agents |
|-------|-------------|--------|
| medical-diagnosis | Diagnostic reasoning, differential diagnosis | chief_doctor, cardiologist |
| medical-imaging | Radiology interpretation, DICOM analysis | radiologist |
| pharmacology | Drug interactions, dosing, medication safety | pharmacist |
| clinical-reasoning | Evidence-based clinical decision making | chief_doctor, medical_researcher |
| medical-documentation | SOAP notes, case reports, clinical notes | medical_scribe |
| research-synthesis | Literature review, evidence grading | medical_researcher |
| team-coordination | Multi-agent coordination, task delegation | medical_team, general_team, marketing_team |
| web-research | Web search, fact-checking, source verification | web_researcher |
| summarization | Text condensation, key point extraction | summarizer |
| note-taking | Information organization, structured notes | note_taker |
| data-analysis | Statistics, quantitative reasoning | data_analyst |
| content-creation | Blog writing, copywriting, content strategy | content_writer |
| seo-optimization | Keyword research, content optimization | seo_optimizer |
| general-assistance | Task coordination, practical help | general_assistant |

## Testing Skills

Run skill validation tests:

```bash
# All skill tests
pytest tests/test_skills_config.py -v

# Specific test
pytest tests/test_skills_config.py::TestSkillRefsValidation::test_all_skill_refs_point_to_existing_skills -v
```

## References

- [Agno Skills Documentation](https://docs.agno.com/basics/skills/overview)
- [Creating Skills Guide](https://docs.agno.com/basics/skills/creating-skills)
