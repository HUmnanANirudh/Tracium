import json
from datetime import datetime
from pydantic import BaseModel, Field

class AuditEvent(BaseModel):
    run_id: str
    actor: str = "system"
    event_type: str
    details: dict
    timestamp: datetime = Field(default_factory=datetime.now)

class AuditStore:
    def __init__(self):
        self.events: list[AuditEvent] = []
        
    def record(self, run_id: str, event_type: str, details: dict, actor: str = "system"):
        event = AuditEvent(
            run_id=run_id,
            actor=actor,
            event_type=event_type,
            details=details
        )
        self.events.append(event)
        # In a real app, this would log to Loki or a database
        print(f"[AUDIT] {event.timestamp.isoformat()} | {actor} | {event_type} | {json.dumps(details)}")

audit_store = AuditStore()
