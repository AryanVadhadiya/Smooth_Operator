import os
import uuid
import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import socketio
import aiohttp

from schemas import TelemetryEventInput, TelemetryEvent, IngestResponse, HealthResponse
from storage import init_storage, store_event, get_events, get_event_count, clear_events

DETECTION_ENGINE_URL = os.environ.get("DETECTION_ENGINE_URL", "http://localhost:8002")
API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL", "http://localhost:3001")

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Ingest Service starting...")
    init_storage()
    print(f"Storage initialized. Events in storage: {get_event_count()}")
    print(f"Forwarding to Detection Engine at: {DETECTION_ENGINE_URL}")
    yield
    print("Ingest Service shutting down...")

app = FastAPI(
    title="Threat_Ops.ai - Ingest Service",
    description="Telemetry ingestion service",
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

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to Ingest Service'}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        service="ingest-service",
        version="1.0.0",
        events_ingested=get_event_count()
    )

@app.post("/ingest", response_model=IngestResponse, tags=["Ingest"])
async def ingest_event(event_input: TelemetryEventInput):
    try:
        event_id = event_input.event_id or str(uuid.uuid4())
        timestamp = event_input.timestamp or int(time.time())

        normalized_event = TelemetryEvent(
            event_id=event_id,
            source_ip=event_input.source_ip,
            domain=event_input.domain,
            service=event_input.service,
            event_type=event_input.event_type,
            payload=event_input.payload,
            timestamp=timestamp,
            received_at=datetime.utcnow().isoformat() + "Z"
        )

        event_dict = normalized_event.model_dump()
        stored = store_event(event_dict)

        if not stored:
            raise HTTPException(status_code=500, detail="Failed to store event")

        await sio.emit('telemetry', event_dict)

        print(f"Ingested event: {event_id} from {event_input.source_ip}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{DETECTION_ENGINE_URL}/analyze",
                    json=event_dict,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        analysis = await resp.json()
                        anomalies = analysis.get("anomalies_detected", 0)
                        if anomalies > 0:
                            print(f"Detection Engine found {anomalies} anomalies")
        except Exception as e:
            print(f"Could not reach Detection Engine: {e}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_GATEWAY_URL}/internal/telemetry",
                    json=event_dict,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        print(f"API Gateway responded: {resp.status}")
        except Exception as e:
            print(f"Could not reach API Gateway: {e}")

        return IngestResponse(
            success=True,
            event_id=event_id,
            message="Event ingested successfully"
        )

    except Exception as e:
        print(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events", tags=["Events"])
async def list_events(limit: int = 100, offset: int = 0):
    events = get_events(limit=limit, offset=offset)
    return {
        "events": events,
        "count": len(events),
        "total": get_event_count()
    }

@app.delete("/events", tags=["Events"])
async def delete_events():
    cleared = clear_events()
    if cleared:
        return {"message": "All events cleared"}
    raise HTTPException(status_code=500, detail="Failed to clear events")

@app.post("/ingest/batch", tags=["Ingest"])
async def ingest_batch(events: list[TelemetryEventInput]):
    ingested = []
    errors = []

    for i, event_input in enumerate(events):
        try:
            event_id = event_input.event_id or str(uuid.uuid4())
            timestamp = event_input.timestamp or int(time.time())

            normalized_event = TelemetryEvent(
                event_id=event_id,
                source_ip=event_input.source_ip,
                domain=event_input.domain,
                service=event_input.service,
                event_type=event_input.event_type,
                payload=event_input.payload,
                timestamp=timestamp,
                received_at=datetime.utcnow().isoformat() + "Z"
            )

            event_dict = normalized_event.model_dump()
            if store_event(event_dict):
                await sio.emit('telemetry', event_dict)
                ingested.append(event_id)
            else:
                errors.append({"index": i, "error": "Storage failed"})

        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    return {
        "ingested": len(ingested),
        "failed": len(errors),
        "event_ids": ingested,
        "errors": errors if errors else None
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8001))

    print(f"Threat_Ops.ai - Ingest Service running on port {port}")

    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=port,
        reload=False
    )
