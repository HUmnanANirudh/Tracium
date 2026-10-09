import json
import os
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
        self.log_dir = os.getenv("LOG_DIR", "services/logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "audit.log")
        
    def record(self, run_id: str, event_type: str, details: dict, actor: str = "system"):
        event = AuditEvent(
            run_id=run_id,
            actor=actor,
            event_type=event_type,
            details=details
        )
        self.events.append(event)
        
        # Write to file for Promtail/Loki
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "level": "info",
            "service": "agent_audit",
            "run_id": run_id,
            "actor": actor,
            "event_type": event_type,
            "details": details
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Failed to write audit log: {e}")
            
        print(f"[AUDIT] {event.timestamp.isoformat()} | {actor} | {event_type} | {json.dumps(details)}")

audit_store = AuditStore()
