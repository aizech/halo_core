# Deployment

This guide covers infrastructure setup and deployment options for HALO Core.

---

## Deployment Options

| Option | Use Case | Complexity |
|--------|----------|------------|
| Local Development | Development, testing | Low |
| Streamlit Cloud | Demo, lightweight hosting | Low |
| Docker Container | Production, portability | Medium |
| Cloud VM | Full control, enterprise | High |

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|--------------|
| Python | 3.10 | 3.11+ |
| RAM | 4 GB | 8 GB+ |
| Disk | 10 GB | 50 GB+ |
| CPU | 2 cores | 4+ cores |

### Software Dependencies

- Python 3.10+
- FFmpeg (for audio/video processing)
- Git (for version control)
- Docker (for containerized deployment)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/aizech/halo_core.git
cd halo_core
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows PowerShell
. .venv/Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Secrets

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-..."
```

### 5. Run Application

```bash
streamlit run app/main.py
```

---

## Streamlit Cloud Deployment

### Limitations

- No persistent storage between sessions
- Session timeout after inactivity (~15-20 min)
- Cold starts may take seconds
- No access to local files/env vars
- User memory backend disabled

### Deployment Steps

1. Push code to GitHub repository
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Deploy from repository
4. Configure secrets in Streamlit Cloud dashboard

### Secrets Configuration

In Streamlit Cloud dashboard, add:

```toml
OPENAI_API_KEY = "sk-..."
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8501

# Run application
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build and Run

```bash
# Build image
docker build -t halo-core .

# Run container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-... \
  -v halo-data:/app/data \
  halo-core
```

### Docker Compose

```yaml
version: '3.8'

services:
  halo-core:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - HALO_DATA_DIR=/app/data
      - HALO_AGENT_DB=sqlite:///app/data/memory.db
    volumes:
      - halo-data:/app/data
      - ./secrets:/app/.streamlit:ro

volumes:
  halo-data:
```

---

## Cloud VM Deployment

### Recommended Providers

- AWS EC2
- Google Cloud Compute Engine
- Azure Virtual Machines
- DigitalOcean Droplets

### Setup Steps

1. **Provision VM**
   - Choose appropriate instance size
   - Configure security groups/firewall
   - Set up SSH access

2. **Install Dependencies**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python
   sudo apt install python3.11 python3.11-venv -y

   # Install FFmpeg
   sudo apt install ffmpeg -y
   ```

3. **Deploy Application**
   ```bash
   git clone https://github.com/aizech/halo_core.git
   cd halo_core
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure as Service**

   Create `/etc/systemd/system/halo-core.service`:

   ```ini
   [Unit]
   Description=HALO Core Application
   After=network.target

   [Service]
   Type=simple
   User=halo
   WorkingDirectory=/opt/halo_core
   Environment="PATH=/opt/halo_core/.venv/bin"
   ExecStart=/opt/halo_core/.venv/bin/streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable halo-core
   sudo systemctl start halo-core
   ```

5. **Configure Reverse Proxy**

   Using Nginx:

   ```nginx
   server {
       listen 80;
       server_name halo.example.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `HALO_DATA_DIR` | Data storage directory | `data/` |
| `HALO_TEMPLATES_DIR` | Templates directory | `templates/` |
| `HALO_AGENT_DB` | Memory backend connection string | None |

---

## Production Checklist

- [ ] API keys configured securely
- [ ] Data directory with appropriate permissions
- [ ] SSL/TLS certificate installed
- [ ] Reverse proxy configured
- [ ] Firewall rules set
- [ ] Monitoring and logging enabled
- [ ] Backup strategy implemented
- [ ] Resource limits configured

---

## Troubleshooting

### Application won't start

1. Check Python version (3.10+)
2. Verify all dependencies installed
3. Check for port conflicts
4. Review logs for errors

### API connectivity issues

1. Verify API key is valid
2. Check network connectivity
3. Review firewall rules
4. Test API directly

### Performance issues

1. Increase resource allocation
2. Check for memory leaks
3. Review concurrent connections
4. Consider caching strategies

---

## Next Steps

- [Configuration](configuration.md) — System configuration
- [Security](security.md) — Security best practices
- [Monitoring](monitoring.md) — Observability setup
