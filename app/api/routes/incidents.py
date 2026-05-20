from fastapi import Query
from typing import Optional
from pydantic import BaseModel
from app.incident_models import IncidentState
from app.log_store import store
from app.incident_engine import engine


class FalsePositiveRequest(BaseModel):
    reason: str
    suppress_seconds: Optional[int] = 3600


async def get_incidents(
    service: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = Query(default=100, le=500),
):
    return {"incidents": store.get_incidents(service=service, state=state, limit=limit)}


async def get_incident(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}, 404
    return {"incident": incident}


async def update_incident_state(incident_id: str, state: IncidentState):
    success = store.update_incident_state(incident_id, state)
    if not success:
        return {"error": "Incident not found"}, 404
    return {"status": "ok", "incident_id": incident_id, "state": state.value}


async def mark_false_positive(incident_id: str, body: FalsePositiveRequest):
    incident_data = store.get_incident(incident_id)
    if not incident_data:
        return {"error": "Incident not found"}, 404

    dedup_key = incident_data.get("deduplication_key")
    if dedup_key:
        engine.mark_false_positive(dedup_key, body.reason, body.suppress_seconds)

    success = store.update_incident_state(incident_id, IncidentState.FALSE_POSITIVE)
    if not success:
        return {"error": "Failed to update incident state"}, 500

    return {
        "status": "ok",
        "incident_id": incident_id,
        "reason": body.reason,
        "suppressed_for_seconds": body.suppress_seconds,
    }


async def get_incident_timeline(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}, 404
    return {"incident_id": incident_id, "timeline": incident.get("timeline", [])}


async def get_incident_related_logs(incident_id: str, limit: int = Query(default=50, le=200)):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}, 404

    dedup_key = incident.get("deduplication_key")
    service = incident.get("service")
    incident_type = incident.get("type")

    related = []
    seen_trace_ids = set()

    if dedup_key:
        dedup_parts = dedup_key.split(":")
        if len(dedup_parts) >= 3:
            if incident_type == "brute_force":
                ip = dedup_parts[-1]
                for log in reversed(store.logs):
                    if log.ip == ip and log.traceId not in seen_trace_ids:
                        related.append(log.model_dump(mode="json"))
                        seen_trace_ids.add(log.traceId)
                    if len(related) >= limit:
                        break
            elif incident_type == "auth_anomaly":
                userId = dedup_parts[-1]
                for log in reversed(store.logs):
                    if log.userId == userId and log.traceId not in seen_trace_ids:
                        related.append(log.model_dump(mode="json"))
                        seen_trace_ids.add(log.traceId)
                    if len(related) >= limit:
                        break

    if not related and service:
        for log in reversed(store.logs):
            if str(log.service) == service and log.traceId not in seen_trace_ids:
                related.append(log.model_dump(mode="json"))
                seen_trace_ids.add(log.traceId)
            if len(related) >= limit:
                break

    return {"incident_id": incident_id, "related_logs": related, "count": len(related)}


async def get_incident_root_cause(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}, 404

    inc_type = incident.get("type")
    severity = incident.get("severity")
    details = incident.get("details", {})
    timeline = incident.get("timeline", [])

    root_cause = {
        "incident_id": incident_id,
        "type": inc_type,
        "summary": incident.get("message"),
        "initial_event": None,
        "contributing_factors": [],
        "impact_assessment": {},
        "recommended_actions": [],
    }

    if timeline:
        root_cause["initial_event"] = {
            "timestamp": timeline[0].get("timestamp"),
            "service": timeline[0].get("service"),
            "message": timeline[0].get("message"),
        }

    if inc_type == "brute_force":
        root_cause["contributing_factors"] = [
            f"Multiple failed login attempts from IP: {details.get('ip')}",
            f"Attempt count: {details.get('attempts')}",
            "Insufficient account lockout policy",
        ]
        root_cause["recommended_actions"] = [
            "Block source IP at firewall",
            "Implement account lockout after N attempts",
            "Enable MFA for affected accounts",
            "Review access logs for successful breaches",
        ]
        root_cause["impact_assessment"] = {
            "account_compromise_risk": "HIGH",
            "lateral_movement_risk": "MEDIUM",
            "data_exposure_risk": "HIGH",
        }

    elif inc_type == "error_spike":
        root_cause["contributing_factors"] = [
            f"Error count in window: {details.get('count')}",
            "Service degradation detected",
        ]
        root_cause["recommended_actions"] = [
            "Check service health endpoints",
            "Review recent deployments",
            "Scale service if under resource pressure",
        ]
        root_cause["impact_assessment"] = {
            "service_availability": "DEGRADED",
            "user_impact": "MEDIUM",
        }

    elif inc_type == "latency_spike":
        root_cause["contributing_factors"] = [
            f"p99 latency: {details.get('p99_ms')}ms",
            f"Sample size: {details.get('sample_size')} requests",
        ]
        root_cause["recommended_actions"] = [
            "Check database query performance",
            "Review recent code changes",
            "Check下游 service dependencies",
        ]
        root_cause["impact_assessment"] = {
            "user_experience": "DEGRADED",
            "timeout_risk": "HIGH",
        }

    elif inc_type == "auth_anomaly":
        root_cause["contributing_factors"] = [
            f"Auth attempt at unusual hour: {details.get('hour')}:00",
            f"Target user: {details.get('userId')}",
        ]
        root_cause["recommended_actions"] = [
            "Verify user identity via alternate channel",
            "Temporary suspend account pending review",
            "Check for successful session logins",
        ]
        root_cause["impact_assessment"] = {
            "account_takeover_risk": "MEDIUM",
            "unauthorized_access_risk": "HIGH",
        }

    elif inc_type == "container_restart":
        root_cause["contributing_factors"] = [
            f"Previous start: {details.get('previous_start')}",
            "Container instability detected",
        ]
        root_cause["recommended_actions"] = [
            "Check container health logs",
            "Review resource limits",
            "Verify orchestration status",
        ]
        root_cause["impact_assessment"] = {
            "service_stability": "DEGRADED",
            "availability": "MEDIUM",
        }

    return root_cause