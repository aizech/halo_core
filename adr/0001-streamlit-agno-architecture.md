# ADR 0001 – Adopt Streamlit + Agno-Orchestrated Architecture

- **Status**: Accepted (2026-01-22)
- **Context**: The NotebookLM-style application must deliver a three-panel Streamlit UI, support rapid iteration, and integrate heterogeneous sources via MCP/system APIs while remaining model-agnostic. We need an orchestrator that can coordinate retrieval, agent tools, memory, and async workers without locking us into a single model vendor.
- **Decision**: Build the user interface with Streamlit and use the open-source [Agno](https://github.com/agno-agi/agno) platform as the orchestration layer for chat, Studio templates, ingestion workflows, and background processing. Streamlit provides fast development for multi-panel layouts and native multimodal inputs, while Agno supplies Memory, Knowledge, Async, and Tool abstractions plus model adapters.
- **Options Considered**:
  1. **Streamlit + Custom Orchestrator**: High flexibility but longer build time; would duplicate Agno features (memory stores, async tooling, agent composition).
  2. **Next.js + Hosted LLM Services**: Better control over branding/performance but slower to prototype, more boilerplate for stateful chat, and weaker alignment with team's Streamlit expertise.
  3. **Streamlit + Agno (Chosen)**: Leverages existing Streamlit knowledge and Agno’s batteries-included orchestration, keeping architecture model-agnostic.
- **Consequences**:
  - **Positive**: Rapid UI iterations, centralized agent logic, built-in async workers, simple swapping of OpenAI/Azure/local models, MCP compatibility, reusable memory/knowledge stores.
  - **Negative**: Streamlit layout constraints may need custom CSS; Agno adds dependency surface area and requires ops familiarity; tight coupling to Python stack.
- **Additional Notes (2026-02)**:
  - Persist chat history to JSON via `HALO_DATA_DIR` to ensure session restoration across reloads.
  - Introduce preset-driven chat configuration (model/tools/members) to keep agent orchestration data-driven.
  - Streaming response handling must de-duplicate team/member events and cumulative content chunks.
  - Mermaid diagrams are rendered from fenced code blocks and sanitized for multiline labels.
- **Implementation Notes**:
  - Scaffold project with `/app`, `/services`, `/data`, `/templates`, `/adr` directories.
  - Install Agno core modules (Memory, Knowledge, Async) plus selected LLM adapters during foundation phase.
  - Expose Agno run telemetry via built-in observability hooks for debugging.
  - Maintain a data-driven Studio template registry (`/templates/studio_templates.json`) that binds UI metadata to Agno agent configs for per-template orchestration.
  - Use a compact Streamlit card pattern: clickable header strips for generation, inline ⋯ menus for template configuration, and standardized download filenames for exports.
  - Keep orchestrator interfaces thin so future frameworks (Next.js frontend, FastAPI backend) could reuse Agno services if migration becomes necessary.
