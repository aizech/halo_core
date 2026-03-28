# HALO Core Documentation

Welcome to the HALO Core documentation. HALO (**Holistic Agent Logical Orchestrator**) Core is an intelligence workspace for teams that need to turn raw information into clear, usable outputs.

---

## Quick Links

| Audience | Documentation |
|----------|---------------|
| **End Users** | [User Handbook](handbook/index.md) |
| **Administrators** | [Admin Guide](admin/index.md) |
| **Developers** | [Technical Reference](reference/index.md) |

---

## What HALO Core Does

- **Collect sources** — files, web findings, connector results
- **Ask questions** — source-grounded AI chat
- **Generate outputs** — reports, infographics, podcasts, presentations
- **Save insights** — reusable notes from your work

---

## Documentation Sections

### User Handbook

Complete guide for end users:

- [Getting Started](handbook/getting-started.md) — Installation and first steps
- [Sources](handbook/sources.md) — Managing your content library
- [Chat](handbook/chat.md) — AI conversations and multimodal input
- [Studio](handbook/studio.md) — Generating outputs from templates
- [Workflows](handbook/workflows.md) — Common task recipes
- [Troubleshooting](handbook/troubleshooting.md) — Solving problems
- [FAQ](handbook/faq.md) — Quick answers
- [Glossary](handbook/glossary.md) — Terms and definitions

### Admin Guide

System administration documentation:

- [Deployment](admin/deployment.md) — Infrastructure and deployment options
- [Configuration](admin/configuration.md) — System configuration
- [User Management](admin/user-management.md) — Identity and memory
- [Security](admin/security.md) — Security and compliance
- [Monitoring](admin/monitoring.md) — Logging and observability
- [Maintenance](admin/maintenance.md) — Backup and updates

### Technical Reference

Developer documentation:

- [Overview](reference/index.md) — Technical reference home
- [Getting Started](reference/getting-started.md) — Developer quickstart
- [Repository Overview](reference/repository-overview.md) — Codebase structure
- [Architecture and Runtime](reference/architecture-and-runtime.md) — System design
- [Agent System](reference/agent-system.md) — AI agent architecture
- [Data Storage and Retrieval](reference/data-storage-and-retrieval.md) — Data layer
- [UI Panels and Pages](reference/ui-panels-and-pages.md) — Frontend architecture
- [Development, Testing, and Operations](reference/development-testing-and-operations.md) — DevOps

### Skills

HALO Core uses Agno Skills for domain-specific agent capabilities:

- [Skills Guide](../skills/README.md) — How to create and use skills
- 15+ pre-built skills for medical, research, marketing, and general tasks

---

## Key Features

### Team-Based AI Collaboration

Run specialized AI agents with different roles, instructions, and tools.

### Smart Delegation

Multiple coordination modes: direct, skill-based delegation, or team-wide collaboration.

### Source-Grounded Responses

Answers are grounded in your selected documents with citations.

### Transparent Execution

Inspect tool calls, agent actions, and reasoning traces.

### Studio Pipeline

Generate reports, presentations, podcasts, and more from your research context.

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/aizech/halo_core.git
cd halo_core
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt

# Configure API key
echo 'OPENAI_API_KEY = "sk-..."' > .streamlit/secrets.toml

# Run
streamlit run app/main.py
```

---

## Resources

- [Changelog](changelog.md) — Version history and changes
- [GitHub Repository](https://github.com/aizech/halo_core)
- [Live Demo](https://halocore.streamlit.app/)
- [Corpus Analytica](https://www.corpusanalytica.com/)

---

Made with ❤️ by Corpus Analytica
