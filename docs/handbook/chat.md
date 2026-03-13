# Chat

The Chat panel is where you interact with the AI assistant using your selected sources.

---

## What It Does

- Ask text questions grounded in your sources
- Attach images for multimodal analysis
- Record or upload audio for transcription
- View tool calls and agent actions
- Save responses as notes

---

## Why It Matters

Chat is the primary interface for turning your source content into insights. Grounded responses are more trustworthy because they cite your actual documents.

---

## Chat Interface

### Input Area

- **Text input**: Type your question or prompt
- **Image upload**: Attach images for analysis
- **Audio input**: Record or upload audio for transcription

### Response Area

- **Main response**: AI-generated answer
- **Source section**: Citations from selected sources
- **Expandable sections**: Agent Actions, Tool Calls, Agent Thinking

---

## Asking Questions

### Basic Flow

1. Select sources in the Sources panel
2. In Chat, enter your prompt
3. Press Enter or click Send
4. Review the response

### Expected Results

- Response appears in the chat area
- Source citations are included when applicable
- Tool calls show if tools were used

---

## Multimodal Input

### Images

1. Click the image icon in the input area
2. Upload an image file
3. Enter a prompt about the image
4. Send

**Use cases:**

- Analyze charts or diagrams
- Extract text from screenshots
- Describe visual content

### Audio

1. Click the audio icon in the input area
2. Record audio or upload an audio file
3. Audio is transcribed to text
4. Edit the transcribed prompt if needed
5. Send

**Use cases:**

- Voice notes as prompts
- Transcribe meetings or lectures
- Hands-free input

---

## Summary of All Sources

### What It Does

Creates a unified summary of all sources in your library.

### How to Use

1. In the chat panel, open **Zusammenfassung aller Quellen**
2. Click the refresh icon to generate/update
3. Optionally pin the summary to notes

### Expected Results

- Summary content is displayed
- Stale indicator appears when source set has changed
- You can save summary as a note for later reuse

---

## Understanding Responses

### Source Citations

When sources are selected, responses may include:

- Source names referenced
- Relevant excerpts quoted
- Links to source documents

### Agent Actions

Expand this section to see:

- Which agent(s) were involved
- Delegation decisions
- Reasoning flow

### Tool Calls

Expand this section to see:

- Tools used (e.g., web search, calculator)
- Input parameters
- Results returned

### Agent Thinking

Expand this section to see:

- Internal reasoning steps
- Decision points
- Confidence indicators

---

## Saving Responses

### Save as Note

1. Below a response, click **In Notiz speichern**
2. Note is saved to the Notes section
3. Note can be reused as a source

### Why Save

- Preserve important findings
- Build a knowledge base
- Reuse content in future queries

---

## Chat History

- Previous conversations are stored in `data/chat_history/`
- History persists across sessions
- Each session maintains its own context

---

## Troubleshooting

### "I get weak or generic answers"

Possible causes:

- No sources selected
- Source summary outdated
- Missing API key

Try this:

1. Confirm selected sources in Sources panel
2. Refresh all-sources summary
3. Verify `OPENAI_API_KEY` is configured

### "Chat streaming fails"

HALO has fallback behavior to still generate responses when possible.

Try this:

1. Check error messages in the UI
2. Verify API connectivity
3. Try a simpler prompt

### "Audio transcription fails"

Possible causes:

- Missing FFmpeg
- Unsupported audio format
- API key issue

Try this:

1. Verify FFmpeg is in PATH
2. Try a different audio format
3. Check OpenAI API key

---

## Next Steps

- [Studio](studio.md) — Generate structured outputs
- [Notes](notes.md) — Manage saved responses
- [Advanced Usage](advanced.md) — Customize chat behavior
