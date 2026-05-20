from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class IncidentState(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


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


class TimelineEntry(BaseModel):
    timestamp: datetime
    sequence: int
    service: str
    level: str
    message: str
    traceId: Optional[str] = None
    userId: Optional[str] = None
    ip: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class Incident(BaseModel):
    id: str
    type: IncidentType
    severity: IncidentSeverity
    state: IncidentState = IncidentState.OPEN
    service: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: dict = Field(default_factory=dict)
    event_count: int = 1
    deduplication_key: Optional[str] = None
    confidence_score: float = 1.0
    false_positive_reason: Optional[str] = None
    suppressed_until: Optional[datetime] = None
    timeline: list[TimelineEntry] = Field(default_factory=list)


class SecurityAlert(BaseModel):
    id: str
    type: str
    severity: IncidentSeverity
    sourceIp: str
    userId: Optional[str] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: dict = Field(default_factory=dict)


class SuppressionRule(BaseModel):
    dedup_key_pattern: str
    suppressed_until: datetime
    reason: str
    created_by: str = "system"
    created_at: datetime = Field(default_factory=datetime.now)