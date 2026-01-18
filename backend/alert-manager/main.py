import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp

PORT = int(os.environ.get("PORT", 8003))
API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL", "http://localhost:3001")
RESPONSE_ENGINE_URL = os.environ.get("RESPONSE_ENGINE_URL", "http://localhost:8004")

class AnomalySignal(BaseModel):
    anomaly_id: str
    rule_id: str
    rule_name: str
    severity: str
    confidence: float
    description: str
    evidence: dict
    recommendation: str
    source_event_id: str
    detected_at: str

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

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "alert-manager"
    version: str = "1.0.0"
    alerts_generated: int = 0

ALERT_TEMPLATES = {
    "sql_injection": {
        "title": "🚨 SQL Injection Attempt",
        "severity": "critical",
    },
    "rate_spike": {
        "title": "⚡ Potential DDoS Attack",
        "severity": "warning",
    },
    "high_cpu": {
        "title": "🔥 High CPU Usage Alert",
        "severity": "warning",
    },
    "high_memory": {
        "title": "💾 Critical Memory Usage",
        "severity": "critical",
    },
    "high_network": {
        "title": "📡 High Network Traffic (Data Exfiltration Risk)",
        "severity": "warning",
    },
    "brute_force": {
        "title": "🔐 Brute Force Attack Detected",
        "severity": "critical",
    },
}

alerts_generated = 0
alert_history: List[Alert] = []

def generate_alert(anomaly: AnomalySignal) -> Alert:
    global alerts_generated

    # Get template config or empty dict
    template_config = ALERT_TEMPLATES.get(anomaly.rule_id, {})

    # determining severity: default to anomaly severity if not in template
    severity = template_config.get("severity", anomaly.severity)

    # If it's an ML rule (starts with ml_) or explicitly crit, trust the anomaly
    if anomaly.rule_id.startswith("ml_") or anomaly.severity == "critical":
        severity = anomaly.severity

    template = {
        "title": template_config.get("title", f"⚠️ {anomaly.rule_name}"),
        "severity": severity,
    }

    source = anomaly.evidence.get("service", "Unknown Service")
    if not source or source == "Unknown Service":
        source = anomaly.evidence.get("source_ip", "Unknown")

    description = generate_description(anomaly)

    alert = Alert(
        id=str(uuid.uuid4()),
        title=template["title"],
        description=description,
        severity=template.get("severity", anomaly.severity),
        source=source,
        timestamp=datetime.utcnow().isoformat() + "Z",
        acknowledged=False,
        evidence=anomaly.evidence,
        recommendation=anomaly.recommendation,
        anomaly_id=anomaly.anomaly_id,
        rule_id=anomaly.rule_id,
    )

    alerts_generated += 1
    alert_history.append(alert)

    if len(alert_history) > 100:
        alert_history.pop(0)

    return alert

def generate_description(anomaly: AnomalySignal) -> str:
    evidence = anomaly.evidence

    if anomaly.rule_id == "sql_injection":
        fields = evidence.get("matched_fields", [])
        field_names = [f["field"] for f in fields] if fields else ["unknown field"]
        return f"Malicious SQL injection patterns detected in {', '.join(field_names)}. Source IP: {evidence.get('source_ip', 'unknown')}. This could be an attempt to extract or manipulate database data."

    elif anomaly.rule_id == "rate_spike":
        count = evidence.get("request_count", "unknown")
        ip = evidence.get("source_ip", "unknown")
        return f"Abnormal request rate detected: {count} requests from {ip} in the last minute. This could indicate a DDoS attack or aggressive scraping."

    elif anomaly.rule_id == "high_cpu":
        cpu = evidence.get("cpu_percent", "unknown")
        service = evidence.get("service", "unknown")
        return f"CPU utilization at {cpu}% on {service}. High CPU may cause service degradation or indicate a runaway process."

    elif anomaly.rule_id == "high_memory":
        memory = evidence.get("memory_percent", "unknown")
        service = evidence.get("service", "unknown")
        return f"Memory usage at {memory}% on {service}. Critical memory pressure may cause service crashes or system instability."

    elif anomaly.rule_id == "high_network":
        network = evidence.get("network_kbps", "unknown")
        return f"Network traffic spike detected at {network} KB/s. This could indicate data exfiltration or a flood attack."

    elif anomaly.rule_id == "brute_force":
        attempts = evidence.get("failed_attempts", "unknown")
        ip = evidence.get("source_ip", "unknown")
        username = evidence.get("username", "unknown")
        return f"Multiple failed authentication attempts ({attempts}) from {ip} targeting user '{username}'. Possible credential stuffing or brute force attack."

    else:
        return anomaly.description

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Alert Manager running on port {PORT}")
    print(f"Gateway URL: {API_GATEWAY_URL}")
    yield
    print("Alert Manager shutting down...")

app = FastAPI(
    title="Threat_Ops.ai - Alert Manager",
    description="Alert generation service",
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
        service="alert-manager",
        version="1.0.0",
        alerts_generated=alerts_generated
    )

@app.get("/alerts", tags=["Alerts"])
async def list_alerts(limit: int = 50):
    return {
        "alerts": alert_history[-limit:][::-1],
        "count": len(alert_history),
        "total_generated": alerts_generated
    }

@app.post("/internal/anomaly", tags=["Internal"])
async def receive_anomaly(anomaly: AnomalySignal):
    try:
        alert = generate_alert(anomaly)

        print(f"Alert generated: {alert.title} ({alert.severity})")

        await forward_to_gateway(alert)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{RESPONSE_ENGINE_URL}/execute",
                    json=alert.model_dump(),
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        execution = await resp.json()
                        actions = execution.get("actions_executed", 0)
                        if actions > 0:
                            print(f"Response Engine executed {actions} actions")
                    else:
                        print(f"Response Engine responded: {resp.status}")
        except Exception as e:
            print(f"Could not reach Response Engine: {e}")

        return {
            "status": "alert_generated",
            "alert_id": alert.id,
            "severity": alert.severity
        }

    except Exception as e:
        print(f"Alert generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def forward_to_gateway(alert: Alert):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_GATEWAY_URL}/internal/alert",
                json=alert.model_dump(),
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    print(f"Alert forwarded to gateway: {alert.id}")
                else:
                    print(f"Gateway responded: {resp.status}")
    except aiohttp.ClientError as e:
        print(f"Could not reach API Gateway: {e}")

@app.post("/alerts/{alert_id}/acknowledge", tags=["Alerts"])
async def acknowledge_alert(alert_id: str):
    for alert in alert_history:
        if alert.id == alert_id:
            alert.acknowledged = True
            return {"status": "acknowledged", "alert_id": alert_id}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.delete("/alerts", tags=["Alerts"])
async def clear_alerts():
    global alert_history
    alert_history = []
    return {"status": "cleared"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        reload=False
    )
