from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fnmatch import fnmatch
from app.models import LogEntry, LogLevel, ServiceName
from app.incident_models import Incident, IncidentSeverity, IncidentType, IncidentState, SecurityAlert, SuppressionRule, TimelineEntry


DEDUP_WINDOW_SECS = 300
SUPPRESSION_DEFAULT_SECS = 3600 
TIMELINE_WINDOW_SECS = 300


class DeduplicationTracker:
    def __init__(self):
        self.active: dict[str, tuple[Incident, datetime]] = {}
        self.suppressions: list[SuppressionRule] = []
        self.timeline_events: dict[str, list[LogEntry]] = defaultdict(list)

    def get_key(self, incident_type: IncidentType, service: str, details: dict) -> str:
        if incident_type == IncidentType.BRUTE_FORCE:
            return f"brute_force:{service}:{details.get('ip', 'unknown')}"
        elif incident_type == IncidentType.ERROR_SPike:
            return f"error_spike:{service}"
        elif incident_type == IncidentType.LATENCY_SPike:
            return f"latency_spike:{service}"
        elif incident_type == IncidentType.AUTH_ANOMALY:
            return f"auth_anomaly:{service}:{details.get('userId', 'unknown')}"
        elif incident_type == IncidentType.CONTAINER_RESTART:
            return f"container_restart:{service}"
        return f"{incident_type.value}:{service}"

    def is_suppressed(self, dedup_key: str) -> tuple[bool, str | None]:
        now = datetime.now(timezone.utc)
        self.suppressions = [s for s in self.suppressions if s.suppressed_until > now]

        for rule in self.suppressions:
            if fnmatch(dedup_key, rule.dedup_key_pattern):
                return True, rule.reason
        return False, None

    def suppress(self, pattern: str, seconds: int, reason: str, created_by: str = "system"):
        rule = SuppressionRule(
            dedup_key_pattern=pattern,
            suppressed_until=datetime.now(timezone.utc) + timedelta(seconds=seconds),
            reason=reason,
            created_by=created_by,
        )
        self.suppressions.append(rule)
        return rule

    def add_timeline_event(self, dedup_key: str, log: LogEntry):
        self.timeline_events[dedup_key].append(log)
        self.cleanup_timeline()

    def cleanup_timeline(self):
        threshold = datetime.now(timezone.utc) - timedelta(seconds=TIMELINE_WINDOW_SECS)
        for key in list(self.timeline_events.keys()):
            self.timeline_events[key] = [
                e for e in self.timeline_events[key]
                if e.timestamp > threshold
            ]
            if not self.timeline_events[key]:
                del self.timeline_events[key]

    def get_timeline(self, dedup_key: str) -> list[TimelineEntry]:
        events = self.timeline_events.get(dedup_key, [])
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        entries = []
        for seq, log in enumerate(sorted_events, start=1):
            entry = TimelineEntry(
                timestamp=log.timestamp,
                sequence=seq,
                service=str(log.service),
                level=log.level.value,
                message=log.message,
                traceId=log.traceId,
                userId=log.userId,
                ip=log.ip,
                metadata=log.metadata,
            )
            entries.append(entry)
        return entries

    def try_aggregate(self, dedup_key: str, incident: Incident) -> tuple[bool, Incident | None]:
        now = datetime.now(timezone.utc)
        window = now - timedelta(seconds=DEDUP_WINDOW_SECS)

        if dedup_key in self.active:
            existing, first_seen = self.active[dedup_key]
            if first_seen > window:
                existing.event_count += incident.event_count
                if incident.details.get("count"):
                    existing.details["count"] = max(
                        existing.details.get("count", 0),
                        incident.details.get("count", 0)
                    )
                existing.timeline = self.get_timeline(dedup_key)
                return True, existing

        self.active[dedup_key] = (incident, now)
        self.cleanup(window)
        return False, None

    def cleanup(self, threshold: datetime):
        expired = [k for k, (_, t) in self.active.items() if t <= threshold]
        for k in expired:
            del self.active[k]
            if k in self.timeline_events:
                del self.timeline_events[k]


class IncidentEngine:
    def __init__(self):
        self.failed_logins: dict[str, list[datetime]] = defaultdict(list)
        self.error_counts: dict[str, list[tuple[datetime, int]]] = defaultdict(list)
        self.latency_samples: dict[str, list[float]] = defaultdict(list)
        self.restart_timestamps: dict[str, datetime] = {}
        self.dedup = DeduplicationTracker()
        self.false_positive_history: dict[str, int] = defaultdict(int)

    def calculate_confidence(self, incident: Incident, dedup_key: str) -> float:
        base_score = 1.0

        if incident.type == IncidentType.BRUTE_FORCE:
            attempts = incident.details.get("attempts", 1)
            if attempts >= 10:
                base_score = 0.95
            elif attempts >= 5:
                base_score = 0.8

        elif incident.type == IncidentType.ERROR_SPike:
            count = incident.details.get("count", 1)
            if count >= 20:
                base_score = 0.9
            elif count >= 10:
                base_score = 0.75

        elif incident.type == IncidentType.LATENCY_SPike:
            p99 = incident.details.get("p99_ms", 0)
            if p99 > 5000:
                base_score = 0.9
            elif p99 > 2000:
                base_score = 0.7

        fp_count = self.false_positive_history.get(dedup_key, 0)
        if fp_count == 1:
            base_score *= 0.7
        elif fp_count == 2:
            base_score *= 0.4
        elif fp_count >= 3:
            base_score *= 0.1

        return round(base_score, 2)

    def mark_false_positive(self, dedup_key: str, reason: str, suppress_seconds: int = SUPPRESSION_DEFAULT_SECS):
        self.dedup.suppress(dedup_key, suppress_seconds, reason)
        self.false_positive_history[dedup_key] += 1

    def build_timeline(self, dedup_key: str) -> list[TimelineEntry]:
        return self.dedup.get_timeline(dedup_key)

    def check_brute_force(self, log: LogEntry) -> tuple[Incident | None, SecurityAlert | None, str | None]:
        if log.service != ServiceName.AUTH or log.level != LogLevel.ERROR:
            return None, None, None
        if "failed" not in log.message.lower() and "invalid" not in log.message.lower():
            return None, None, None

        ip = log.ip or "unknown"
        dedup_key = f"brute_force:auth:{ip}"

        if self.dedup.is_suppressed(dedup_key)[0]:
            return None, None, None

        self.dedup.add_timeline_event(dedup_key, log)

        now = datetime.now(timezone.utc)
        window = now - timedelta(minutes=5)

        self.failed_logins[ip] = [t for t in self.failed_logins[ip] if t > window]
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
                deduplication_key=dedup_key,
            )
            incident.confidence_score = self.calculate_confidence(incident, dedup_key)
            incident.timeline = self.build_timeline(dedup_key)
            self.failed_logins[ip] = []

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
            return incident, alert, dedup_key

        return None, None, None

    def check_auth_anomaly(self, log: LogEntry) -> tuple[Incident | None, str | None]:
        if log.service != ServiceName.AUTH or log.level != LogLevel.ERROR:
            return None, None

        dedup_key = f"auth_anomaly:auth:{log.userId or 'unknown'}"
        if self.dedup.is_suppressed(dedup_key)[0]:
            return None, None

        self.dedup.add_timeline_event(dedup_key, log)

        hour = datetime.now(timezone.utc).hour
        is_off_hours = hour < 6 or hour > 22

        if is_off_hours and ("auth" in log.message.lower() or "token" in log.message.lower()):
            now = datetime.now(timezone.utc)
            incident = Incident(
                id=f"auth-ano-{now.strftime('%Y%m%d%H%M%S')}",
                type=IncidentType.AUTH_ANOMALY,
                severity=IncidentSeverity.MEDIUM,
                service=str(log.service),
                message=f"Off-hours authentication failure detected",
                timestamp=now,
                details={"hour": hour, "userId": log.userId},
                deduplication_key=dedup_key,
            )
            incident.confidence_score = self.calculate_confidence(incident, dedup_key)
            incident.timeline = self.build_timeline(dedup_key)
            return incident, dedup_key

        return None, None

    def check_error_spike(self, log: LogEntry) -> tuple[Incident | None, str | None]:
        if log.level not in (LogLevel.ERROR, LogLevel.CRITICAL):
            return None, None

        service = str(log.service)
        dedup_key = f"error_spike:{service}"

        if self.dedup.is_suppressed(dedup_key)[0]:
            return None, None

        self.dedup.add_timeline_event(dedup_key, log)

        now = datetime.now(timezone.utc)
        window = now - timedelta(minutes=1)

        self.error_counts[service] = [(t, c) for t, c in self.error_counts[service] if t > window]
        current_count = sum(c for _, c in self.error_counts[service])
        self.error_counts[service].append((now, 1))

        if current_count >= 10:
            incident = Incident(
                id=f"err-spike-{service}-{now.strftime('%Y%m%d%H%M%S')}",
                type=IncidentType.ERROR_SPike,
                severity=IncidentSeverity.HIGH,
                service=service,
                message=f"Error spike: {current_count} errors in last minute",
                timestamp=now,
                details={"count": current_count},
                deduplication_key=dedup_key,
            )
            incident.confidence_score = self.calculate_confidence(incident, dedup_key)
            incident.timeline = self.build_timeline(dedup_key)
            return incident, dedup_key

        return None, None

    def check_latency_spike(self, log: LogEntry) -> tuple[Incident | None, str | None]:
        if log.latencyMs is None or log.service != ServiceName.BACKEND:
            return None, None

        service = str(log.service)
        dedup_key = f"latency_spike:{service}"

        if self.dedup.is_suppressed(dedup_key)[0]:
            return None, None

        self.dedup.add_timeline_event(dedup_key, log)

        now = datetime.now(timezone.utc)

        self.latency_samples[service].append(log.latencyMs)
        if len(self.latency_samples[service]) > 100:
            self.latency_samples[service] = self.latency_samples[service][-100:]

        if len(self.latency_samples[service]) >= 20:
            sorted_latencies = sorted(self.latency_samples[service])
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]

            if p99 > 2000:
                incident = Incident(
                    id=f"lat-spike-{service}-{now.strftime('%Y%m%d%H%M%S')}",
                    type=IncidentType.LATENCY_SPike,
                    severity=IncidentSeverity.MEDIUM,
                    service=service,
                    message=f"Latency spike: p99={p99:.0f}ms exceeds 2000ms threshold",
                    timestamp=now,
                    details={"p99_ms": p99, "sample_size": len(self.latency_samples[service])},
                    deduplication_key=dedup_key,
                )
                incident.confidence_score = self.calculate_confidence(incident, dedup_key)
                incident.timeline = self.build_timeline(dedup_key)
                return incident, dedup_key

        return None, None

    def check_container_restart(self, log: LogEntry) -> tuple[Incident | None, str | None]:
        service = str(log.service)
        dedup_key = f"container_restart:{service}"

        if self.dedup.is_suppressed(dedup_key)[0]:
            return None, None

        self.dedup.add_timeline_event(dedup_key, log)

        now = datetime.now(timezone.utc)

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
                        deduplication_key=dedup_key,
                    )
                    incident.confidence_score = self.calculate_confidence(incident, dedup_key)
                    incident.timeline = self.build_timeline(dedup_key)
                    self.restart_timestamps[service] = now
                    return incident, dedup_key
            self.restart_timestamps[service] = now

        return None, None

    def analyze(self, log: LogEntry) -> tuple[list[Incident], list[SecurityAlert]]:
        incidents = []
        alerts = []

        checks = [
            ("brute_force", self.check_brute_force),
            ("auth_anomaly", self.check_auth_anomaly),
            ("error_spike", self.check_error_spike),
            ("latency_spike", self.check_latency_spike),
            ("container_restart", self.check_container_restart),
        ]

        for name, check in checks:
            result = check(log)
            if not result[0]:
                continue

            incident, *rest = result
            dedup_key = rest[-1] if rest else None

            if dedup_key:
                was_aggregated, existing = self.dedup.try_aggregate(dedup_key, incident)
                if was_aggregated and existing:
                    incidents.append(existing)
                    continue

            incidents.append(incident)
            if name == "brute_force" and rest:
                alerts.append(rest[0])

        return incidents, alerts


engine = IncidentEngine()