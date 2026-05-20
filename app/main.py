from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models import LogIngestRequest, LogQueryParams, LogLevel, ServiceName
from app.incident_models import IncidentSeverity, IncidentState, SuppressionRule
from app.log_store import store
from app.incident_engine import engine

app = FastAPI(title="Tracium", description="Log Aggregation & Incident Correlation System")


class FalsePositiveRequest(BaseModel):
    reason: str
    suppress_seconds: Optional[int] = 3600


class SuppressionRequest(BaseModel):
    pattern: str
    seconds: int = 3600
    reason: str


@app.post("/logs/ingest")
async def ingest_logs(request: LogIngestRequest):
    ingested = store.ingest(request.logs)

    for log in request.logs:
        incidents, alerts = engine.analyze(log)
        for inc in incidents:
            store.add_incident(inc)
        for alert in alerts:
            store.add_alert(alert)

    return {"status": "ok", "ingested": ingested}


@app.get("/logs/query")
async def query_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    search: Optional[str] = None,
    userId: Optional[str] = None,
    ip: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
):
    params = LogQueryParams(
        service=ServiceName(service) if service else None,
        level=LogLevel(level) if level else None,
        start_time=start_time,
        end_time=end_time,
        search=search,
        userId=userId,
        ip=ip,
        limit=limit,
        offset=offset,
    )
    return {"logs": store.query(params), "count": len(store.query(params))}


@app.get("/logs/services")
async def get_services():
    return {"services": store.get_services()}


@app.get("/incidents")
async def get_incidents(
    service: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = Query(default=100, le=500),
):
    return {"incidents": store.get_incidents(service=service, state=state, limit=limit)}


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    incident = store.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}, 404
    return {"incident": incident}


@app.patch("/incidents/{incident_id}/state")
async def update_incident_state(incident_id: str, state: IncidentState):
    success = store.update_incident_state(incident_id, state)
    if not success:
        return {"error": "Incident not found"}, 404
    return {"status": "ok", "incident_id": incident_id, "state": state.value}


@app.post("/incidents/{incident_id}/false-positive")
async def mark_false_positive(
    incident_id: str,
    body: FalsePositiveRequest = Body(...),
):
    incident_data = store.get_incident(incident_id)
    if not incident_data:
        return {"error": "Incident not found"}, 404

    dedup_key = incident_data.get("deduplication_key")
    if dedup_key:
        engine.mark_false_positive(dedup_key, body.reason, body.suppress_seconds)

    success = store.update_incident_state(incident_id, IncidentState.FALSE_POSITIVE)
    if not success:
        return {"error": "Failed to update incident state"}, 500

    incident = store.get_incident(incident_id)
    incident["false_positive_reason"] = body.reason
    return {
        "status": "ok",
        "incident_id": incident_id,
        "reason": body.reason,
        "suppressed_for_seconds": body.suppress_seconds,
    }


@app.post("/suppressions")
async def create_suppression(body: SuppressionRequest):
    rule = engine.dedup.suppress(
        pattern=body.pattern,
        seconds=body.seconds,
        reason=body.reason,
    )
    return {"status": "ok", "rule": rule.model_dump()}


@app.get("/suppressions")
async def get_suppressions():
    return {"suppressions": engine.dedup.suppressions}


@app.get("/alerts/security")
async def get_security_alerts(limit: int = Query(default=100, le=500)):
    return {"alerts": store.get_alerts(limit=limit)}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": store.get_services(),
        "stats": {
            "total_logs": len(store.logs),
            "total_incidents": len(store.incidents),
            "total_alerts": len(store.alerts),
        },
    }