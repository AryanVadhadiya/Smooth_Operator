# Threat_Ops.ai - Alert Manager

Converts anomaly signals to human-readable alerts.

## Quick Start

```bash
cd /Users/aryan/Developer/Threat_Ops.ai/backend/alert-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Port:** 8003

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/alerts` | List alerts |
| POST | `/internal/anomaly` | Receive from detection |
| POST | `/alerts/{id}/acknowledge` | Acknowledge alert |

## Test

```bash
curl -X POST http://localhost:8003/internal/anomaly \
  -H "Content-Type: application/json" \
  -d '{
    "anomaly_id": "test-1",
    "rule_id": "sql_injection",
    "rule_name": "SQL Injection",
    "severity": "critical",
    "confidence": 0.9,
    "description": "SQL injection detected",
    "evidence": {"source_ip": "192.168.1.100"},
    "recommendation": "Block IP",
    "source_event_id": "evt-1",
    "detected_at": "2024-01-01T00:00:00Z"
  }'
```
