import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp

from rules import run_all_rules, AnomalySignal

PORT = int(os.environ.get("PORT", 8002))
ALERT_MANAGER_URL = os.environ.get("ALERT_MANAGER_URL", "http://localhost:8003")

class TelemetryEvent(BaseModel):
    event_id: str
    source_ip: str
    domain: str = "general"
    service: str
    event_type: str
    payload: dict = {}
    timestamp: int
    received_at: str = None

class AnomalyOutput(BaseModel):
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

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "detection-engine"
    version: str = "1.0.0"
    rules_loaded: int = 0

class AnalyzeResponse(BaseModel):
    event_id: str
    anomalies_detected: int
    anomalies: List[AnomalyOutput]

@asynccontextmanager
async def lifespan(app: FastAPI):
    from rules import DETECTION_RULES
    print(f"Detection Engine running on port {PORT}")
    print(f"Rules loaded: {len(DETECTION_RULES)}")
    print(f"Alert Manager URL: {ALERT_MANAGER_URL}")
    yield
    print("Detection Engine shutting down...")

app = FastAPI(
    title="Threat_Ops.ai - Detection Engine",
    description="Rule-based anomaly detection service",
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
    from rules import DETECTION_RULES
    return HealthResponse(
        status="healthy",
        service="detection-engine",
        version="1.0.0",
        rules_loaded=len(DETECTION_RULES)
    )

@app.get("/rules", tags=["Rules"])
async def list_rules():
    from rules import DETECTION_RULES
    return {
        "rules": [
            {"id": rule_id, "name": rule_func.__name__}
            for rule_id, rule_func in DETECTION_RULES
        ],
        "count": len(DETECTION_RULES)
    }

@app.post("/analyze", response_model=AnalyzeResponse, tags=["Detection"])
async def analyze_event(event: TelemetryEvent):
    try:
        event_dict = event.model_dump()
        anomaly_signals = run_all_rules(event_dict)

        anomalies = []
        for signal in anomaly_signals:
            anomaly_id = str(uuid.uuid4())

            anomaly = AnomalyOutput(
                anomaly_id=anomaly_id,
                rule_id=signal.rule_id,
                rule_name=signal.rule_name,
                severity=signal.severity,
                confidence=signal.confidence,
                description=signal.description,
                evidence=signal.evidence,
                recommendation=signal.recommendation,
                source_event_id=event.event_id,
                detected_at=datetime.utcnow().isoformat() + "Z"
            )
            anomalies.append(anomaly)

            print(f"Anomaly detected: {signal.rule_name} ({signal.severity})")

        if anomalies:
            await forward_to_alert_manager(anomalies)

        return AnalyzeResponse(
            event_id=event.event_id,
            anomalies_detected=len(anomalies),
            anomalies=anomalies
        )

    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def forward_to_alert_manager(anomalies: List[AnomalyOutput]):
    try:
        async with aiohttp.ClientSession() as session:
            for anomaly in anomalies:
                async with session.post(
                    f"{ALERT_MANAGER_URL}/internal/anomaly",
                    json=anomaly.model_dump(),
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        print(f"Forwarded anomaly to alert manager: {anomaly.anomaly_id}")
                    else:
                        print(f"Alert manager responded: {resp.status}")
    except aiohttp.ClientError as e:
        print(f"Could not reach alert manager: {e}")

@app.post("/analyze/batch", tags=["Detection"])
async def analyze_batch(events: List[TelemetryEvent]):
    results = []
    total_anomalies = 0

    for event in events:
        event_dict = event.model_dump()
        anomaly_signals = run_all_rules(event_dict)

        for signal in anomaly_signals:
            anomaly_id = str(uuid.uuid4())
            results.append({
                "event_id": event.event_id,
                "anomaly_id": anomaly_id,
                "rule_id": signal.rule_id,
                "severity": signal.severity,
            })
            total_anomalies += 1

    return {
        "events_analyzed": len(events),
        "anomalies_detected": total_anomalies,
        "anomalies": results
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        reload=False
    )
