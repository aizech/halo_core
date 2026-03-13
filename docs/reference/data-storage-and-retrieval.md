# HALO Core Data Storage, Ingestion, and Retrieval

## 1) Storage model summary

HALO Core persists most runtime state in local JSON files plus LanceDB vectors.

Base location is `HALO_DATA_DIR` (default: `data/`).

Primary persisted assets:

- `sources.json`
- `studio_notes.json`
- `studio_outputs.json`
- `config.json`
- `connector_cache.json`
- `chat_history/<session_id>.json`
- `lancedb/` vector store

Optional: Agno memory DB via `HALO_AGENT_DB`.

## 2) JSON persistence layer (`services/storage.py`)

`services/storage.py` provides read/write helpers and ensures data directories exist.

### 2.1 Sources

- load: `load_sources()`
- save: `save_sources(sources)`

Used by source panel for displaying and maintaining selected source inventory.

### 2.2 Studio notes and outputs

- notes: `load_notes()` / `save_notes()`
- outputs: `load_studio_outputs()` / `save_studio_outputs()`

Studio output and note actions (rename, delete, promote, download) operate on these JSON-backed structures.

### 2.3 Chat history

- load: `load_chat_history(session_id)`
- save: `save_chat_history(session_id, history)`

Each chat session has its own JSON file under `chat_history/`.

### 2.4 UI config and connector cache

- config: `load_config()` / `save_config()`
- connector cache: `load_connector_cache()` / `save_connector_cache()`

Connector cache avoids unnecessary repeated fetches in non-refresh paths.

## 3) Source ingestion pipeline

The ingestion path is orchestrated by `services/ingestion.py`.

## 3.1 Upload payload extraction

`extract_document_payload(filename, data)` returns:

- `title`
- `type_label`
- `body`

`type_label` is inferred from extension via `infer_type_label()`.

## 3.2 Indexing flow

`ingest_source_content(title, body, meta)`:

1. calls `chunking.prepare_chunks(...)`
2. iterates chunk records
3. indexes each into retrieval with `retrieval.index_source_text(...)`

## 3.3 Directory ingestion helper

`load_directory_documents(directory)` recursively loads supported textual documents (excluding image/audio/video media paths).

## 4) Parser system (`services/parsers.py`)

`extract_text_from_bytes()` routes by extension.

### 4.1 Text and office formats

- text-like: direct decoding with utf-8/latin-1 fallback
- PDF: `pypdf.PdfReader`
- DOCX: `python-docx`
- CSV/XLSX/PPTX: Agno knowledge readers

### 4.2 Image parsing path

- if OpenAI key exists: image caption agent (`gpt-4o-mini`) describes image
- otherwise fallback text: `"Bilddatei: <filename>"`

### 4.3 Audio parsing path

- if OpenAI key exists: OpenAI transcription via `OpenAITools`
- otherwise fallback text: `"Audio-Datei: <filename>"`

### 4.4 Video parsing path

- extracts audio with `MoviePyVideoTools`
- transcribes extracted audio via OpenAI tools
- falls back to placeholder text when key unavailable

## 5) Chunking logic (`services/chunking.py`)

Core constants:

- `DEFAULT_CHUNK_SIZE = 500`
- `DEFAULT_CHUNK_OVERLAP = 75`

Pipeline:

1. normalize whitespace (`normalize_text`)
2. split into overlapping word windows (`chunk_text`)
3. enrich each chunk with metadata (`prepare_chunks`)

Metadata includes:

- `source_title`
- `type_label`
- `chunk_index`
- `chunk_count`
- any additional source metadata

## 6) Vector indexing and retrieval (`services/retrieval.py`)

## 6.1 Database structure

- LanceDB path: `<HALO_DATA_DIR>/lancedb`
- table name: `sources`

Each record stores:

- `text`
- `embedding`
- `meta` (includes `title` and source metadata)

## 6.2 Embedding behavior

`_embed(text)`:

- with OpenAI key: uses `text-embedding-3-small`
- without key: deterministic random embedding fallback (hash-seeded)

This allows local/offline behavior while preserving deterministic retrieval tests.

## 6.3 Query path

`query_similar(text, limit=5)`:

- computes query embedding
- cosine similarity search in LanceDB
- returns top matches with metadata

## 6.4 Source maintenance operations

- `delete_source_chunks(source_id, title=None)`:
  - delete by `meta.source_id`
  - fallback to `meta.title` when older rows lack source id

- `rename_source(source_id, new_title, previous_title=None)`:
  - preferred path uses LanceDB update by source id
  - fallback path rebuilds affected rows when needed

## 7) Knowledge abstraction (`services/knowledge.py`)

`get_agent_knowledge()` wraps LanceDB with native Agno Knowledge when possible.

Key behavior:

- requires OpenAI API key
- reuses same database/table as retrieval (`lancedb/sources`)
- on Windows, prefers vector search for stability over hybrid index mutation behavior
- if initialization fails, returns `None` and app falls back to manual retrieval

## 8) Source lifecycle end-to-end

1. Source added in UI (upload/search/connector/note/studio output)
2. Source metadata persisted in `sources.json`
3. Source body (if available) chunked and indexed in LanceDB
4. Chat retrieval queries top chunks for each prompt
5. Citation policy appends source references into final assistant response

## 9) Chat persistence lifecycle

1. Session ID initialized in app state
2. existing `chat_history/<session>.json` loaded (or welcome message used)
3. every appended message persisted to session history JSON
4. assistant messages may include:
   - serialized tool calls
   - structured trace/telemetry
   - image references

This allows full chat restoration on rerun.

## 10) Studio and notes lifecycle

### 10.1 Studio outputs

Generated output payload is normalized to include:

- `content`
- `sources`
- `generated_at`
- optional `image_path`

Persisted to `studio_outputs.json` and displayed in ordered section.

### 10.2 Notes

Notes can come from:

- chat response "save to note"
- all-sources summary pin
- manual note add dialog

Persisted in `studio_notes.json`, with actions for rename/delete/download/promote to source.

## 11) Connector data flow

Current connectors are mock abstractions in `services/connectors.py`.

Flow:

1. user selects connector slugs
2. cached results returned unless refresh requested
3. otherwise connector fetch runs and cache is updated
4. selected entries can be promoted into source list

Connector cache format is JSON and stored in `connector_cache.json`.

## 12) Operational considerations

### 12.1 Local data location

Use `HALO_DATA_DIR` to isolate data per environment (dev/test/staging).

### 12.2 Secret handling

- keep API keys in `.streamlit/secrets.toml` or environment variables
- do not commit secrets

### 12.3 OneDrive/Windows considerations

Repository and data paths under OneDrive can affect file locking/index operations.

Current mitigations include:

- safe temp-file cleanup retries in parsers
- vector search fallback in knowledge module on Windows

## 13) Backup and cleanup guidance

Recommended for operators:

1. Back up JSON files + `lancedb/` together.
2. Keep session history files if auditability matters.
3. If rebuilding index, keep `sources.json` and re-run ingestion/indexing path.
4. Validate retrieval quality after any index migration.

## 14) Known limitations

- Connector/web search are currently mock implementations.
- Embedding fallback without OpenAI key is deterministic but not semantically meaningful.
- Studio export formats beyond markdown are placeholder-quality in current implementation.

These are active areas for progressive hardening as tracked in backlog and internal PRDs.
