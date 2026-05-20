from datetime import datetime, timedelta
from collections import defaultdict
from app.models import LogEntry, LogLevel, ServiceName
from app.incident_models import Incident, IncidentSeverity, IncidentType, SecurityAlert


class IncidentEngine:
    def __init__(self):
        self.failed_logins: dict[str, list[datetime]] = defaultdict(list)
        self.error_counts: dict[str, list[tuple[datetime, int]]] = defaultdict(list)
        self.latency_samples: dict[str, list[float]] = defaultdict(list)
        self.last_error_time: dict[str, datetime] = {}
        self.restart_timestamps: dict[str, datetime] = {}

    def check_brute_force(self, log: LogEntry) -> tuple[Incident | None, SecurityAlert | None]:
        if log.service != ServiceName.AUTH or log.level != LogLevel.ERROR:
            return None, None
        if "failed" not in log.message.lower() and "invalid" not in log.message.lower():
            return None, None

        ip = log.ip or "unknown"
        now = datetime.utcnow()
        window = now - timedelta(minutes=5)

        self.failed_logins[ip] = [
            t for t in self.failed_logins[ip] if t > window
        ]
        self.failed_logins[ip].append(now)

        if len(self.failed_logins[ip]) >= 5:
            incident = Incident(
                id=f"bf-{ip}-{now.strftime('%Y%m%d%H%M%S')}",
                type=IncidentType.BRUTE_FORCE,
                severity=IncidentSeverity.HIGH,
                service=str(log.service),
                message=f"Brute force detected: {len(self.failed_logins[ip])} failed login attempts from {ip}",
                timestamp=now,
                details={"ip": ip, "attempts": len(self.failed_logins[ip]), "window": "5min"},
            )
            alert = SecurityAlert(
                id=f"alert-bf-{now.strftime('%Y%m%d%H%M%S')}",
                type="brute_force",
                severity=IncidentSeverity.HIGH,
                sourceIp=ip,
                userId=log.userId,
                message=incident.message,
                timestamp=now,
                details={"attempts": len(self.failed_logins[ip])},
            )
            self.failed_logins[ip] = []
            return incident, alert

        return None, None

    def check_auth_anomaly(self, log: LogEntry) -> Incident | None:
        if log.service != ServiceName.AUTH or log.level != LogLevel.ERROR:
            return None

        hour = datetime.utcnow().hour
        is_off_hours = hour < 6 or hour > 22

        if is_off_hours and ("auth" in log.message.lower() or "token" in log.message.lower()):
            return Incident(
                id=f"auth-ano-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                type=IncidentType.AUTH_ANOMALY,
                severity=IncidentSeverity.MEDIUM,
                service=str(log.service),
                message=f"Off-hours authentication failure detected",
                timestamp=datetime.utcnow(),
                details={"hour": hour, "userId": log.userId},
            )
        return None

    def check_error_spike(self, log: LogEntry) -> Incident | None:
        if log.level not in (LogLevel.ERROR, LogLevel.CRITICAL):
            return None

        service = str(log.service)
        now = datetime.utcnow()
        window = now - timedelta(minutes=1)

        self.error_counts[service] = [
            (t, c) for t, c in self.error_counts[service] if t > window
        ]
        current_count = sum(c for _, c in self.error_counts[service])
        self.error_counts[service].append((now, 1))

        if current_count >= 10:
            return Incident(
                id=f"err-spike-{service}-{now.strftime('%Y%m%d%H%M%S')}",
                type=IncidentType.ERROR_SPike,
                severity=IncidentSeverity.HIGH,
                service=service,
                message=f"Error spike: {current_count} errors in last minute",
                timestamp=now,
                details={"count": current_count},
            )
        return None

    def check_latency_spike(self, log: LogEntry) -> Incident | None:
        if log.latencyMs is None or log.service != ServiceName.BACKEND:
            return None

        service = str(log.service)
        now = datetime.utcnow()

        self.latency_samples[service].append(log.latencyMs)
        if len(self.latency_samples[service]) > 100:
            self.latency_samples[service] = self.latency_samples[service][-100:]

        if len(self.latency_samples[service]) >= 20:
            sorted_latencies = sorted(self.latency_samples[service])
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]

            if p99 > 2000:
                return Incident(
                    id=f"lat-spike-{service}-{now.strftime('%Y%m%d%H%M%S')}",
                    type=IncidentType.LATENCY_SPike,
                    severity=IncidentSeverity.MEDIUM,
                    service=service,
                    message=f"Latency spike: p99={p99:.0f}ms exceeds 2000ms threshold",
                    timestamp=now,
                    details={"p99_ms": p99, "sample_size": len(self.latency_samples[service])},
                )
        return None

    def check_container_restart(self, log: LogEntry) -> Incident | None:
        service = str(log.service)
        now = datetime.utcnow()

        if log.level == LogLevel.INFO and "started" in log.message.lower():
            if service in self.restart_timestamps:
                prev = self.restart_timestamps[service]
                if (now - prev) < timedelta(minutes=5):
                    incident = Incident(
                        id=f"restart-{service}-{now.strftime('%Y%m%d%H%M%S')}",
                        type=IncidentType.CONTAINER_RESTART,
                        severity=IncidentSeverity.LOW,
                        service=service,
                        message=f"Container restart detected for {service}",
                        timestamp=now,
                        details={"previous_start": prev.isoformat()},
                    )
                    self.restart_timestamps[service] = now
                    return incident
            self.restart_timestamps[service] = now
        return None

    def analyze(self, log: LogEntry) -> tuple[list[Incident], list[SecurityAlert]]:
        incidents = []
        alerts = []

        for check in [
            self.check_brute_force,
            self.check_auth_anomaly,
            self.check_error_spike,
            self.check_latency_spike,
            self.check_container_restart,
        ]:
            result = check(log)
            if result:
                if isinstance(result, tuple):
                    inc, alert = result
                    if inc:
                        incidents.append(inc)
                    if alert:
                        alerts.append(alert)
                else:
                    incidents.append(result)

        return incidents, alerts


engine = IncidentEngine()