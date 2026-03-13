# Admin Guide

Welcome to the HALO Core Admin Guide. This documentation covers deployment, configuration, user management, security, monitoring, and maintenance for system administrators.

---

## Who This Guide Is For

This guide is intended for:

- System administrators deploying HALO Core
- DevOps engineers managing infrastructure
- Security officers reviewing compliance
- IT staff supporting users

---

## Guide Overview

| Section | Description |
|---------|-------------|
| [Deployment](deployment.md) | Infrastructure setup and deployment options |
| [Configuration](configuration.md) | System configuration and environment setup |
| [User Management](user-management.md) | User identity and memory management |
| [Security](security.md) | Security practices and compliance |
| [Monitoring](monitoring.md) | Logging, observability, and diagnostics |
| [Maintenance](maintenance.md) | Backup, updates, and migrations |

---

## Quick Reference

### Essential Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API authentication |
| `HALO_DATA_DIR` | No | Custom data directory |
| `HALO_AGENT_DB` | No | Memory backend database |
| `HALO_TEMPLATES_DIR` | No | Custom templates directory |

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `data/` | Persistent workspace data |
| `data/chat_history/` | Conversation logs |
| `data/lancedb/` | Vector database |
| `data/agents/` | Agent configurations |
| `.streamlit/` | Streamlit configuration |

### Key Files

| File | Purpose |
|------|---------|
| `.streamlit/secrets.toml` | API keys and secrets |
| `config.json` | Application settings |
| `presets.json` | Chat presets |
| `templates/studio_templates.json` | Studio templates |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      HALO Core Application                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │ Sources │  │  Chat   │  │ Studio  │  │ Configuration   │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
│       │            │            │                  │         │
│       └────────────┴────────────┴──────────────────┘         │
│                           │                                   │
│  ┌────────────────────────┴────────────────────────────────┐ │
│  │                    Services Layer                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │ │
│  │  │ Parsers  │ │ Knowledge│ │  Agents  │ │  Runtime   │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Storage                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ JSON     │ │ LanceDB  │ │ SQLite   │ │ File Storage   │  │
│  │ Files    │ │ (Vector) │ │ (Memory) │ │ (Uploads)      │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Getting Started Checklist

- [ ] Install Python 3.10+ and dependencies
- [ ] Configure API keys in `.streamlit/secrets.toml`
- [ ] Set up data directory with appropriate permissions
- [ ] Configure memory backend (optional)
- [ ] Review security settings
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

---

## Support Resources

- [User Handbook](../handbook/index.md) — End-user documentation
- [Technical Reference](../reference/index.md) — Developer documentation
- [GitHub Repository](https://github.com/aizech/halo_core) — Source code and issues

---

Made with ❤️ by Corpus Analytica
