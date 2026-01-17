import os
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Set

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socketio

PORT = int(os.environ.get("PORT", 3001))
INGEST_SERVICE_URL = os.environ.get("INGEST_SERVICE_URL", "http://localhost:8001")

class TelemetryEvent(BaseModel):
    event_id: str
    source_ip: str
    domain: str
    service: str
    event_type: str
    payload: dict = {}
    timestamp: int
    received_at: str = None

class AlertEvent(BaseModel):
    id: str
    title: str
    description: str = ""
    severity: str
    source: str
    timestamp: str
    acknowledged: bool = False
    evidence: dict = None
    recommendation: str = None

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "api-gateway"
    version: str = "1.0.0"
    connected_clients: int = 0

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

connected_clients: Set[str] = set()

@sio.event
async def connect(sid, environ):
    connected_clients.add(sid)
    print(f"Frontend connected: {sid} (total: {len(connected_clients)})")
    await sio.emit('connected', {
        'message': 'Connected to Threat_Ops.ai Gateway',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }, to=sid)

@sio.event
async def disconnect(sid):
    connected_clients.discard(sid)
    print(f"Frontend disconnected: {sid} (total: {len(connected_clients)})")

@sio.event
async def ping(sid, data):
    await sio.emit('pong', {'timestamp': datetime.utcnow().isoformat() + 'Z'}, to=sid)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"API Gateway running on port {PORT}")
    print(f"Ingest URL: {INGEST_SERVICE_URL}")
    yield
    print("API Gateway shutting down...")

app = FastAPI(
    title="Threat_Ops.ai - API Gateway",
    description="Socket.IO bridge",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_app = socketio.ASGIApp(sio, app)

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        service="api-gateway",
        version="1.0.0",
        connected_clients=len(connected_clients)
    )

@app.get("/clients", tags=["Status"])
async def get_connected_clients():
    return {
        "connected_clients": len(connected_clients),
        "client_ids": list(connected_clients)
    }

@app.post("/internal/telemetry", tags=["Internal"])
async def receive_telemetry(event: TelemetryEvent):
    try:
        frontend_event = {
            "deviceId": event.service,
            "deviceName": event.service.replace("-", " ").title(),
            "timestamp": event.received_at or datetime.utcnow().isoformat() + "Z",
            "metrics": {
                "cpu": event.payload.get("cpu", 50),
                "memory": event.payload.get("memory", 50),
                "network": event.payload.get("network", 100),
                "requests": event.payload.get("requests", 100),
            }
        }

        await sio.emit('telemetry', frontend_event)

        return {"status": "broadcast", "clients": len(connected_clients)}

    except Exception as e:
        print(f"Telemetry broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/alert", tags=["Internal"])
async def receive_alert(alert: AlertEvent):
    try:
        await sio.emit('alert', alert.model_dump())

        return {"status": "broadcast", "clients": len(connected_clients)}

    except Exception as e:
        print(f"Alert broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/device-status", tags=["Internal"])
async def receive_device_status(data: dict):
    try:
        await sio.emit('device:status', data)
        return {"status": "broadcast", "clients": len(connected_clients)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=PORT,
        reload=False
    )
