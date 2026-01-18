import os
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Set, Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socketio

# IP Management imports
from ip_manager import ip_manager, BlockReason, ThreatSeverity
from ip_middleware import setup_ip_middleware, process_event_queue, set_socket_io

PORT = int(os.environ.get("PORT", 3001))
INGEST_SERVICE_URL = os.environ.get("INGEST_SERVICE_URL", "http://localhost:8001")
RESPONSE_ENGINE_URL = os.environ.get("RESPONSE_ENGINE_URL", "http://localhost:8004")

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
    blocked_ips: int = 0

# Pydantic models for IP management API
class BlockIPRequest(BaseModel):
    ip: str
    reason: str = "manual"
    severity: str = "high"
    duration: Optional[int] = None  # seconds, None = use default

class UnblockIPRequest(BaseModel):
    ip: str

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
    # Set Socket.IO reference for middleware events
    set_socket_io(sio)

    # Start IP Manager background tasks
    await ip_manager.start()

    # Start event queue processor
    async def event_processor():
        while True:
            await process_event_queue()
            await asyncio.sleep(0.1)  # Process every 100ms

    event_task = asyncio.create_task(event_processor())

    print(f"API Gateway running on port {PORT}")
    print(f"Ingest URL: {INGEST_SERVICE_URL}")
    print(f"IP Manager: Active with auto-cleanup")
    print(f"Detection: SQL Injection, Brute Force, Flooding enabled")
    yield

    # Stop event processor
    event_task.cancel()
    try:
        await event_task
    except asyncio.CancelledError:
        pass

    # Stop IP Manager
    await ip_manager.stop()
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

# Setup IP blocking middleware (runs after CORS)
# Set bypass_local=True for development
setup_ip_middleware(app, sio=sio, bypass_local=True, enable_threat_detection=True)

socket_app = socketio.ASGIApp(sio, app)

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    stats = ip_manager.get_stats()
    return HealthResponse(
        status="healthy",
        service="api-gateway",
        version="1.0.0",
        connected_clients=len(connected_clients),
        blocked_ips=stats.get("blocked_count", 0)
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
                "devices": event.payload.get("devices", {}),
                "sector": event.payload.get("sector", "unknown"),
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

# ==========================================
# IP MANAGEMENT API
# ==========================================

@app.post("/ip/block", tags=["IP Management"])
async def block_ip_endpoint(request_data: BlockIPRequest):
    """
    Block an IP address manually or via automated response.

    - **ip**: IP address to block
    - **reason**: Why blocking (flooding, sql_injection, brute_force, manual, abuse)
    - **severity**: Threat level (low, medium, high, critical)
    - **duration**: Block duration in seconds (optional, uses severity default)
    """
    try:
        reason = BlockReason(request_data.reason)
    except ValueError:
        reason = BlockReason.MANUAL

    try:
        severity = ThreatSeverity(request_data.severity)
    except ValueError:
        severity = ThreatSeverity.HIGH

    result = ip_manager.block_ip(
        ip=request_data.ip,
        reason=reason,
        severity=severity,
        duration=request_data.duration,
        triggered_by="api_request"
    )

    # Broadcast block event to frontend
    if result.get("success"):
        await sio.emit('ip:blocked', {
            "ip": request_data.ip,
            "reason": request_data.reason,
            "severity": request_data.severity,
            "expires_in": result.get("expires_in"),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    return result


@app.post("/ip/unblock", tags=["IP Management"])
async def unblock_ip_endpoint(request_data: UnblockIPRequest):
    """Unblock an IP address"""
    result = ip_manager.unblock_ip(
        ip=request_data.ip,
        triggered_by="api_request"
    )

    # Broadcast unblock event to frontend
    if result.get("success"):
        await sio.emit('ip:unblocked', {
            "ip": request_data.ip,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    return result


@app.get("/ip/check/{ip}", tags=["IP Management"])
async def check_ip_status(ip: str):
    """Check if an IP is blocked"""
    return ip_manager.is_blocked(ip)


@app.get("/ip/blocked", tags=["IP Management"])
async def get_blocked_ips():
    """Get list of all blocked IPs with details"""
    blocked = ip_manager.get_blocked_ips()
    return {
        "blocked_ips": blocked,
        "count": len(blocked)
    }


@app.get("/ip/throttled", tags=["IP Management"])
async def get_throttled_ips():
    """Get list of throttled IPs"""
    throttled = ip_manager.get_throttled_ips()
    return {
        "throttled_ips": throttled,
        "count": len(throttled)
    }


@app.get("/ip/audit", tags=["IP Management"])
async def get_ip_audit_log(limit: int = 100):
    """Get IP management audit log"""
    return {
        "audit_log": ip_manager.get_audit_log(limit),
        "limit": limit
    }


@app.get("/ip/stats", tags=["IP Management"])
async def get_ip_stats():
    """Get IP manager statistics"""
    return ip_manager.get_stats()


# ==========================================
# DROPPED PACKETS API
# ==========================================

@app.get("/ip/dropped", tags=["Dropped Packets"])
async def get_dropped_packets(limit: int = 100, attack_type: str = None):
    """
    Get recent dropped/blocked packets.

    - **limit**: Max number of records to return (default 100)
    - **attack_type**: Filter by type (sql_injection, brute_force, flooding, blocked_ip, rate_limit)
    """
    packets = ip_manager.get_dropped_packets(limit=limit, attack_type=attack_type)
    stats = ip_manager.get_dropped_stats()
    return {
        "packets": packets,
        "count": len(packets),
        "total_dropped": stats.get("total_dropped", 0),
        "stats": stats
    }


@app.get("/ip/dropped/stats", tags=["Dropped Packets"])
async def get_dropped_stats():
    """Get dropped packet statistics"""
    return ip_manager.get_dropped_stats()


@app.get("/ip/dropped/stream", tags=["Dropped Packets"])
async def get_dropped_stream():
    """
    Get the most recent dropped packets for live display.
    Returns the last 20 dropped packets.
    """
    packets = ip_manager.get_dropped_packets(limit=20)
    return {
        "packets": packets,
        "count": len(packets)
    }


# ==========================================
# BRUTE FORCE DETECTION API
# ==========================================

@app.get("/ip/brute-force/{ip}", tags=["Detection"])
async def check_brute_force_status(ip: str):
    """Check brute force detection status for an IP"""
    return ip_manager.check_brute_force(ip)


@app.post("/ip/auth-attempt", tags=["Detection"])
async def record_auth_attempt(request: Request, data: dict):
    """
    Record an authentication attempt for brute force detection.
    Called by auth services to report login attempts.

    - **ip**: Source IP (optional, uses request IP if not provided)
    - **username**: Username attempted
    - **success**: Whether auth succeeded
    - **endpoint**: Auth endpoint path
    """
    ip = data.get("ip")
    if not ip:
        forwarded_for = request.headers.get("X-Forwarded-For")
        ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")

    result = ip_manager.record_auth_attempt(
        ip=ip,
        username=data.get("username", "unknown"),
        success=data.get("success", False),
        endpoint=data.get("endpoint", "/login")
    )

    # Broadcast if blocked
    if result.get("action") == "blocked":
        await sio.emit('ip:blocked', {
            "ip": ip,
            "reason": "brute_force",
            "severity": "high",
            "automated": True,
            "details": result.get("details", {}),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    return result


# ==========================================
# FLOODING DETECTION API
# ==========================================

@app.get("/ip/flooding/{ip}", tags=["Detection"])
async def check_flooding_status(ip: str):
    """Check flooding detection status for an IP"""
    return ip_manager.check_flooding(ip)


@app.post("/ip/rate-limit", tags=["Detection"])
async def apply_rate_limit(data: dict):
    """
    Manually apply rate limiting/throttling to an IP.

    - **ip**: IP address to throttle
    - **limit**: New rate limit (requests per minute)
    - **duration**: How long to apply throttle (seconds)
    """
    ip = data.get("ip")
    if not ip:
        raise HTTPException(status_code=400, detail="IP address required")

    result = ip_manager.apply_throttle(
        ip=ip,
        new_limit=data.get("limit", 10),
        duration=data.get("duration", 300)
    )

    # Broadcast rate limit event
    await sio.emit('ip:rate_limited', {
        "ip": ip,
        "new_limit": data.get("limit", 10),
        "duration": data.get("duration", 300),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

    return result


@app.post("/ip/clear", tags=["IP Management"])
async def clear_all_blocks():
    """Clear all IP blocks (for testing/reset)"""
    result = ip_manager.clear_all()

    await sio.emit('ip:cleared', {
        "cleared_count": result.get("cleared_count", 0),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

    return result


@app.post("/ip/detect-threat", tags=["IP Management"])
async def detect_threat_endpoint(request: Request, data: dict):
    """
    Manually trigger threat detection for an IP.
    Used by other services to report suspicious activity.
    """
    ip = data.get("ip") or (request.client.host if request.client else "unknown")
    activity_type = data.get("activity_type", "suspicious")
    score = data.get("score", 25)
    details = data.get("details", {})

    result = ip_manager.record_suspicious_activity(
        ip=ip,
        activity_type=activity_type,
        score=score,
        details=details
    )

    # If blocked, broadcast
    if result.get("action") == "blocked":
        await sio.emit('ip:blocked', {
            "ip": ip,
            "reason": activity_type,
            "severity": result.get("severity", "high"),
            "automated": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    return result

# ==========================================
# FLEET MANAGEMENT (Multi-Laptop)
# ==========================================
import aiohttp

@app.get("/nodes", tags=["Fleet"])
async def get_nodes():
    """Proxy to Ingest Service /nodes"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{INGEST_SERVICE_URL}/nodes") as resp:
                if resp.status == 200:
                    return await resp.json()
                raise HTTPException(status_code=resp.status, detail="Failed to fetch nodes")
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Ingest Service unavailable: {e}")

@app.post("/attack", tags=["Fleet"])
async def route_attack(data: dict, request: Request):
    """Route an attack to the correct sector node(s)"""
    sector = data.get("sector", "general")
    attack_type = data.get("attack_type", "unknown")
    payload = data.get("payload", {})

    # Get REAL attacker IP from the request
    # Check X-Forwarded-For header (if behind proxy) or use direct client IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        attacker_ip = forwarded_for.split(",")[0].strip()
    else:
        attacker_ip = request.client.host if request.client else "unknown"

    print(f"🎯 Attack received from IP: {attacker_ip}")

    # 0. Check if this attacker IP is already blocked
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RESPONSE_ENGINE_URL}/status") as resp:
                if resp.status == 200:
                    status_data = await resp.json()
                    blocked_ips = status_data.get("blocked_ips", [])
                    if attacker_ip in blocked_ips:
                        await sio.emit('attack_blocked', {
                            "attacker_ip": attacker_ip,
                            "sector": sector,
                            "attack_type": attack_type,
                            "message": f"🛡️ Attack BLOCKED! IP {attacker_ip} is on blocked list."
                        })
                        return {
                            "success": False,
                            "blocked": True,
                            "attacker_ip": attacker_ip,
                            "message": f"Attack blocked! IP {attacker_ip} is blocked."
                        }
    except:
        pass  # Continue if Response Engine is unavailable

    # 1. Get matching nodes from Ingest Service
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{INGEST_SERVICE_URL}/nodes") as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=503, detail="Cannot reach node registry")
                nodes_data = await resp.json()
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Registry unavailable: {e}")

    # 2. Filter nodes by sector
    matching_nodes = [
        n for n in nodes_data.get("nodes", [])
        if n.get("sector") == sector and n.get("status") == "online"
    ]

    if not matching_nodes:
        return {
            "success": False,
            "error": f"No online nodes found for sector: {sector}",
            "available_sectors": nodes_data.get("sectors", {})
        }

    # 3. Forward attack to all matching nodes (with attacker_ip)
    results = []
    for node in matching_nodes:
        node_url = f"http://{node['ip']}:{node['port']}/receive-attack"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    node_url,
                    json={
                        "attack_type": attack_type,
                        "payload": payload,
                        "from_gateway": True,
                        "attacker_ip": attacker_ip  # Pass attacker IP for blocking check
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    result = await resp.json()

                    # Handle blocked response
                    if resp.status == 403:
                        result["blocked"] = True
                        await sio.emit('attack_blocked', {
                            "attacker_ip": attacker_ip,
                            "node_id": node['node_id'],
                            "message": result.get("message", "Attack blocked!")
                        })
                    results.append({
                        "node_id": node["node_id"],
                        "ip": node["ip"],
                        "status": "delivered" if resp.status == 200 else "failed",
                        "response": result
                    })
        except Exception as e:
            results.append({
                "node_id": node["node_id"],
                "ip": node["ip"],
                "status": "unreachable",
                "error": str(e)
            })

    # Broadcast attack event to dashboard
    await sio.emit('attack_routed', {
        "sector": sector,
        "attack_type": attack_type,
        "nodes_targeted": len(matching_nodes),
        "results": results
    })

    return {
        "success": True,
        "sector": sector,
        "nodes_targeted": len(matching_nodes),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=PORT,
        reload=False
    )
