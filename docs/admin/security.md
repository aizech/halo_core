# Security

Security best practices and compliance considerations for HALO Core.

---

## Security Overview

HALO Core handles:

- API credentials
- User-uploaded documents
- Generated content
- Conversation history

Proper security measures protect this sensitive data.

---

## API Key Security

### Storage Options

| Method | Security | Use Case |
|--------|----------|----------|
| Secrets file | Medium | Development |
| Environment variables | High | Production |
| Secrets manager | Highest | Enterprise |

### Secrets File

Location: `.streamlit/secrets.toml`

```toml
OPENAI_API_KEY = "sk-..."
```

**Best practices:**

1. Add to `.gitignore`:
   ```
   .streamlit/secrets.toml
   ```

2. Restrict permissions:
   ```bash
   chmod 600 .streamlit/secrets.toml
   ```

3. Never commit to version control

### Environment Variables

```bash
# More secure for production
export OPENAI_API_KEY="sk-..."
```

### Secrets Managers

For enterprise deployments:

- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- GCP Secret Manager

---

## Network Security

### HTTPS/TLS

Always use HTTPS in production:

1. **Reverse Proxy with SSL**

   Nginx example:
   ```nginx
   server {
       listen 443 ssl;
       server_name halo.example.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://localhost:8501;
       }
   }
   ```

2. **Let's Encrypt**

   ```bash
   certbot --nginx -d halo.example.com
   ```

### Firewall Rules

Restrict access:

```bash
# Allow only specific IPs
ufw allow from 10.0.0.0/8 to any port 8501

# Or use reverse proxy
ufw allow 80/tcp
ufw allow 443/tcp
```

### VPN Access

For internal tools:

- Deploy behind VPN
- Use VPN-only network rules
- Implement zero-trust access

---

## Data Security

### Data at Rest

| Data Type | Location | Protection |
|-----------|----------|------------|
| Sources | `data/sources/` | File permissions |
| Chat history | `data/chat_history/` | File permissions |
| Vector DB | `data/lancedb/` | File permissions |
| Memory DB | `HALO_AGENT_DB` | Database encryption |

### Encryption Options

1. **File System Encryption**
   - LUKS (Linux)
   - BitLocker (Windows)
   - FileVault (macOS)

2. **Database Encryption**
   - SQLite with SQLCipher
   - PostgreSQL with pgcrypto

### Access Control

```bash
# Restrict data directory
chmod 700 data/
chown halo:halo data/
```

---

## Authentication

### Current State

Default HALO Core:

- No built-in authentication
- Single-user local identity
- No login required

### Adding Authentication

Options for authentication:

1. **Streamlit Authenticator**

   ```python
   import streamlit_authenticator as stauth
   # Implement login flow
   ```

2. **Reverse Proxy Auth**

   - OAuth2 Proxy
   - Authelia
   - Cloudflare Access

3. **Custom Implementation**

   - Integrate with IdP
   - Implement session management
   - Add user context

---

## Compliance

### HIPAA Considerations

For healthcare use:

- **Business Associate Agreement** with API providers
- **Data encryption** at rest and in transit
- **Access logging** and audit trails
- **Data minimization** practices
- **Breach notification** procedures

### GDPR Considerations

For EU users:

- **Lawful basis** for processing
- **Data subject rights** implementation
- **Privacy notices** and consent
- **Data retention** policies
- **Cross-border transfer** safeguards

### SOC 2 Considerations

For enterprise:

- **Security controls** documentation
- **Access management** procedures
- **Change management** processes
- **Incident response** plans

---

## Audit Logging

### Enable Logging

In configuration:

```json
{
  "chat": {
    "log_user_requests": true,
    "log_agent_payloads": true,
    "log_agent_responses": true,
    "log_agent_errors": true
  }
}
```

### Log Location

Logs are written to:

- Streamlit logs (stdout)
- Application logs (configurable)

### Log Retention

Implement retention:

```bash
# Rotate logs older than 30 days
find /var/log/halo -name "*.log" -mtime +30 -delete
```

---

## Vulnerability Management

### Dependency Scanning

Regular audits:

```bash
# Using pip-audit
pip-audit -r requirements.txt

# Using safety
safety check -r requirements.txt
```

### Security Updates

1. Monitor CVE databases
2. Subscribe to security advisories
3. Update dependencies promptly
4. Test before deployment

### Penetration Testing

For production systems:

- Regular security assessments
- Code review for security issues
- External penetration testing

---

## Incident Response

### Preparation

1. Document security procedures
2. Establish incident team
3. Define escalation paths
4. Prepare communication templates

### Detection

Monitor for:

- Unusual access patterns
- Failed authentication attempts
- Data exfiltration signs
- Service disruptions

### Response

1. **Contain** — Isolate affected systems
2. **Investigate** — Determine scope and cause
3. **Remediate** — Fix vulnerability
4. **Recover** — Restore normal operations
5. **Report** — Notify affected parties

---

## Security Checklist

- [ ] API keys stored securely
- [ ] HTTPS enabled
- [ ] Firewall rules configured
- [ ] Data directory permissions set
- [ ] Logging enabled
- [ ] Dependency audit completed
- [ ] Incident response plan documented
- [ ] Compliance requirements reviewed

---

## Next Steps

- [Monitoring](monitoring.md) — Security monitoring
- [Maintenance](maintenance.md) — Security updates
