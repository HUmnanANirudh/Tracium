from datetime import datetime
from typing import Optional
from app.models import LogEntry, LogQueryParams, ServiceName
from app.incident_models import Incident, IncidentState, SecurityAlert


class LogStore:
    def __init__(self):
        self.logs: list[LogEntry] = []
        self.incidents: list[Incident] = []
        self.alerts: list[SecurityAlert] = []

    def ingest(self, logs: list[LogEntry]) -> int:
        self.logs.extend(logs)
        return len(logs)

    def query(self, params: LogQueryParams) -> list[dict]:
        results = []
        for log in reversed(self.logs):
            if params.service and log.service != params.service:
                continue
            if params.level and log.level != params.level:
                continue
            if params.userId and log.userId != params.userId:
                continue
            if params.ip and log.ip != params.ip:
                continue
            if params.start_time and log.timestamp < params.start_time:
                continue
            if params.end_time and log.timestamp > params.end_time:
                continue
            if params.search and params.search.lower() not in log.message.lower():
                continue

            results.append(log.model_dump(mode="json"))

            if len(results) >= params.limit + params.offset:
                break

        return results[params.offset : params.offset + params.limit]

    def get_services(self) -> list[str]:
        return [s.value for s in ServiceName]

    def add_incident(self, incident: Incident):
        self.incidents.append(incident)

    def add_alert(self, alert: SecurityAlert):
        self.alerts.append(alert)

    def get_incidents(
        self,
        service: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        results = []
        for inc in reversed(self.incidents):
            if service and inc.service != service:
                continue
            if state and inc.state.value != state:
                continue
            results.append(inc.model_dump(mode="json"))
            if len(results) >= limit:
                break
        return results

    def get_incident(self, incident_id: str) -> Optional[dict]:
        for inc in self.incidents:
            if inc.id == incident_id:
                return inc.model_dump(mode="json")
        return None

    def get_alerts(self, limit: int = 100) -> list[dict]:
        results = []
        for alert in reversed(self.alerts):
            results.append(alert.model_dump(mode="json"))
            if len(results) >= limit:
                break
        return results

    def update_incident_state(self, incident_id: str, new_state: IncidentState) -> bool:
        for inc in self.incidents:
            if inc.id == incident_id:
                inc.state = new_state
                return True
        return False


store = LogStore()