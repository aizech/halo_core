# Advanced Usage

This section covers advanced customization options for power users.

---

## Theme and Navigation Customization

### Colors

In Configuration → App, customize:

| Setting | Description |
|---------|-------------|
| Background | Main background color |
| Text | Primary text color |
| Hover | Hover state color |
| Separator | Divider line color |

### Icon and Font Sizes

- Adjust icon size for visibility
- Set base font size for readability

### Sidebar Width

- **Collapsed width**: Width when sidebar is minimized
- **Expanded width**: Width when sidebar is open

### Menu Entry Order

1. In Configuration → App, find menu settings
2. Drag entries to reorder
3. Add spacers and separators
4. Save configuration

### Entry Types

| Type | Purpose |
|------|---------|
| Link | Navigation to a page |
| Spacer | Vertical spacing |
| Separator | Horizontal divider |
| Theme toggle | Light/dark mode switch |

### Branding Assets

- **Light logo**: `assets/logo_light.png`
- **Dark logo**: `assets/logo_dark.png`
- **Light icon**: `assets/icon_light.png`
- **Dark icon**: `assets/icon_dark.png`

---

## Chat Presets

### What Presets Do

Presets bundle configuration for quick switching:

- Model selection
- Enabled tools
- Team members
- Other chat settings

### Using Presets

1. Open Configuration → Chat
2. Select a preset from dropdown
3. Settings apply immediately

### Creating Presets

Edit `presets.json`:

```json
{
  "presets": [
    {
      "name": "Quick Response",
      "model": "gpt-4o-mini",
      "tools": [],
      "members": []
    },
    {
      "name": "Deep Analysis",
      "model": "gpt-4o",
      "tools": ["web_search", "calculator"],
      "members": ["researcher", "analyst"]
    }
  ]
}
```

---

## Tool and Coordination Tuning

### Agent Configuration Access

1. Open Configuration
2. Click **Open Agent Config**
3. Select an agent to edit

### Tool Selection

Enable/disable tools per agent:

| Tool | Function |
|------|----------|
| Web search | Search the internet |
| Calculator | Perform calculations |
| File operations | Read/write files |
| Custom tools | Via MCP servers |

### MCP Servers

Model Context Protocol (MCP) servers provide additional tools:

1. In Agent Config, find MCP server list
2. Enable/disable servers
3. Configure server credentials

### Coordination Modes

| Mode | Behavior |
|------|----------|
| `direct_only` | Master agent answers directly |
| `delegate_on_complexity` | Delegates based on skills match |
| `always_delegate` | Delegates to all members |
| `coordinated_rag` | Source-first RAG with delegation |

### Stream Events

- **`stream_events`**: Enable event-rich streaming
- **`log_stream_events`**: Verbose event logging

---

## Storage and Runtime Environment

### Data Directory

Set `HALO_DATA_DIR` environment variable:

```bash
# Windows PowerShell
$env:HALO_DATA_DIR = "C:\data\halo"

# Linux/macOS
export HALO_DATA_DIR="/data/halo"
```

### Memory Backend

Set `HALO_AGENT_DB` for persistent memory:

```bash
$env:HALO_AGENT_DB = "sqlite:///data/memory.db"
```

When enabled:

- Agents use bounded history (`num_history_runs=3`)
- User memories persist across sessions
- Account page shows memory entries

### Templates Directory

Set `HALO_TEMPLATES_DIR` for custom templates:

```bash
$env:HALO_TEMPLATES_DIR = "custom_templates"
```

---

## Team Agent Setup

### Member Configuration

In Agent Config, for each member:

1. Set **enabled** state
2. Define **skills** (for delegation matching)
3. Configure **tools**
4. Write **role instructions**

### Skills Matching

When using `delegate_on_complexity`:

- Agent skills are matched against prompt
- Matching members receive delegation
- Non-matching members are skipped

### Example Skills

```json
{
  "skills": ["research", "analysis", "medical", "writing"]
}
```

---

## Knowledge and RAG

### Knowledge Base

- LanceDB stored in `data/lancedb`
- Automatic indexing of sources
- Vector search for retrieval

### Search Types

| Type | Description |
|------|-------------|
| Hybrid | Vector + full-text search |
| Vector | Vector similarity only |

!!! note
    On Windows, vector search is used to avoid hybrid/FTS index lock issues.

---

## Troubleshooting

### "Team members not active"

Check:

1. Member `enabled` is true
2. Coordination mode allows delegation
3. Skills match the prompt

### "Knowledge retrieval fails"

Check:

1. LanceDB directory exists
2. Sources are indexed
3. Check logs for errors

### "Custom settings don't apply"

Try:

1. Save configuration
2. Restart the app
3. Verify environment variables

---

## Next Steps

- [Workflows](workflows.md) — Apply advanced settings in practice
- [Admin Configuration](../admin/configuration.md) — System administration
