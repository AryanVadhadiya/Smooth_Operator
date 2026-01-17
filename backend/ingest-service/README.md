# Threat_Ops.ai - Ingest Service

Telemetry ingestion service for security event processing.

## Features

- **POST /ingest** - Receive and normalize telemetry events
- **GET /events** - List stored events with pagination
- **Socket.IO** - Real-time event streaming
- **JSON Storage** - Local file persistence (demo-safe)

## Quick Start

### 1. Create Virtual Environment

```bash
cd /Users/aryan/Developer/Threat_Ops.ai/backend/ingest-service
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Service

```bash
python main.py
```

Service runs at: **http://localhost:8001**

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest` | Ingest single event |
| POST | `/ingest/batch` | Ingest multiple events |
| GET | `/events` | List stored events |
| DELETE | `/events` | Clear all events |

## Test with curl

### Send Single Event

```bash
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_ip": "192.168.1.100",
    "domain": "healthcare",
    "service": "patient-api",
    "event_type": "http_request",
    "payload": {
      "method": "POST",
      "path": "/api/patients/123",
      "status_code": 200
    }
  }'
```

### Health Check

```bash
curl http://localhost:8001/health
```

### List Events

```bash
curl http://localhost:8001/events
```

## Socket.IO

Connect to `http://localhost:8001` and listen for `telemetry` events.

```javascript
import { io } from 'socket.io-client'

const socket = io('http://localhost:8001')

socket.on('telemetry', (event) => {
  console.log('Received:', event)
})
```

## Event Schema

```json
{
  "event_id": "auto-generated UUID",
  "source_ip": "192.168.1.12",
  "domain": "healthcare",
  "service": "patient-api",
  "event_type": "http_request",
  "payload": {},
  "timestamp": 1710000000,
  "received_at": "2024-03-09T12:00:00.000Z"
}
```
