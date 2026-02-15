# HALO Core Documentation Content Overview

This folder contains practical, code-aligned documentation for the current `halo_core` repository.

## Documentation map

1. [Repository Overview](./REPOSITORY_OVERVIEW.md)
   - High-level project purpose, stack, structure, and entry points.
   - Read this first if you are new to the codebase.

2. [Architecture and Runtime Flows](./ARCHITECTURE_AND_RUNTIME.md)
   - End-to-end request/response flows for Sources, Chat, and Studio.
   - Describes service boundaries, fallback behavior, and runtime traces.

3. [UI Panels and Pages](./UI_PANELS_AND_PAGES.md)
   - Streamlit layout, sidebar navigation, page responsibilities, and key UI behaviors.
   - Useful when changing UX and app state handling.

4. [Agent System and Configuration](./AGENT_SYSTEM.md)
   - Agent config schema, team delegation behavior, presets, tools, and streaming event handling.
   - Primary reference for agent/preset changes.

5. [Data Storage, Ingestion, and Retrieval](./DATA_STORAGE_AND_RETRIEVAL.md)
   - Source ingestion pipeline, parser behavior, chunking, LanceDB indexing/querying, and JSON persistence.
   - Primary reference for RAG and data lifecycle work.

6. [Development, Testing, and Operations](./DEVELOPMENT_TESTING_AND_OPERATIONS.md)
   - Setup, local run, test strategy, quality gates, and troubleshooting.
   - Primary reference for contributors and release readiness.

## Suggested reading paths

### A) New contributor onboarding
1. Repository Overview
2. Architecture and Runtime Flows
3. Development, Testing, and Operations

### B) Feature work on Chat / agents
1. Agent System and Configuration
2. Architecture and Runtime Flows
3. UI Panels and Pages

### C) Feature work on source ingestion / RAG
1. Data Storage, Ingestion, and Retrieval
2. Architecture and Runtime Flows
3. Development, Testing, and Operations

### D) UI/UX changes
1. UI Panels and Pages
2. Architecture and Runtime Flows
3. Repository Overview

## Canonical product and decision documents

- Product requirements (internal): `docs_internal/HALO_CORE_PRD.md`
- Chat integration PRD (internal): `docs_internal/HALO_CHAT_INTEGRATION_PRD.md`
- Agent config integration plan (internal): `docs_internal/AGENT_CONFIG_INTEGRATION_PLAN.md`
- Architecture decision record: `adr/0001-streamlit-agno-architecture.md`

## Scope notes

- These docs describe the **current implementation state** in this repository.
- Roadmap and aspirational capabilities are tracked in PRD/plan documents under `docs_internal/` and backlog files.
