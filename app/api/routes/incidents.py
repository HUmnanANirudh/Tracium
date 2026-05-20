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