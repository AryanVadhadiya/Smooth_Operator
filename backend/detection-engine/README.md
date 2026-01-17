# Threat_Ops.ai - Detection Engine

Rule-based anomaly detection service.

## Features

- **SQL Injection Detection** - Pattern matching for malicious queries
- **Rate Spike Detection** - Abnormal request rates per IP
- **Metric Thresholds** - High CPU/Memory/Network alerts
- **Brute Force Detection** - Failed authentication patterns

## Quick Start

```bash
cd /Users/aryan/Developer/Threat_Ops.ai/backend/detection-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Service runs at: **http://localhost:8002**

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/rules` | List detection rules |
| POST | `/analyze` | Analyze single event |
| POST | `/analyze/batch` | Analyze multiple events |

## Test Detection

```bash
# SQL Injection test
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-1",
    "source_ip": "192.168.1.100",
    "domain": "healthcare",
    "service": "api",
    "event_type": "http_request",
    "payload": {"query": "SELECT * FROM users WHERE id=1 OR 1=1"},
    "timestamp": 1710000000
  }'

# High CPU test
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-2",
    "source_ip": "10.0.0.1",
    "domain": "infrastructure",
    "service": "database",
    "event_type": "system_metric",
    "payload": {"cpu": 95.0, "memory": 60.0},
    "timestamp": 1710000000
  }'
```

## Detection Rules

| Rule | Trigger | Severity |
|------|---------|----------|
| `sql_injection` | SQL patterns in payload | Critical |
| `rate_spike` | >100 req/min from IP | Warning |
| `high_cpu` | CPU > 85% | Warning/Critical |
| `high_memory` | Memory > 90% | Critical |
| `high_network` | Network > 900 KB/s | Warning |
| `brute_force` | 5+ failed auths in 5min | Critical |
