# User Management

User identity and memory management for HALO Core administrators.

---

## User Identity Model

### Default Behavior

HALO Core uses a **local user identity** by default:

- User ID: `local-user`
- No authentication required
- Single-user context

### Custom User Identity

Set a custom user ID via configuration:

```json
{
  "app": {
    "user_id": "custom-user-123"
  }
}
```

---

## Memory Backend

### What It Does

The memory backend enables:

- Persistent user memory across sessions
- Agent memory for context continuity
- Bounded conversation history

### Enabling Memory Backend

Set `HALO_AGENT_DB` environment variable:

```bash
# SQLite (recommended for single instance)
export HALO_AGENT_DB="sqlite:///data/memory.db"

# PostgreSQL (for distributed setups)
export HALO_AGENT_DB="postgresql://user:pass@host/db"
```

### Memory Behavior

When enabled:

- Agents use bounded history (`num_history_runs=3`)
- User memories persist across sessions
- Account page displays memory entries

---

## Account Page

### User View

The Account page shows:

- Current user identity
- Memory entries (if backend enabled)
- Memory management controls

### Memory Management

Users can:

- View stored memory entries
- Delete selected entries
- Clear all memory

---

## Multi-User Considerations

### Current Limitations

The default setup is designed for:

- Single-user local deployment
- Single-user cloud instance

### Multi-User Options

For multi-user scenarios:

1. **Separate Instances**
   - Deploy separate HALO instances
   - Each has own data directory

2. **Custom Authentication**
   - Implement custom auth layer
   - Integrate with identity provider
   - Modify user_id based on session

3. **Database Backend**
   - Use shared database
   - Implement user isolation
   - Requires custom development

---

## Session Management

### Session Lifecycle

1. User opens application
2. Session created with user identity
3. Chat history accumulates in session
4. Session persists to `data/chat_history/`
5. Session can be resumed

### Session Files

Location: `data/chat_history/`

Format: JSON files per session

### Clearing Sessions

Delete session files:

```bash
rm -rf data/chat_history/*
```

---

## Data Isolation

### Per-User Data Directory

Use different `HALO_DATA_DIR` per user:

```bash
# User 1
export HALO_DATA_DIR="/data/user1"

# User 2
export HALO_DATA_DIR="/data/user2"
```

### Data Structure

```
data/
├── chat_history/       # Conversation logs
├── lancedb/            # Vector database
├── sources/            # Uploaded files
├── notes/              # Saved notes
├── outputs/            # Studio outputs
└── agents/             # Agent configs
```

---

## Memory Database Schema

### SQLite Schema

```sql
-- User memories table
CREATE TABLE user_memories (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    memory TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent runs table
CREATE TABLE agent_runs (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    run_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Privacy Considerations

### Data Stored

- Chat history
- Uploaded sources
- Generated outputs
- User memories
- Agent configurations

### Data Retention

Implement retention policies:

1. **Chat History**
   ```bash
   # Delete chats older than 30 days
   find data/chat_history -mtime +30 -delete
   ```

2. **Sources**
   - Manual cleanup via UI
   - Automated cleanup scripts

3. **Memory**
   - User-managed via Account page
   - Admin can clear database

### GDPR Compliance

For GDPR compliance:

1. Implement data export functionality
2. Implement right to erasure
3. Document data processing
4. Obtain user consent

---

## Troubleshooting

### "Memory backend disabled"

**Cause:** `HALO_AGENT_DB` not set.

**Solution:**
```bash
export HALO_AGENT_DB="sqlite:///data/memory.db"
```

### "Memory entries don't persist"

**Possible causes:**

- Database file not writable
- Invalid connection string
- Disk space issue

**Solutions:**

1. Check file permissions
2. Verify connection string format
3. Ensure disk space available

### "Account page shows no memory"

**Possible causes:**

- No memories stored yet
- Memory backend not enabled
- Database query error

**Solutions:**

1. Use chat to generate memories
2. Enable memory backend
3. Check logs for errors

---

## Next Steps

- [Security](security.md) — Secure user data
- [Monitoring](monitoring.md) — Track usage
- [Maintenance](maintenance.md) — Backup user data
