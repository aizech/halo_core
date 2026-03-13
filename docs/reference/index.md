# Technical Reference

Developer documentation for HALO Core contributors and maintainers.

---

## Overview

This section provides technical documentation for:

- **Developers** contributing to the codebase
- **DevOps engineers** managing deployments
- **Maintainers** reviewing changes

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [Getting Started](getting-started.md) | Developer quickstart |
| [Repository Overview](repository-overview.md) | Codebase structure |
| [Architecture and Runtime](architecture-and-runtime.md) | System design |
| [Agent System](agent-system.md) | AI agent architecture |
| [Data Storage and Retrieval](data-storage-and-retrieval.md) | Data layer |
| [UI Panels and Pages](ui-panels-and-pages.md) | Frontend architecture |
| [Development, Testing, and Operations](development-testing-and-operations.md) | DevOps |

---

## Quick Reference

### Key Directories

```
halo_core/
├── app/           # Streamlit UI components
├── services/      # Backend services
├── data/          # Persistent data
├── templates/     # Studio templates
├── tests/         # Test suites
└── docs/          # Documentation
```

### Development Commands

```bash
# Run application
streamlit run app/main.py

# Run tests
pytest

# Lint and format
ruff check .
black .

# Build docs
mkdocs serve
```

### Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | Application entry point |
| `services/chat_runtime.py` | Chat orchestration |
| `services/agents.py` | Agent configuration |
| `services/knowledge.py` | Knowledge retrieval |
| `requirements.txt` | Dependencies |

---

## Contributing

See [AGENTS.md](https://github.com/aizech/halo_core/blob/main/AGENTS.md) for contribution guidelines.

---

Made with ❤️ by Corpus Analytica
