# Monitoring

Logging, observability, and diagnostics for HALO Core administrators.

---

## Monitoring Overview

Effective monitoring covers:

- **Application health** — Is it running?
- **Performance** — Is it fast enough?
- **Errors** — What's failing?
- **Usage** — How is it being used?

---

## Logging Configuration

### Log Controls

Enable in configuration:

```json
{
  "chat": {
    "log_user_requests": true,
    "log_agent_payloads": true,
    "log_agent_responses": true,
    "log_agent_errors": true,
    "log_stream_events": false
  }
}
```

### Log Levels

| Setting | Purpose |
|---------|---------|
| `log_user_requests` | Log all user inputs |
| `log_agent_payloads` | Log request payloads to AI |
| `log_agent_responses` | Log AI responses |
| `log_agent_errors` | Log errors (recommended: true) |
| `log_stream_events` | Log streaming events (verbose) |

### Streamlit Logs

View real-time logs:

```bash
streamlit run app/main.py
# Logs output to console
```

### Production Logging

Capture logs to file:

```bash
streamlit run app/main.py 2>&1 | tee -a logs/app.log
```

---

## Chat Run Traces

### What Traces Contain

Each chat turn stores telemetry:

| Field | Description |
|-------|-------------|
| `model` | AI model used |
| `selected_members` | Team agents involved |
| `tools` | Tools used |
| `stream_mode` | Streaming configuration |
| `stream_events` | Events enabled flag |
| `stream_result` | Streaming outcome |
| `latency_ms` | Response time |
| `knowledge_hits` | Retrieved documents |
| `knowledge_sources` | Source references |
| `used_fallback` | Fallback triggered |

### Accessing Traces

Traces are stored in:

- Chat history JSON files
- Assistant message metadata

### Using Traces for Debugging

1. Check `latency_ms` for slow responses
2. Review `knowledge_hits` for retrieval issues
3. Check `used_fallback` for streaming problems
4. Verify `selected_members` for delegation issues

---

## Performance Monitoring

### Key Metrics

| Metric | Target | Warning |
|--------|--------|---------|
| Response latency | < 5s | > 10s |
| Memory usage | < 2GB | > 4GB |
| CPU usage | < 50% | > 80% |
| Error rate | < 1% | > 5% |

### Monitoring Tools

**Built-in:**

- Streamlit status indicators
- Application logs

**External:**

- Prometheus + Grafana
- Datadog
- New Relic
- Cloud provider monitoring

### Streamlit Metrics

```python
# Add to custom monitoring
import streamlit as st
import time

start = time.time()
# ... operation ...
latency = time.time() - start
st.session_state['metrics'] = {
    'latency': latency
}
```

---

## Error Tracking

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| API key invalid | Wrong/expired key | Update credentials |
| Rate limit | Too many requests | Implement backoff |
| Timeout | Slow response | Increase timeout |
| Memory error | Large files | Limit file size |

### Error Logging

Enable error logging:

```json
{
  "chat": {
    "log_agent_errors": true
  }
}
```

### Error Alerts

Set up alerts for:

- API errors
- Application crashes
- High error rates
- Resource exhaustion

---

## Health Checks

### Basic Health Check

```bash
# Check if app is responding
curl -f http://localhost:8501/_stcore/health

# Or check HTTP status
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
```

### Automated Health Monitoring

```bash
#!/bin/bash
# healthcheck.sh

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501)

if [ "$RESPONSE" != "200" ]; then
    echo "HALO Core health check failed: $RESPONSE"
    # Send alert
    exit 1
fi

echo "HALO Core is healthy"
exit 0
```

### Systemd Watchdog

```ini
[Unit]
Description=HALO Core

[Service]
Type=simple
WatchdogSec=30
Restart=always
ExecStart=/path/to/streamlit run app/main.py
```

---

## Usage Analytics

### What to Track

- Active sessions
- Messages per session
- Sources uploaded
- Outputs generated
- Feature usage

### Implementation

```python
# Custom analytics
import json
from datetime import datetime

def track_event(event_type, metadata):
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "metadata": metadata
    }
    # Store or send to analytics service
```

### Privacy Considerations

- Anonymize user data
- Respect user preferences
- Comply with regulations
- Document data collection

---

## Observability Stack

### Recommended Setup

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   HALO      │────▶│  Prometheus │────▶│   Grafana   │
│   Core      │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       │            ┌─────────────┐     ┌─────────────┐
       └───────────▶│   Loki      │────▶│   Grafana   │
                    │   (Logs)    │     │             │
                    └─────────────┘     └─────────────┘
```

### Metrics Export

Add Prometheus metrics:

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('halo_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('halo_request_latency_seconds', 'Request latency')

@REQUEST_LATENCY.time()
def process_request():
    REQUEST_COUNT.inc()
    # ... process ...
```

---

## Alerting

### Alert Rules

Example Prometheus rules:

```yaml
groups:
  - name: halo-core
    rules:
      - alert: HighLatency
        expr: halo_request_latency_seconds > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High response latency

      - alert: HighErrorRate
        expr: rate(halo_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

### Notification Channels

- Email
- Slack
- PagerDuty
- SMS

---

## Troubleshooting Runbook

### App Not Responding

1. Check process running
2. Check port availability
3. Check resource usage
4. Review logs for errors

### High Latency

1. Check API response times
2. Check knowledge retrieval performance
3. Check resource constraints
4. Review streaming configuration

### Errors Increasing

1. Check API status
2. Review recent changes
3. Check resource limits
4. Analyze error patterns

---

## Next Steps

- [Maintenance](maintenance.md) — Routine maintenance
- [Security](security.md) — Security monitoring
