# Troubleshooting

This guide helps you solve common problems in HALO Core.

---

## Chat and Responses

### Problem: "I get weak or generic answers"

**Possible causes:**

- No sources selected
- Source summary outdated
- Missing API key

**Try this:**

1. Confirm selected sources in Sources panel
2. Refresh all-sources summary
3. Verify `OPENAI_API_KEY` is configured in `.streamlit/secrets.toml`
4. Restart the app

---

### Problem: "Chat streaming fails"

**Possible causes:**

- API connectivity issue
- Model rate limit reached
- Temporary service issue

**Try this:**

1. Check error messages in the UI
2. Wait a moment and retry
3. Try a simpler prompt
4. Verify API key is valid

---

### Problem: "Responses don't cite sources"

**Possible causes:**

- Sources not properly indexed
- Query doesn't match source content
- Model not using retrieval

**Try this:**

1. Verify sources are selected
2. Check source summary for content
3. Make query more specific
4. Enable knowledge retrieval in agent config

---

## Sources and Files

### Problem: "My uploaded file fails to import"

**Possible causes:**

- Unsupported file extension
- Corrupted file
- Missing parsing dependency

**Try this:**

1. Check supported file types in [Sources](sources.md)
2. Try a smaller or simpler file
3. For audio/video, verify FFmpeg is installed
4. Check error message for details

---

### Problem: "Connector returns no results"

**Possible causes:**

- Connector not configured
- No matching content
- Authentication issue

**Try this:**

1. Verify connector credentials in Configuration
2. Check connector-specific settings
3. Test with different search terms

---

### Problem: "Source list is empty after upload"

**Possible causes:**

- Upload didn't complete
- Ingestion failed
- Data directory issue

**Try this:**

1. Check for error messages
2. Verify data directory is writable
3. Refresh the page
4. Check disk space

---

## Account and Memory

### Problem: "Account page says memory backend disabled"

**Cause:** Optional memory DB is not configured.

**Try this:**

1. Set `HALO_AGENT_DB` in environment:

   ```bash
   # Windows PowerShell
   $env:HALO_AGENT_DB = "sqlite:///data/memory.db"

   # Linux/macOS
   export HALO_AGENT_DB="sqlite:///data/memory.db"
   ```

2. Restart the app

---

### Problem: "Memory entries don't persist"

**Possible causes:**

- Memory backend not properly configured
- Database file not writable
- Session issue

**Try this:**

1. Verify `HALO_AGENT_DB` path exists
2. Check file permissions
3. Restart the app

---

## Configuration

### Problem: "Preset list is empty"

**Cause:** `presets.json` missing or invalid.

**Try this:**

1. Create `presets.json` in project root:

   ```json
   {
     "presets": [
       {
         "name": "Default",
         "model": "gpt-4o-mini",
         "tools": [],
         "members": []
       }
     ]
   }
   ```

2. Reopen Configuration → Chat

---

### Problem: "Configuration doesn't save"

**Possible causes:**

- File permissions issue
- Invalid value format
- Disk space issue

**Try this:**

1. Check file permissions on `data/` directory
2. Verify value formats are correct
3. Ensure disk space is available
4. Check for error messages

---

### Problem: "Changes don't take effect"

**Try this:**

1. Save the configuration explicitly
2. Refresh the app (press R)
3. Restart the app if necessary

---

## Studio and Outputs

### Problem: "No studio outputs generated"

**Possible causes:**

- No relevant source context
- Model/tool configuration issue
- API connectivity problem

**Try this:**

1. Confirm source selection
2. Test with Bericht template first
3. Check chat configuration
4. Verify API key

---

### Problem: "Output quality is poor"

**Possible causes:**

- Insufficient source context
- Vague extra prompt
- Wrong tone setting

**Try this:**

1. Add more relevant sources
2. Provide specific extra prompt instructions
3. Adjust tone setting
4. Try a different model

---

## Team and Agents

### Problem: "Team members not active"

**Possible causes:**

- Members disabled in agent config
- Coordination mode set to `direct_only`
- Prompt didn't match skills for delegation

**Try this:**

1. Open Agent Config page
2. Verify member `enabled` is true
3. Check `coordination_mode` setting
4. Inspect assistant trace in "Agent Actions"

---

### Problem: "Tool calls not displayed"

**Possible causes:**

- `stream_events` disabled
- Tools not configured for agent
- Display setting issue

**Try this:**

1. Verify `stream_events: true` in agent config
2. Verify tool IDs are configured
3. Enable stream debug logging

---

### Problem: "Knowledge retrieval fails"

**Possible causes:**

- LanceDB not initialized
- Sources not indexed
- Windows FTS lock issue

**Try this:**

1. Check `data/lancedb` directory exists
2. Verify sources are ingested
3. On Windows, vector search fallback should activate automatically
4. Check logs for errors

---

## Audio and Video

### Problem: "Audio transcription fails"

**Possible causes:**

- Missing FFmpeg
- Unsupported audio format
- API key issue

**Try this:**

1. Verify FFmpeg is in system PATH
2. Try a different audio format (MP3, WAV)
3. Check OpenAI API key

---

### Problem: "Video parsing issues"

**Possible causes:**

- Missing FFmpeg
- Large file size
- Unsupported format

**Try this:**

1. Verify FFmpeg installation
2. Try a smaller video file
3. Check supported formats

---

## Windows-Specific Issues

### Problem: "LanceDB WinError 5 (`_indices/fts`)"

**Cause:** Windows file locking on FTS index.

**Try this:**

1. Restart Streamlit
2. Move `HALO_DATA_DIR` outside heavily locked sync folders
3. Vector search fallback should activate automatically

---

## Getting Help

If problems persist:

1. Check logs for error details
2. Review [FAQ](faq.md) for common questions
3. Consult [Admin Guide](../admin/index.md) for system issues
4. Check GitHub issues for known problems
