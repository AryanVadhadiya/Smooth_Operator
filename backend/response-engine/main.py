import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp

from playbooks import (
    run_playbook,
    get_blocked_ips,
    get_isolated_services,
    get_action_log,
    clear_all_actions,
    ActionResult
)

PORT = int(os.environ.get("PORT", 8004))
API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL", "http://localhost:3001")

class Alert(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    source: str
    timestamp: str
    acknowledged: bool = False
    evidence: Optional[dict] = None
    recommendation: Optional[str] = None
    anomaly_id: Optional[str] = None
    rule_id: Optional[str] = None

class ActionOutput(BaseModel):
    action_id: str
    action_type: str
    status: str
    target: str
    message: str
    executed_at: str
    details: Optional[dict] = None

class ExecuteResponse(BaseModel):
    alert_id: str
    actions_executed: int
    actions: List[ActionOutput]

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "response-engine"
    version: str = "1.0.0"
    blocked_ips: int = 0
    isolated_services: int = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Response Engine running on port {PORT}")
    print(f"Gateway: {API_GATEWAY_URL}")
    yield
    print("Response Engine shutting down...")

app = FastAPI(
    title="Threat_Ops.ai - Response Engine",
    description="Automated incident response",
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

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        service="response-engine",
        version="1.0.0",
        blocked_ips=len(get_blocked_ips()),
        isolated_services=len(get_isolated_services())
    )

@app.get("/status", tags=["Status"])
async def get_status():
    return {
        "blocked_ips": get_blocked_ips(),
        "isolated_services": get_isolated_services(),
        "actions_executed": len(get_action_log())
    }

@app.get("/actions", tags=["Actions"])
async def list_actions(limit: int = 50):
    actions = get_action_log()[-limit:]
    return {
        "actions": [
            {
                "action_type": a.action_type,
                "status": a.status,
                "target": a.target,
                "message": a.message,
                "executed_at": a.executed_at,
            }
            for a in reversed(actions)
        ],
        "count": len(actions)
    }

@app.post("/execute", response_model=ExecuteResponse, tags=["Execute"])
async def execute_response(alert: Alert):
    try:
        print(f"Executing response for: {alert.title}")

        results = run_playbook(alert.model_dump())

        actions = []
        for result in results:
            action_id = str(uuid.uuid4())
            action = ActionOutput(
                action_id=action_id,
                action_type=result.action_type,
                status=result.status,
                target=result.target,
                message=result.message,
                executed_at=result.executed_at,
                details=result.details
            )
            actions.append(action)

            print(f"   {result.message}")

        await emit_action_events(alert, actions)

        return ExecuteResponse(
            alert_id=alert.id,
            actions_executed=len(actions),
            actions=actions
        )

    except Exception as e:
        print(f"Response execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def emit_action_events(alert: Alert, actions: List[ActionOutput]):
    try:
        async with aiohttp.ClientSession() as session:
            for action in actions:
                event = {
                    "type": "response_action",
                    "alert_id": alert.id,
                    "action": action.model_dump(),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

                async with session.post(
                    f"{API_GATEWAY_URL}/internal/device-status",
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        print(f"Action event emitted: {action.action_type}")
    except aiohttp.ClientError as e:
        print(f"Could not emit action event: {e}")

@app.post("/block/{ip}", tags=["Manual"])
async def manual_block_ip(ip: str):
    from playbooks import blocked_ips

    if ip in blocked_ips:
        return {"status": "already_blocked", "ip": ip}

    blocked_ips.add(ip)
    return {"status": "blocked", "ip": ip, "message": f"IP {ip} blocked"}

@app.delete("/block/{ip}", tags=["Manual"])
async def manual_unblock_ip(ip: str):
    from playbooks import blocked_ips

    if ip not in blocked_ips:
        raise HTTPException(status_code=404, detail="IP not blocked")

    blocked_ips.discard(ip)
    return {"status": "unblocked", "ip": ip}

@app.post("/isolate/{service}", tags=["Manual"])
async def manual_isolate_service(service: str):
    from playbooks import isolated_services

    if service in isolated_services:
        return {"status": "already_isolated", "service": service}

    isolated_services.add(service)
    return {"status": "isolated", "service": service}

@app.delete("/isolate/{service}", tags=["Manual"])
async def manual_restore_service(service: str):
    from playbooks import isolated_services

    if service not in isolated_services:
        raise HTTPException(status_code=404, detail="Service not isolated")

    isolated_services.discard(service)
    return {"status": "restored", "service": service}

@app.delete("/reset", tags=["Admin"])
async def reset_all():
    clear_all_actions()
    return {"status": "reset", "message": "All actions cleared"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        reload=False
    )
