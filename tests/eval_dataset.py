from app.incident_models import Incident, IncidentType, IncidentSeverity
from app.models import LogEntry, LogLevel, ServiceName
from datetime import datetime

# Scenario 1: True Positive Brute Force
brute_force_incident = Incident(
    id="inc-bf-1",
    type=IncidentType.BRUTE_FORCE,
    severity=IncidentSeverity.HIGH,
    service="auth",
    message="Multiple failed logins followed by success",
    details={"ip": "203.0.113.5", "userId": "user123", "attempts": 10},
)
brute_force_logs = [
    LogEntry(service=ServiceName.AUTH, level=LogLevel.ERROR, message="Failed login", ip="203.0.113.5", userId="user123")
    for _ in range(10)
] + [
    LogEntry(service=ServiceName.AUTH, level=LogLevel.INFO, message="Successful login", ip="203.0.113.5", userId="user123")
]

# Scenario 2: False Positive - Internal Security Scanner
fp_incident = Incident(
    id="inc-fp-1",
    type=IncidentType.SECURITY_ALERT,
    severity=IncidentSeverity.HIGH,
    service="backend",
    message="Suspicious shell execution",
    details={"ip": "10.0.0.5", "userId": "admin", "cmd": "whoami"},
)
fp_logs = [
    LogEntry(service=ServiceName.BACKEND, level=LogLevel.WARNING, message="Shell command: whoami", ip="10.0.0.5", userId="admin")
]

EVAL_DATASET = [
    {
        "scenario": "true_positive_brute_force",
        "incident": brute_force_incident,
        "logs": brute_force_logs,
        "expected_verdict": "true_positive"
    },
    {
        "scenario": "false_positive_internal_scanner",
        "incident": fp_incident,
        "logs": fp_logs,
        "expected_verdict": "false_positive"
    }
]
