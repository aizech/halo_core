# AGENTS.md – Windsurf Cascade Collaboration Guide

This document defines how human collaborators and Cascade-based agents work together when developing the NotebookLM-style Streamlit application inside `halo_core`.

## 1. Operating Principles
1. **Source of Truth**: Requirements live in `NOTEBOOKLM_PRD.md` and ADRs. Agents must reference the PRD before starting major work.
2. **Small, Reviewable Changes**: Favor incremental pull requests with descriptive commits (see `MEMORY[user_global]` guidelines). Avoid mixing unrelated fixes.
3. **Tool Discipline**: Prefer IDE-native tools (`code_search`, `read_file`, `apply_patch`, etc.) over shell commands when possible.
4. **Deterministic Builds**: Always update `requirements.txt`/lock files when adding dependencies. Document environment assumptions in README/ADR.
5. **Telemetry & Logging**: Instrument new services with clear logs; don’t leave print/debug clutter in committed code.

## 2. Planning & Communication
1. **Plan First**: Before coding, outline steps via `update_plan` unless the change is trivial (<15 lines, no branching logic).
2. **Checkpointing**: After completing each plan step, mark it complete and briefly describe results.
3. **Assumption Callouts**: If a requirement is ambiguous, stop and clarify via comments or follow-up tasks rather than guessing.
4. **Documentation Updates**: Any functional change must include relevant updates to docs, ADRs, or inline comments (only when logic is non-obvious).

## 3. Coding Standards
1. **Style**: Follow repo conventions—Python code formatted with `ruff`/`black`, descriptive naming, minimal side effects.
2. **Modularity**: Encapsulate complex logic in functions/classes; avoid long monolithic scripts.
3. **Error Handling**: Fail fast with explicit exceptions or `st.error` messages; include actionable guidance.
4. **Testing**: Add or update unit/integration tests for non-trivial changes. Prefer deterministic fixtures over network calls.
5. **Secrets**: Never hardcode API keys. Use `.streamlit/secrets.toml` or env vars; document required keys.

## 4. Streamlit + Agno Best Practices
1. **State Management**: Use `st.session_state` guards to avoid mutation-after-render errors. Encapsulate state resets in helpers.
2. **Asynchronous Tasks**: Offload long-running ingestion/transcription to Agno Async workers; surface job status in UI.
3. **MCP & Connectors**: Wrap external APIs in reusable service modules; handle pagination, retries, and rate limits uniformly.
4. **Multimodal Chat**: Use the latest `st.chat_input` for text/file/voice. Store artifacts in the ingestion pipeline for reuse.
5. **Studio Templates**: Define template metadata (prompt, inputs, permissions) in `/templates`. Respect customization presets and admin locks.

## 5. Git Workflow & CI/CD
1. **Branch Strategy**: `main` (stable), `develop` (integration), feature branches named `feature/<issue-id>-<summary>`, and hotfix branches `hotfix/<summary>`. Rebase on `develop` before opening a PR; never commit directly to `main`.
2. **Pull Requests**: Require descriptive titles, linked issues, and at least one reviewer. PRs must include screenshots or logs for UI/infra changes. Enable GitHub’s "Allow auto-merge" only after checks pass.
3. **Release Cadence**: Tag semantic versions (`vX.Y.Z`) from `main`. Generate release notes automatically via GitHub Releases pulling PR summaries.
4. **GitHub Actions Pipeline**:
   - `ci.yml`: matrix build (Python versions) running `ruff`, `black --check`, `pytest`, and type checks (`mypy`). Cache `.venv`/pip, fail fast on lint violations.
   - `build.yml`: package Streamlit app into Docker image, run security scans (Trivy/Bandit), push to registry when `main` tagged.
   - `deploy.yml`: triggered on release publish; pulls image, runs migrations, posts status to Slack/Teams.
   - Required checks enforced via branch protection; secrets injected through GitHub Environments.
5. **Maintenance Automation**: Enable Dependabot for Python deps and GitHub Actions versions; stale-issue workflow closes inactive tickets after warning commenters.

## 6. Review & Merging
1. **CI First**: Ensure lint/tests pass locally before submitting. Attach logs if CI failures are expected (e.g., missing secrets).
2. **Peer Review Checklist**:
   - Requirements satisfied?
   - Tests/docs updated?
   - No secrets or personal data committed?
   - Performance implications considered?
3. **Commit Format**: Use `prefix: summary` (see global memory rules). Reference issue IDs when available.

## 7. Incident Response
1. **Bug Priority**: Critical regressions in ingestion/chat/studio pipelines get hotfix branches with targeted commits.
2. **Postmortem Notes**: Document significant incidents (data loss, downtime) in `/doc/incidents` or an ADR update.
3. **Rollbacks**: Prefer reverting offending commits rather than patching over unknown states.

## 8. Collaboration Etiquette
1. **Respect Ownership**: When editing another agent’s work-in-progress, coordinate via comments or assign the task explicitly.
2. **Traceability**: Reference task IDs or PR links in comments/commits for future auditing.
3. **Knowledge Sharing**: Capture new learnings (e.g., API quirks, deployment tips) in `README.md` or additional ADRs.

Adhering to these rules keeps Cascade agents predictable, auditable, and aligned with the NotebookLM clone roadmap.
