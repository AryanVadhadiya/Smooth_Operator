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

# ==========================================
# NODE REGISTRY (Multi-Laptop Fleet)
# ==========================================
NODE_REGISTRY = {}  # {node_id: {ip, port, sector, last_seen, status}}

class NodeRegistration:
    """Pydantic model for node registration"""
    pass  # Using dict for simplicity

@app.post("/register", tags=["Fleet"])
async def register_node(data: dict):
    """Register a new node (laptop) with the fleet"""
    node_id = data.get("node_id") or str(uuid.uuid4())
    ip = data.get("ip", "unknown")
    port = data.get("port", 5050)
    sector = data.get("sector", "general")

    NODE_REGISTRY[node_id] = {
        "node_id": node_id,
        "ip": ip,
        "port": port,
        "sector": sector,
        "last_seen": time.time(),
        "status": "online",
        "registered_at": datetime.utcnow().isoformat() + "Z"
    }

    print(f"📡 Node registered: {node_id} ({ip}:{port}) as {sector.upper()}")

    # Broadcast to connected clients
    await sio.emit('node_registered', NODE_REGISTRY[node_id])

    return {
        "success": True,
        "node_id": node_id,
        "message": f"Registered as {sector} node"
    }

@app.get("/nodes", tags=["Fleet"])
async def list_nodes():
    """List all registered nodes with status"""
    # Update status based on last_seen (offline if > 30s)
    current_time = time.time()
    for node_id, node in NODE_REGISTRY.items():
        if current_time - node["last_seen"] > 30:
            node["status"] = "offline"
        else:
            node["status"] = "online"

    return {
        "nodes": list(NODE_REGISTRY.values()),
        "count": len(NODE_REGISTRY),
        "sectors": {
            "healthcare": sum(1 for n in NODE_REGISTRY.values() if n["sector"] == "healthcare" and n["status"] == "online"),
            "agriculture": sum(1 for n in NODE_REGISTRY.values() if n["sector"] == "agriculture" and n["status"] == "online"),
            "urban": sum(1 for n in NODE_REGISTRY.values() if n["sector"] == "urban" and n["status"] == "online"),
        }
    }

@app.get("/nodes/{node_id}", tags=["Fleet"])
async def get_node(node_id: str):
    """Get details of a specific node"""
    if node_id not in NODE_REGISTRY:
        raise HTTPException(status_code=404, detail="Node not found")
    return NODE_REGISTRY[node_id]

@app.delete("/nodes/{node_id}", tags=["Fleet"])
async def deregister_node(node_id: str):
    """Remove a node from the registry"""
    if node_id not in NODE_REGISTRY:
        raise HTTPException(status_code=404, detail="Node not found")
    del NODE_REGISTRY[node_id]
    return {"success": True, "message": f"Node {node_id} deregistered"}

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

        # Update heartbeat for registered nodes
        service_name = event_input.service
        for node_id, node in NODE_REGISTRY.items():
            if service_name and node_id in service_name:
                node["last_seen"] = time.time()
                node["status"] = "online"
                break

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
