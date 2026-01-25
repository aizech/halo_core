# AGENTS.md – Guide

Guidance for AI coding agents contributing to the HALO Core repository.

Prioritize critical thinking, verification, and evidence-driven changes. Treat tests and logs as the strongest signals. Every change should reduce entropy or improve clarity.

## User Priority
- User requests come first unless they conflict with system/developer rules.

## AGENTS.md Maintenance
- Treat this file as the highest-priority maintenance artifact.
- Update it when feedback reveals gaps or ambiguous rules.

## Readiness Checklist (Before Coding)
- For non-trivial work, create a short plan and keep it in sync; skip planning only for trivial edits.
- Read the relevant files first; do not rely on memory.
- If requirements are ambiguous after research, ask a single, specific question.

## Planning & Communication
- Use `update_plan` for multi-step work and mark steps complete as you go.
- Summarize changes with file references; keep responses concise.
- Update docs/ADRs when behavior or requirements change.

## Tool Discipline
- Prefer repo tools (`code_search`, `read_file`, `apply_patch`) over shell commands.
- Review diffs after edits; do not touch unrelated changes.

## Coding Standards
- Python formatted with **black**; lint with **ruff**.
- Use type hints on public interfaces.
- Fail fast with actionable errors (`st.error` when user-facing).
- Never hardcode secrets; use `.streamlit/secrets.toml` or env vars.

## Streamlit + Agno Practices
- Guard `st.session_state` mutations to avoid duplicate-key or default-value conflicts.
- Use Agno agents for chat/studio generation; keep templates data-driven in `/templates/studio_templates.json`.
- Keep UI changes minimal and consistent with existing layout conventions.

## Tests & Evidence
- For bug fixes, add a test that fails before the fix and passes after.
- For doc-only changes, skip tests but note manual verification if needed.

## Escalation Triggers
- Ask when behavior is ambiguous, when a design decision changes behavior, or when a workaround is required.
- Pause if unexpected files change; ask before proceeding.

## Git Practices
- Do not commit or stage unless the user explicitly asks.
- Keep diffs small and focused; avoid unrelated refactors.

## Documentation
- Update `HALO_CORE_PRD.md` for requirements changes.
- Add or update ADRs in `adr/` for architecture decisions.
- Keep README links accurate.

## End-of-Task Checklist
- Requirements satisfied
- Diffs are minimal and focused
- Tests updated or manual verification noted
- Docs updated when behavior changes
