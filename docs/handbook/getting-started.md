# Getting Started

This guide walks you through installing, configuring, and using HALO Core for the first time.

---

## Prerequisites

Before running HALO Core, make sure you have:

- **Python 3.10+** (3.11 recommended)
- **FFmpeg** — required for audio/video transcription
- **OpenAI API key** — for full AI features
- Optional: Node/npm for frontend tooling

---

## Installation

### 1. Create Virtual Environment

```bash
python -m venv .venv
. .venv/Scripts/activate        # Windows PowerShell
# or
source .venv/bin/activate       # Linux/macOS
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Secrets

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-..."
```

Additional optional keys:

```toml
# For memory backend
HALO_AGENT_DB = "sqlite:///data/memory.db"

# For custom data directory
HALO_DATA_DIR = "data"
```

---

## Running the App

```bash
streamlit run app/main.py
```

The app opens in your browser at `http://localhost:8501`.

---

## First-Use Flow

Follow these steps for your first successful workflow:

### Step 1: Add Sources

1. Open **Sources** panel (left column)
2. Click **+ Quellen hinzufügen**
3. Upload one or more files (PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, images, audio, video)
4. Wait for ingestion to complete

### Step 2: Select Sources

1. Mark sources via checkboxes
2. Or use "select all" for bulk selection

### Step 3: Ask a Question

1. Open **Chat** panel (center column)
2. Enter a prompt in the text input
3. Optionally attach an image or record audio
4. Press Enter or click Send

### Step 4: Review the Answer

- The response appears in the chat area
- Expand **Agent Actions** or **Tool Calls** for details
- Check source citations if applicable

### Step 5: Save as Note

1. Click **In Notiz speichern** below the response
2. The note appears in the Notes section

### Step 6: Generate Output

1. Open **Studio** panel (right column)
2. Choose a template (e.g., **Bericht**)
3. Click the generate button
4. Review the output in **Studio-Ergebnisse**

---

## Expected Result

You now have a complete source-to-output workflow:

1. ✅ Sources imported and selected
2. ✅ Question asked and answered
3. ✅ Answer saved as note
4. ✅ Structured output generated

---

## Account and Identity

There is no mandatory account sign-up in the UI:

- Default user identity is `local-user`
- Advanced users can set a custom `user_id` in configuration
- Memory backend enables persistent user memory across sessions

---

## Next Steps

- [Sources](sources.md) — Learn about source management
- [Chat](chat.md) — Deep dive into chat features
- [Studio](studio.md) — Explore output generation
- [Workflows](workflows.md) — Common task recipes
