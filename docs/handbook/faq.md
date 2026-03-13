# Frequently Asked Questions

Quick answers to common questions about HALO Core.

---

## General

### Q: Do I need an account to use HALO Core?

No mandatory signup is required in the default local setup. The app uses a local user identity (`local-user`) by default.

---

### Q: Where is my data stored?

By default, data is stored in local JSON files under the `data/` directory. You can change this with the `HALO_DATA_DIR` environment variable.

---

### Q: Is HALO Core free to use?

The application is open source. However, AI features require API keys (e.g., OpenAI) which have their own pricing.

---

### Q: Can I use HALO Core offline?

Basic functionality works offline, but AI chat features require API connectivity to your configured model provider.

---

## Sources

### Q: Can I use only one source?

Yes. You can select one or many sources per task. Select what's relevant for your current query.

---

### Q: What file types are supported?

Documents (PDF, DOCX, TXT, MD), spreadsheets (CSV, XLSX), presentations (PPTX), images (PNG, JPG, etc.), audio (MP3, WAV, etc.), and video (MP4, MOV, etc.).

---

### Q: How do I remove a source?

Click the source menu (⋮) and select Delete. Confirm the deletion.

---

## Chat

### Q: Can I change the AI model?

Yes. Use Configuration (Chat tab) to select a different model, or use Agent Config for detailed control.

---

### Q: Why are my answers generic?

Likely no sources are selected, or the source summary is outdated. Select relevant sources and refresh the summary.

---

### Q: Can I use images and audio in chat?

Yes. Chat input supports image uploads and audio capture/import for multimodal queries.

---

### Q: What if chat streaming fails?

The runtime has fallback behavior to still generate responses when possible. Check error messages and retry.

---

## Studio

### Q: What outputs can I generate?

Reports, infographics, podcast scripts, video scripts, presentations, and data tables.

---

### Q: Can I export generated outputs?

Yes. Outputs can be downloaded from the Studio-Ergebnisse section.

---

### Q: Why is my output quality poor?

Ensure you have relevant sources selected, provide specific extra prompts, and check your tone settings.

---

## Configuration

### Q: How do I reset menu/sidebar customization?

Use Configuration → App and reset sidebar menu settings, or manually edit the configuration.

---

### Q: Where are presets stored?

Presets are stored in `presets.json` in the project root.

---

### Q: Can I have multiple configurations?

You can use different `HALO_DATA_DIR` values for different environments (dev, staging, prod).

---

## Agents and Team

### Q: Can I control which tools an agent uses?

Yes. Use Agent Config to enable/disable specific tools per agent.

---

### Q: What are coordination modes?

Rules for how master and team agents collaborate:

| Mode | Behavior |
|------|----------|
| `direct_only` | Master answers directly |
| `delegate_on_complexity` | Delegates by skill match |
| `always_delegate` | Delegates to all members |
| `coordinated_rag` | Source-first RAG with delegation |

---

### Q: Why aren't team members responding?

Check that members are enabled, coordination mode allows delegation, and your prompt matches member skills.

---

## Memory

### Q: How do I enable persistent memory?

Set the `HALO_AGENT_DB` environment variable to a database path.

---

### Q: Where is memory stored?

Memory is stored in the database specified by `HALO_AGENT_DB`, or in JSON files if not configured.

---

### Q: How do I clear my memory?

Use the Account page to view and delete memory entries.

---

## Technical

### Q: What Python version do I need?

Python 3.10 or higher. Python 3.11 is recommended.

---

### Q: What dependencies are required?

See `requirements.txt` for the full list. Key dependencies include Streamlit, Agno, OpenAI SDK, and various parsing libraries.

---

### Q: How do I run tests?

```bash
pytest
```

Or for specific tests:

```bash
pytest tests/test_chat_runtime.py -v
```

---

### Q: How do I run the docs locally?

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000`.

---

## Deployment

### Q: Can I deploy HALO Core to the cloud?

Yes. Options include:

- Streamlit Cloud (demo hosting)
- Self-hosted Docker containers
- Cloud VMs with manual setup

---

### Q: Is every connector production-ready?

Not necessarily in this repository snapshot. Some connector flows are MVP/mock-oriented and may need extension for production use.

---

### Q: How do I secure my API keys?

Store keys in `.streamlit/secrets.toml` or environment variables. Never commit secrets to version control.

---

## More Help

- [Troubleshooting](troubleshooting.md) — Detailed problem-solving
- [Admin Guide](../admin/index.md) — System administration
- [GitHub Issues](https://github.com/aizech/halo_core/issues) — Report bugs
