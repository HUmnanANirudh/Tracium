from fastapi import FastAPI, Query
from datetime import datetime
from typing import Optional

from app.models import LogIngestRequest, LogQueryParams, LogLevel, ServiceName
from app.incident_models import IncidentSeverity, IncidentState
from app.log_store import store
from app.incident_engine import engine

app = FastAPI(title="Tracium", description="Log Aggregation & Incident Correlation System")


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