from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    BRUTE_FORCE = "brute_force"
    AUTH_ANOMALY = "auth_anomaly"
    ERROR_SPike = "error_spike"
    LATENCY_SPike = "latency_spike"
    CONTAINER_RESTART = "container_restart"
    SECURITY_ALERT = "security_alert"


class Incident(BaseModel):
    id: str
    type: IncidentType
    severity: IncidentSeverity
    service: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict = Field(default_factory=dict)
    resolved: bool = False


class SecurityAlert(BaseModel):
    id: str
    type: str
    severity: IncidentSeverity
    sourceIp: str
    userId: Optional[str] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict = Field(default_factory=dict)