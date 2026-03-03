# AGENTS.md

Guidance for AI coding agents in the HALO Core repository.

## Core Principles
- **Evidence-first**: All changes must be justified by tests, logs, or clear specification
- **Defend consistency**: Question deviations from established patterns
- **Reproduce bugs**: Always verify failures locally before fixing
- **Minimal diffs**: Prefer surgical edits; avoid unnecessary changes

## Commands

```bash
# Format & Lint
black .
ruff check .

# Type-check
mypy app services

# Test
pytest                     # Run all tests
pytest tests/<target>.py -v    # Single test file
pytest tests/<target>.py::test_func -v  # Single test function

# Run app
streamlit run app/main.py

# Audit dependencies
pip-audit -r requirements.txt
```

**Always run `black . && ruff check .` after code changes.**

## Python Standards

- Python >= 3.11
- Type hints mandatory for public interfaces; use `str | int | None` syntax
- Fail fast: `st.error` for user-facing, exceptions for service-layer
- Max file: 500 lines; max method: 100 lines (prefer 10-40)
- Prefer top-level imports
- No hardcoded paths in code or tests

## Streamlit + Agno Practices

- Guard `st.session_state` mutations to avoid conflicts
- Templates data-driven in `templates/studio_templates.json`
- Agent configs as JSON in `services/agents/`
- Persist sources/artifacts as JSON under `data/`; override with `HALO_DATA_DIR`

## Test Guidelines

- Use `pytest` with `tmp_path` for isolation
- Test behavior, not implementation
- Max 100 lines per test function
- Name descriptively for readability
- Files match service modules: `test_chunking.py` → `services/chunking.py`
- Unit tests: offline, minimal mocks
- For bug fixes: add test that fails before fix, passes after

## Workflow

1. Review `git diff` / `git diff --staged` for current state
2. Read relevant source files and tests before changes
3. Search for similar patterns globally
4. Make small focused changes, validate incrementally
5. Run relevant tests before completing

## Refactoring Rules

**Allowed**: Code movement, method extraction, renaming, file splitting

**Forbidden**: Logic/behavior changes, bug fixes (unless explicitly requested)

## Architecture

- `app/main.py` - Streamlit entrypoint
- `services/agents.py`, `services/agents_config.py` - Agno orchestration
- `services/retrieval.py` - RAG pipeline
- `services/ingestion.py`, `services/parsers.py`, `services/chunking.py` - Upload pipeline
- `services/storage.py` - Local/cloud storage
- `services/connectors.py` - API connectors (Drive, Notion, GitHub)
- `services/exports.py` - Artifact export
- `services/pipelines.py` - Studio generation pipelines
- `services/settings.py` - Configuration

## Secrets

- Credentials in `.streamlit/secrets.toml` or `.env`
- Never hardcode secrets in source

## Key References

- `HALO_CORE_PRD.md` - Product requirements
- `adr/` - Architectural Decision Records
- `templates/studio_templates.json` - Studio templates
- `services/agents/` - Agent configs

## End-of-Task Checklist

- [ ] All tests pass
- [ ] `black . && ruff check .` clean
- [ ] Minimal, precise diffs
- [ ] Documentation updated for behavior changes
- [ ] No regressions
