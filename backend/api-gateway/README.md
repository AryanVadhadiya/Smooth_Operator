# Threat_Ops.ai - API Gateway

Socket.IO bridge between backend services and frontend.

## Features

- **Socket.IO server** on port 3001
- **Internal endpoints** for service-to-service communication
- **Broadcasts** telemetry, alerts, device status to frontend

## Quick Start

### 1. Create Virtual Environment

```bash
cd /Users/aryan/Developer/Threat_Ops.ai/backend/api-gateway
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

Service runs at: **http://localhost:3001**

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/clients` | Connected client count |
| POST | `/internal/telemetry` | Receive + broadcast telemetry |
| POST | `/internal/alert` | Receive + broadcast alerts |

## Socket.IO Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Frontend connects |
| `telemetry` | Server → Client | Telemetry data |
| `alert` | Server → Client | Security alerts |
| `device:status` | Server → Client | Device updates |

## Test

```bash
# Health check
curl http://localhost:3001/health

# Check connected clients
curl http://localhost:3001/clients
```

## Architecture

```
Frontend (React) ←→ Socket.IO ←→ API Gateway ←→ Backend Services
                                      ↑
                              POST /internal/*
```
