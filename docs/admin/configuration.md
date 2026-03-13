# Configuration

System configuration for HALO Core administrators.

---

## Configuration Layers

HALO Core uses multiple configuration layers:

1. **Environment variables** — System-level settings
2. **Secrets file** — Sensitive credentials
3. **Application config** — User-configurable settings
4. **Agent configs** — Per-agent behavior

---

## Environment Variables

### Core Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `HALO_DATA_DIR` | Data storage directory | `data/` |
| `HALO_TEMPLATES_DIR` | Templates directory | `templates/` |
| `HALO_AGENT_DB` | Memory backend connection string | None |

### DICOM Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DICOM_ANONYMIZE_ON_UPLOAD` | Auto-anonymize DICOM on upload | `false` |
| `DICOM_PACS_HOST` | PACS server hostname | None |
| `DICOM_PACS_PORT` | PACS server port | None |
| `DICOM_PACS_AE_TITLE` | PACS Application Entity title | None |

### MCP Connector Credentials

| Variable | Description | Default |
|----------|-------------|---------|
| `NOTION_API_KEY` | Notion integration API key | None |
| `GOOGLE_OAUTH_CREDENTIALS` | Path to Google OAuth JSON | None |
| `MSAL_TENANT_ID` | Microsoft 365 tenant ID | None |
| `MSAL_CLIENT_ID` | Microsoft 365 client ID | None |
| `MSAL_CLIENT_SECRET` | Microsoft 365 client secret | None |

### Setting Environment Variables

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:HALO_DATA_DIR = "C:\data\halo"
```

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-..."
export HALO_DATA_DIR="/data/halo"
```

**Docker:**
```bash
docker run -e OPENAI_API_KEY=sk-... -e HALO_DATA_DIR=/data halo-core
```

---

## Secrets Management

### Secrets File Location

`.streamlit/secrets.toml`

### Format

```toml
# API Keys
OPENAI_API_KEY = "sk-..."

# Optional
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "AI..."

# Memory Backend
HALO_AGENT_DB = "sqlite:///data/memory.db"

# Custom Data Directory
HALO_DATA_DIR = "data"
```

### Security Best Practices

!!! warning
    Never commit `.streamlit/secrets.toml` to version control.

1. Add to `.gitignore`:
   ```
   .streamlit/secrets.toml
   ```

2. Use environment variables in production

3. Rotate API keys regularly

4. Restrict file permissions:
   ```bash
   chmod 600 .streamlit/secrets.toml
   ```

---

## Application Configuration

### Config File Location

`data/config.json` (or `{HALO_DATA_DIR}/config.json`)

### Structure

```json
{
  "app": {
    "theme": "light",
    "sidebar_width": {
      "collapsed": 60,
      "expanded": 250
    },
    "colors": {
      "background": "#ffffff",
      "text": "#16213e",
      "hover": "#00C2A8",
      "separator": "#e8e8e8"
    }
  },
  "chat": {
    "model": "gpt-4o-mini",
    "stream_events": true,
    "log_stream_events": false,
    "log_agent_payloads": false,
    "log_agent_responses": false,
    "log_agent_errors": true,
    "log_user_requests": true
  },
  "sources": {
    "image_model": "dall-e-3"
  },
  "studio": {
    "default_language": "de",
    "default_tone": "professional"
  }
}
```

### Configuration Categories

| Category | Settings |
|----------|----------|
| `app` | Theme, sidebar, colors, branding |
| `chat` | Model, streaming, logging |
| `sources` | Connectors, image model |
| `studio` | Template defaults |

---

## Agent Configuration

### Config Directory

`data/agents/` (or `{HALO_DATA_DIR}/agents/`)

### Agent Config Structure

```json
{
  "name": "researcher",
  "enabled": true,
  "role": "Research Specialist",
  "instructions": "You are a research specialist...",
  "skills": ["research", "analysis", "medical"],
  "tools": ["web_search", "calculator"],
  "mcp_servers": [],
  "coordination_mode": "delegate_on_complexity",
  "model": "gpt-4o",
  "stream_events": true,
  "markdown": true,
  "debug_mode": false
}
```

### Key Agent Settings

| Setting | Description |
|---------|-------------|
| `enabled` | Whether agent is active |
| `role` | Display name |
| `instructions` | System prompt |
| `skills` | Skills for delegation matching |
| `tools` | Enabled tool IDs |
| `mcp_servers` | Connected MCP servers |
| `coordination_mode` | Delegation behavior |
| `model` | AI model to use |
| `stream_events` | Enable event streaming |

---

## Presets Configuration

### Presets File

`presets.json` (project root)

### Structure

```json
{
  "presets": [
    {
      "name": "Quick Response",
      "model": "gpt-4o-mini",
      "tools": [],
      "members": [],
      "coordination_mode": "direct_only"
    },
    {
      "name": "Deep Analysis",
      "model": "gpt-4o",
      "tools": ["web_search", "calculator"],
      "members": ["researcher", "analyst"],
      "coordination_mode": "delegate_on_complexity"
    },
    {
      "name": "Team Research",
      "model": "gpt-4o",
      "tools": ["web_search"],
      "members": ["researcher", "writer", "analyst"],
      "coordination_mode": "always_delegate"
    }
  ]
}
```

---

## Studio Templates Configuration

### Templates File

`templates/studio_templates.json`

### Structure

```json
{
  "templates": [
    {
      "id": "report",
      "name": "Bericht",
      "description": "Structured written report",
      "output_format": "markdown",
      "default_language": "de",
      "default_tone": "professional"
    }
  ]
}
```

---

## Multi-Environment Setup

### Directory Structure

```
halo_core/
├── data-dev/          # Development data
├── data-staging/      # Staging data
├── data-prod/         # Production data
└── .streamlit/
    ├── secrets-dev.toml
    ├── secrets-staging.toml
    └── secrets-prod.toml
```

### Environment Switching

```bash
# Development
export HALO_DATA_DIR="data-dev"

# Staging
export HALO_DATA_DIR="data-staging"

# Production
export HALO_DATA_DIR="data-prod"
```

---

## Configuration Validation

### Check Configuration

Run validation tests:

```bash
pytest tests/test_agents_config.py -v
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Invalid JSON | Validate JSON syntax |
| Missing required field | Add missing field |
| Invalid coordination mode | Use valid mode name |
| Unknown tool ID | Check tool availability |

---

## Next Steps

- [User Management](user-management.md) — User identity setup
- [Security](security.md) — Secure configuration
- [Monitoring](monitoring.md) — Logging configuration
