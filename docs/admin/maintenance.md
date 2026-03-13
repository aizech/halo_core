# Maintenance

Backup, updates, and migration procedures for HALO Core administrators.

---

## Backup Strategy

### What to Back Up

| Data | Location | Frequency |
|------|----------|-----------|
| Sources | `data/sources/` | Daily |
| Chat history | `data/chat_history/` | Daily |
| Notes | `data/notes/` | Daily |
| Outputs | `data/outputs/` | Daily |
| Vector DB | `data/lancedb/` | Daily |
| Agent configs | `data/agents/` | On change |
| App config | `data/config.json` | On change |

### Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/halo/$DATE"
DATA_DIR="${HALO_DATA_DIR:-data}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup data
cp -r "$DATA_DIR" "$BACKUP_DIR/data"

# Backup configuration
cp config.json "$BACKUP_DIR/" 2>/dev/null
cp presets.json "$BACKUP_DIR/" 2>/dev/null
cp templates/studio_templates.json "$BACKUP_DIR/" 2>/dev/null

# Compress
tar -czf "$BACKUP_DIR.tar.gz" -C "/backups/halo" "$DATE"
rm -rf "$BACKUP_DIR"

echo "Backup created: $BACKUP_DIR.tar.gz"
```

### Automated Backups

**Cron job:**

```bash
# Daily backup at 2 AM
0 2 * * * /opt/halo/scripts/backup.sh >> /var/log/halo/backup.log 2>&1
```

**Systemd timer:**

```ini
# /etc/systemd/system/halo-backup.timer
[Unit]
Description=HALO Core Daily Backup

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Backup Retention

```bash
# Delete backups older than 30 days
find /backups/halo -name "*.tar.gz" -mtime +30 -delete
```

### Restore Procedure

```bash
# Extract backup
tar -xzf /backups/halo/20240115_020000.tar.gz

# Restore data
cp -r 20240115_020000/data/* ${HALO_DATA_DIR:-data}/

# Restore configuration
cp 20240115_020000/config.json ./
cp 20240115_020000/presets.json ./
```

---

## Updates

### Update Process

1. **Backup current state**
   ```bash
   ./scripts/backup.sh
   ```

2. **Pull latest changes**
   ```bash
   git pull origin main
   ```

3. **Update dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Run tests**
   ```bash
   pytest
   ```

5. **Restart application**
   ```bash
   sudo systemctl restart halo-core
   ```

### Version Updates

Check for new releases:

```bash
git fetch --tags
git tag -l
```

Update to specific version:

```bash
git checkout v1.2.0
pip install -r requirements.txt
```

### Dependency Updates

Check for outdated packages:

```bash
pip list --outdated
```

Update specific package:

```bash
pip install --upgrade package-name
```

### Database Migrations

If schema changes:

```bash
# Backup database
cp data/memory.db data/memory.db.bak

# Run migrations (if applicable)
python scripts/migrate.py
```

---

## Data Migration

### Migrate Data Directory

```bash
# Stop application
sudo systemctl stop halo-core

# Copy data
cp -r /old/data/* /new/data/

# Update environment
export HALO_DATA_DIR=/new/data

# Restart application
sudo systemctl start halo-core
```

### Migrate to New Server

1. **Prepare new server**
   - Install dependencies
   - Configure environment

2. **Transfer data**
   ```bash
   # On old server
   tar -czf halo-data.tar.gz data/ config.json presets.json

   # Transfer
   scp halo-data.tar.gz user@new-server:/opt/halo/

   # On new server
   tar -xzf halo-data.tar.gz
   ```

3. **Verify migration**
   - Check data integrity
   - Test functionality
   - Monitor for issues

### Database Migration

**SQLite to PostgreSQL:**

```bash
# Export SQLite
sqlite3 data/memory.db .dump > dump.sql

# Convert to PostgreSQL format
# (may require manual adjustments)

# Import to PostgreSQL
psql -h host -U user -d db < dump.sql
```

---

## Routine Maintenance

### Daily

- Monitor application health
- Check error logs
- Verify backup completion

### Weekly

- Review resource usage
- Check disk space
- Update dependencies (dev)
- Review security logs

### Monthly

- Full dependency audit
- Security review
- Performance analysis
- Backup verification

---

## Cleanup Procedures

### Clear Old Chat History

```bash
# Delete chats older than 90 days
find data/chat_history -name "*.json" -mtime +90 -delete
```

### Clear Temporary Files

```bash
# Clear temp uploads
rm -rf data/temp/*

# Clear old logs
find logs -name "*.log" -mtime +30 -delete
```

### Optimize Vector Database

```bash
# LanceDB optimization (if needed)
# Typically automatic, but can trigger manually
python scripts/optimize_lancedb.py
```

---

## Disaster Recovery

### Recovery Plan

1. **Assess damage**
   - Determine scope of issue
   - Identify affected components

2. **Restore from backup**
   ```bash
   tar -xzf /backups/halo/latest.tar.gz
   cp -r data/* ${HALO_DATA_DIR:-data}/
   ```

3. **Verify integrity**
   - Check data consistency
   - Test core functions

4. **Resume operations**
   - Restart application
   - Monitor for issues

### Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single server failure | 1 hour | 24 hours |
| Data corruption | 4 hours | 24 hours |
| Complete site failure | 8 hours | 24 hours |

---

## Maintenance Checklist

### Daily

- [ ] Health check passed
- [ ] No critical errors
- [ ] Backup completed

### Weekly

- [ ] Resource usage reviewed
- [ ] Disk space adequate
- [ ] Logs reviewed

### Monthly

- [ ] Dependencies audited
- [ ] Security reviewed
- [ ] Backups tested
- [ ] Performance analyzed

---

## Troubleshooting

### Backup fails

1. Check disk space
2. Verify permissions
3. Check for file locks

### Restore fails

1. Verify backup integrity
2. Check file permissions
3. Ensure compatible version

### Migration issues

1. Verify data integrity
2. Check path references
3. Test with small dataset first

---

## Next Steps

- [Deployment](deployment.md) — Redeploy if needed
- [Monitoring](monitoring.md) — Monitor after maintenance
