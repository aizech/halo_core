# HALO Core Architecture and Runtime Flows

## 1) Architectural style

HALO Core follows a UI + service-layer split:

- `app/` handles Streamlit rendering and interaction wiring.
- `services/` handles orchestration, storage, ingestion, retrieval, routing, and agent behavior.

The current codebase is in an incremental migration state: some runtime logic still lives in `app/main.py`, while core chat orchestration has already been extracted into `services/chat_runtime.py`.

## 2) Runtime layers

## 2.1 Presentation layer
- `app/main.py`: primary 3-panel UI and sidebar
- `app/pages/*.py`: auxiliary Streamlit pages (Configuration, Agent Config, Dashboard, Account, Help)

## 2.2 Orchestration layer
- `services/chat_runtime.py`: chat-turn pipeline (payload, agent creation, stream handling, fallback, trace)
- `services/pipelines.py`: lightweight wrappers for chat/studio/infographic generation
- `services/agents.py`: core agent and team invocation logic

## 2.3 Agent/team coordination layer
- `services/halo_team.py`: team assembly from config
- `services/routing_policy.py`: deterministic member selection for coordination modes
- `services/agent_factory.py`: provider/model/tool factory functions
- `services/agents_config.py`: config schema, defaults, migration, persistence
- `services/presets.py`: preset application and chat config overrides

## 2.4 Data and retrieval layer
- `services/storage.py`: JSON persistence and optional agent DB initialization
- `services/ingestion.py`: source extraction + indexing bridge
- `services/parsers.py`: file-type-specific parsing/transcription/captioning
- `services/chunking.py`: text normalization/chunk segmentation
- `services/retrieval.py`: LanceDB indexing and similarity search
- `services/knowledge.py`: optional native Agno Knowledge wrapper over LanceDB

## 2.5 Streaming abstraction layer
- `services/streaming_adapter.py`: normalizes event names, deduplicates output, merges tool events, and enforces final response authority.

## 3) App startup flow

1. `run_app()` sets page configuration and renders sidebar.
2. `_init_state()` initializes session-state keys and loads persisted data:
   - session id
   - sources
   - chat history
   - notes
   - studio templates and outputs
   - app config
   - agent configs
3. Main content is rendered via three Streamlit columns:
   - `render_sources_panel()`
   - `render_chat_panel()`
   - `render_studio_panel()`

## 4) Source ingestion flow

### 4.1 Upload and document parsing
In Sources panel:

- user uploads one or more files
- each file is passed to `ingestion.extract_document_payload()`
- extraction delegates to `parsers.extract_text_from_bytes()`
- a source entry is created and persisted in JSON
- parsed body is chunked and indexed into LanceDB via `ingestion.ingest_source_content()` and `retrieval.index_source_text()`

### 4.2 Supported content paths
Parser behavior by extension:

- text-like: `.txt`, `.md`, `.csv`
- office docs: `.pdf`, `.docx`, `.xlsx`, `.pptx`
- image captioning path (if API key available): `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`
- audio transcription path: `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.opus`
- video transcription path: `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`

### 4.3 Connector and web search paths
- connectors are currently mock providers (`GoogleDriveConnector`, `NotionConnector`) cached in JSON
- web search in ingestion is currently a mock response set

## 5) Chat turn flow

Chat flow is intentionally split between UI and service orchestration.

### 5.1 UI responsibilities (`render_chat_panel`)
- render chat history and media attachments
- capture user input from `st.chat_input` (text, optional images, optional audio)
- persist user message
- create `ChatTurnInput`
- wire UI callbacks for streaming response and tool-call display
- append final assistant message to persisted history

### 5.2 Runtime responsibilities (`services/chat_runtime.py`)
`run_chat_turn()` pipeline:

1. `build_chat_payload()`
   - query retrieval contexts (`retrieval.query_similar`)
   - build payload text (`agents.build_chat_payload`)
2. `create_chat_agent()`
   - build team/agent from config (with prompt-aware fallback)
3. `stream_chat_response()`
   - stream normalized events via `stream_agent_response`
4. response handling
   - if stream is `None` or empty: fallback to `pipelines.generate_chat_reply`
   - apply citation policy
5. trace and telemetry
   - compose structured trace with model, members, tools, latency, knowledge hits/sources, stream outcome

## 6) Streaming behavior model

`stream_agent_response()` handles difficult stream cases:

- normalizes event names across possible event enum/string formats
- allows content only for known run/team events
- deduplicates team/member output overlap
- treats completed events as authoritative final output
- ignores post-final chunks to avoid corrupted response merges
- collects tool-call events into unique tool list

This behavior is validated by streaming-focused tests in `tests/test_streaming.py` and runtime tests in `tests/test_chat_runtime.py`.

## 7) Citation and grounding policy

Chat runtime applies a post-processing citation policy:

- single source: append one normalized citation (`[Quelle: ...]` + page when available)
- multiple sources: append a markdown `### Quellen` section with bulletized citations
- existing citation tags are cleaned/reduced for consistency

Page inference supports multiple metadata key names (`page`, `page_number`, `page_index`, `chunk_index`, etc.).

## 8) Studio generation flow

`render_studio_panel()` loads templates from `templates/studio_templates.json` and renders cards.

Card generation flow:

1. user presses template generate action
2. UI builds prompt from language/tone/instructions/user prompt
3. selected sources are passed to pipeline
4. for infographic template, dedicated image generation pipeline is used
5. output is normalized and persisted to `studio_outputs`
6. output appears in Studio results section, where it can be:
   - renamed
   - downloaded
   - deleted
   - promoted to source

Studio notes are managed separately in `studio_notes` and can also be promoted to source entries.

## 9) Persistence architecture

Persistence uses local files by default, under `HALO_DATA_DIR`:

- source catalog
- notes and studio outputs
- connector cache
- per-session chat history JSON files
- LanceDB vector store for retrieval

Optional persistent Agno DB memory is activated when `HALO_AGENT_DB` is configured.

## 10) Config-driven behavior

Configuration is data-driven in three major areas:

1. Agent configs (`data/agents/*.json`)
2. Studio template definitions (`templates/studio_templates.json`)
3. Chat presets (`presets.json`)

This allows many behavior changes without touching Python code.

## 11) Fallback and resilience behavior

The implementation includes multiple protective fallback paths:

- model construction returns `None` if provider/key unavailable
- team build falls back to single-agent mode
- stream failure or empty stream falls back to non-streaming generation
- parser functions return meaningful placeholders when API keys are absent for media understanding
- knowledge initialization failures degrade to manual retrieval path

## 12) Observability and trace model

Runtime traces combine base agent trace and chat telemetry envelope:

- model
- selected members
- tools
- stream mode/events/result
- latency (ms)
- knowledge hits and source names
- fallback usage flag

Traces are attached to assistant chat messages and rendered in UI under "Agent Actions".

## 13) Architectural constraints and near-term priorities

Current constraints:

- `app/main.py` remains large and still contains mixed concerns
- some connectors and search paths are mock/demo behavior
- studio export helpers are placeholder-level for PDF/slide output

Near-term direction (as already tracked in backlog/docs):

- continue extracting orchestration from `app/main.py`
- keep routing and stream handling deterministic and test-covered
- expand native Agno knowledge/memory usage while preserving safe fallback behavior
