# Threat_Ops.ai - Response Engine

Automated incident response and playbook execution.

## Quick Start

```bash
cd /Users/aryan/Developer/Threat_Ops.ai/backend/response-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Port:** 8004

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Current defense status |
| GET | `/actions` | Action log |
| POST | `/execute` | Execute playbook for alert |
| POST | `/block/{ip}` | Manually block IP |
| DELETE | `/block/{ip}` | Unblock IP |

## Playbooks

| Rule | Actions |
|------|---------|
| sql_injection | Block IP, Alert |
| brute_force | Block IP, Throttle |
| rate_spike | Throttle |
| high_memory | Isolate Service |

## Test

```bash
curl -X POST http://localhost:8004/execute \
  -H "Content-Type: application/json" \
  -d '{
    "id": "alert-1",
    "title": "SQL Injection",
    "description": "...",
    "severity": "critical",
    "source": "api",
    "timestamp": "2024-01-01T00:00:00Z",
    "rule_id": "sql_injection",
    "evidence": {"source_ip": "192.168.1.100"}
  }'
```
