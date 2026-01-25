# NotebookLM-Style Streamlit App PRD

## 1. Executive Summary
Build a Streamlit application that replicates Google NotebookLM's three-panel experience (Sources/"Quellen", Chat, Studio) with a productivity-focused sidebar for administration, configuration, account, and help utilities. Users curate heterogeneous sources, chat with an AI grounded in those sources, and generate structured studio artifacts. Emphasis on rapid source ingestion, multimodal insight generation, and template-driven exports.

## 2. Objectives & KPIs
- **Goals**
  1. Aggregate multiple document/audio/video/web sources into notebooks.
  2. Provide reference-backed conversational answers using selected sources.
  3. Offer Studio templates (summaries, briefs, quizzes, etc.) that can be exported or shared.
- **Success Metrics**
  - Time-to-first-answer after upload < 30s.
  - ≥90% of AI replies include at least one citation.
  - Studio artifact generation success rate ≥ 98%.
  - Sidebar admin actions discoverable within two clicks.

## 3. Personas
1. **Knowledge Synthesizer** — Consultants, researchers who summarize many files quickly.
2. **Content Creator** — Writers producing outlines, quizzes, scripts from curated sources.
3. **Team Reviewer** — Managers validating outputs, adjusting settings, monitoring usage.

## 4. User Journeys
1. **Source Collection**: Upload files or URLs → auto-extract metadata/transcripts → tag and organize.
2. **Insight Chat**: Select notebook → ask grounded questions → view citation-backed answers → save notes.
3. **Studio Output**: Choose template → configure parameters → generate artifact → export/share.
4. **Admin Sidebar**: Manage notebooks, billing, roles, API keys, and support from sidebar sections.

## 5. Feature Requirements
### 5.1 Global Layout
- **Sidebar**: Persistent menu with sections for Dashboard, Administration, Configuration, Account, Help/Docs, Feedback, plus theme toggle and logo.
- **Three Main Panels**:
  1. **Sources / Quellen**
     - Source list with metadata, type badges, validation status.
     - Actions: add sources, filter, select/deselect, quick web search, drag reorder.
     - Source detail drawer with preview, transcript, tags, delete/rename.
  2. **Chat**
     - Notebook header (title, source count, sharing button).
     - Streaming AI responses with citation chips, pin/copy/save note actions, quick prompts.
     - Input supporting text and file drop; model/token indicators.
  3. **Studio**
     - Card grid for templates (audio summary, report, mind map, quiz, infographic, data table, etc.).
     - Per-card generate/edit/export actions; history list with timestamps and linked sources.

### 5.2 Source Management
- Supported types: PDF, DOCX, TXT, Markdown, audio (mp3/wav), video (mp4), URLs.
- Automatic transcription for audio/video (Whisper/Fast-Whisper).
- Chunking + embeddings pipeline (OpenAI embeddings or FAISS fallback).
- Validations: file size limit, duplicate detection, optional virus scan hook.
- Version history per source.
- Multi-source ingestion modal consolidates uploads, URL capture, drive connectors, clipboard paste, and quick web search with configurable presets (e.g., "Web", "Drive", "Code Repo").
- System API connectors (Google Drive, Notion, SharePoint, Confluence, GitHub, etc.) managed centrally with OAuth token storage and scheduled sync jobs.
- MCP (Model Context Protocol) adapters allow invoking external tools with code execution (e.g., running notebooks, scraping scripts, data pipelines) to ingest derived artifacts back into Sources.
- Ingestion flow emits events so Studio and Chat can react to newly available content without reload.

### 5.3 Chat Engine
- System prompt built from notebook metadata and selected sources.
- Retrieval-augmented generation with top-k chunk citations.
- Tooling hooks (summarize_source, search_web, create_note).
- Session persistence per notebook; ability to fork conversations.
- Saved highlights convertible into Studio artifacts.
- "Save to Studio" action on every assistant response pushes the rendered text (and referenced sources) into the Studio "Notes" board where it can be edited, tagged, or repurposed in other templates.
- Streamlit chat input uses the latest `st.chat_input` multimodal capabilities (text, file upload, microphone capture) so users can dictate or attach reference files directly; content is automatically transcribed and routed through the same ingestion pipeline.

### 5.4 Studio Templates
- Template specification (JSON/YAML) defining inputs, prompts, output schema.
- Template registry backed by `/templates/studio_templates.json` so new templates can be added without code changes beyond the loader/renderer.
- Initial templates: Audio Summary, Video Summary, Reports, Quiz, Mind Map, Infographic, Data Table.
- Execution: gather sources → call LLM → render previews → export (Markdown/PDF/CSV/audio where applicable).
- Notes sub-module receives chat-saved entries, supports pinning to templates, and exposes API hooks so new Studio artifacts can be seeded from these notes.
- Each Studio card uses a compact, clickable header strip to trigger generation, with an inline ⋯ menu for template configuration (language, tone, instructions, optional user prompt).
- Studio artifacts (notes, audio podcasts, videos, infographics) offer a three-dot context menu with actions: promote item to a Notebook source, rename, download/export, share, and delete with confirmation + audit logging.
- Downloads use standardized filenames: `[YYYYMMDD]_<sanitized-title>.<ext>` to keep exports consistent and sortable.
- Studio generation must support **Agno agent pipelines** per template. Each template declares which Agno agent(s) or agent graph to run (e.g., research → outline → draft) along with agent instructions, tool access, and memory scope.
- Studio cards/actions are **data-driven**: a single config file (JSON/YAML) defines card metadata, inputs, action buttons, agent bindings, and export options. Adding a template should not require code changes outside the config loader/renderer.
- Provide a lightweight template registry that maps `template_id -> agent config -> UI schema` so per-template behavior is easy to manage and version.

### 5.5 Sidebar Modules
1. **Administration**: Usage stats, user roles, API keys, notebook inventory, audit log.
2. **Configuration**: Model selection, temperature, retrieval params, storage options, integration toggles, and per-tenant source provider controls (enable/disable Drive, Websites, MCP tools, code execution sandbox quotas).
3. **Account**: Profile, billing plan, limits, connected services.
4. **Help & Docs**: Onboarding checklist, FAQ, release notes, support contact form.

Admin area includes a "Source Providers" panel listing all ingestion connectors with status, credentials, scopes, rate limits, and MCP tool registration. Operators can map each connector to allowed notebooks, configure automated crawl cadence, and upload system API credentials.

### 5.6 Non-Functional
- Handle ≥50 MB per notebook, average answer latency <5 s with cached embeddings.
- RBAC, encrypted secrets, audit logging.
- Abstractions for storage/vector DB providers.
- Accessibility (WCAG AA) and localization (EN/DE labels such as "Quellen").
- Orchestration platform must remain model-agnostic using the open-source [Agno](https://github.com/agno-agi/agno) stack so we can hot-swap models (OpenAI, Azure OpenAI, local) without refactoring downstream logic.

### 5.7 Public Notebook Sharing & Consumption
- **Visibility Modes**: Private (default), Organization, Public. Public notebooks surface in a "Recommended" carousel with metadata (source count, publisher, updated date) similar to the reference screenshot.
- **Access Control**: Shareable links with slug + optional passcode; owner can revoke or downgrade visibility at any time. Public notebooks expose sources, notes, videos, podcasts, and studio artifacts as read-only.
- **Consumer Experience**: Visitors can chat with the notebook using the bundled source set but Studio panel is restricted to view-only previews (no editing/generation, except optionally re-run using owner's presets). Actions like copy/export prompt attribution reminders.
- **Engagement Features**: Follow/save public notebooks to personal library, show view counts, highlight "Last updated" badges, and allow feedback/emoji reactions.
- **Governance**: Moderation queue for public publishing, automated scans for PII/blocked content, logging of public access events.

## 6. Technical Architecture
1. **Frontend (Streamlit)**
   - Custom CSS for multi-panel layout via `st.columns`/`st.container`.
   - Session state for notebook selection, chat history, studio artifacts.
   - Reusable components for file uploads, drag/drop, collapsible cards.
2. **Backend Services**
   - Source pipeline: upload → storage (`/data` or cloud) → metadata DB (SQLite/Postgres) → embeddings/vector store.
   - Chat service: Retrieval-augmented LLM (LangChain or bespoke pipeline) with streaming responses.
   - Studio engine: Template definitions in `/app/templates` powering LLM prompts and renderers.
   - MCP controller: registers external tools, handles code execution requests (sandboxed) and streams results back into notebooks.
   - Connector services: wrappers for system APIs (Drive, GitHub, Confluence, etc.) with OAuth refresh, delta sync, and failure alerts.
   - **Agno Orchestration Layer**: Compose Memory, Knowledge, Async, and Tool agents to coordinate ingestion, chat, and Studio pipelines. Use Agno's model-agnostic adapters plus built-in observability to track runs.
3. **Data Layer**
   - SQLite/Postgres for metadata, FAISS/Pinecone/Azure Cognitive Search for vectors, object storage for raw files/exports.
   - Agno Memory stores (Redis/Postgres implementations) to persist long-term conversation context, per-notebook knowledge state, and async job metadata.
4. **Integrations**
   - OpenAI (chat, embeddings, TTS), optional Google Drive import, web search API, email/share services.
   - Public notebook CDN/storage for serving published assets (static hosting or signed URLs).
   - MCP servers (Onlyfy, custom data tools) and system API connectors for source ingestion and code execution.
   - Agno Async workers (Celery/RQ) for background transcription, crawling, and Studio generation tasks.
5. **Infrastructure**
   - Local dev via Streamlit CLI, production via Streamlit Cloud or container (Docker + Azure Web App).
   - Secrets via `.streamlit/secrets.toml`.
   - CI pipeline (GitHub Actions) for lint (ruff/black), tests (pytest), type checks (mypy).

## 7. Implementation Roadmap
1. **Foundation**
   - Initialize repo structure (`app/`, `services/`, `data/`, `templates/`, `tests/`).
   - Configure virtual env, requirements, and `.streamlit/config.toml` theme.
   - Install and configure Agno core (Memory, Knowledge, Async modules) plus adapters for selected LLMs.
2. **MVP**
   - Skeleton UI with sidebar + placeholder panels.
   - Notebook & source CRUD (local storage + metadata DB).
   - Retrieval-grounded chat for text uploads leveraging Agno Memory to persist conversations.
   - Single Studio template (summary) exporting to Markdown.
3. **Feature Expansion**
   - Add audio/video transcription, URL scraping, multiple Studio templates.
   - Build admin sidebar modules and localization.
   - Implement template framework + export formats (PDF/CSV).
   - Launch public notebook sharing (recommendations feed, link-based access, studio read-only mode).
4. **Hardening**
   - Authentication/authorization, permissions, sharing links.
   - Monitoring/logging, caching, automated tests.
5. **Launch Readiness**
   - Populate help content, finalize UX polish, QA, performance profiling, deployment scripts.

## 8. Backlog Ideas
- Live collaboration with real-time presence.
- Co-editing and comments on sources/studio outputs.
- Audio playback + TTS for generated summaries.
- Plugin marketplace for custom templates.
- Mobile-optimized layout variants.

## 9. Risks & Mitigations
| Risk | Mitigation |
| --- | --- |
| LLM hallucination | Enforce citation chips, show confidence scores, enable "view source snippet" modal. |
| Large file handling | Streaming uploads, background processing queue, chunk status feedback. |
| Vendor lock-in | Abstract model & vector providers behind interfaces for swapability. |
| Streamlit layout constraints | Custom CSS + component wrappers to mimic NotebookLM while staying responsive. |

## 10. Next Steps
1. Confirm MVP scope for Studio templates and data providers.
2. Baseline `requirements.txt` and Streamlit skeleton in repo.
3. Schedule visual design pass to match NotebookLM aesthetics.
4. Create sprint backlog/issues per roadmap milestones.
