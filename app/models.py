from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ServiceName(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    AUTH = "auth"
    WORKER = "worker"


from uuid import uuid4

class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    service: ServiceName
    level: LogLevel
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str
    userId: Optional[str] = None
    ip: Optional[str] = None
    traceId: Optional[str] = None
    eventType: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    statusCode: Optional[int] = None
    latencyMs: Optional[float] = None
    endpoint: Optional[str] = None


class LogIngestRequest(BaseModel):
    logs: list[LogEntry]


class LogQueryParams(BaseModel):
    service: Optional[ServiceName] = None
    level: Optional[LogLevel] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    search: Optional[str] = None
    userId: Optional[str] = None
    ip: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0)