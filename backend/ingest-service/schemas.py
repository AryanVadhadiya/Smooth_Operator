"""
Threat_Ops.ai - Ingest Service Schemas
Pydantic models for telemetry event validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class EventType(str, Enum):
    """Supported event types"""
    HTTP_REQUEST = "http_request"
    AUTH_ATTEMPT = "auth_attempt"
    NETWORK_FLOW = "network_flow"
    SYSTEM_METRIC = "system_metric"
    FILE_ACCESS = "file_access"
    PROCESS_EXEC = "process_exec"
    DATABASE_QUERY = "database_query"
    API_CALL = "api_call"


class DomainType(str, Enum):
    """Supported domain types"""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    INFRASTRUCTURE = "infrastructure"
    IOT = "iot"
    GENERAL = "general"


class TelemetryEventInput(BaseModel):
    """
    Input schema for incoming telemetry events.
    event_id and timestamp are optional (auto-generated if not provided).
    """
    event_id: Optional[str] = Field(default=None, description="Unique event ID (auto-generated if not provided)")
    source_ip: str = Field(..., description="Source IP address", examples=["192.168.1.12"])
    domain: str = Field(default="general", description="Event domain", examples=["healthcare"])
    service: str = Field(..., description="Service name", examples=["patient-api"])
    event_type: str = Field(..., description="Type of event", examples=["http_request"])
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload data")
    timestamp: Optional[int] = Field(default=None, description="Unix timestamp (auto-generated if not provided)")

    class Config:
        json_schema_extra = {
            "example": {
                "source_ip": "192.168.1.12",
                "domain": "healthcare",
                "service": "patient-api",
                "event_type": "http_request",
                "payload": {
                    "method": "POST",
                    "path": "/api/patients/123",
                    "status_code": 200,
                    "user_agent": "Mozilla/5.0"
                }
            }
        }


class TelemetryEvent(BaseModel):
    """
    Normalized telemetry event with auto-generated fields.
    This is what gets stored and emitted.
    """
    event_id: str = Field(..., description="Unique event ID")
    source_ip: str = Field(..., description="Source IP address")
    domain: str = Field(..., description="Event domain")
    service: str = Field(..., description="Service name")
    event_type: str = Field(..., description="Type of event")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload data")
    timestamp: int = Field(..., description="Unix timestamp")
    received_at: str = Field(..., description="ISO timestamp when event was received")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "source_ip": "192.168.1.12",
                "domain": "healthcare",
                "service": "patient-api",
                "event_type": "http_request",
                "payload": {
                    "method": "POST",
                    "path": "/api/patients/123",
                    "status_code": 200
                },
                "timestamp": 1710000000,
                "received_at": "2024-03-09T12:00:00.000Z"
            }
        }


class IngestResponse(BaseModel):
    """Response after successful ingestion"""
    success: bool = True
    event_id: str
    message: str = "Event ingested successfully"


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "ingest-service"
    version: str = "1.0.0"
    events_ingested: int = 0
