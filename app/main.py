from fastapi import FastAPI, Query, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from collections import defaultdict
from time import time
import threading

from app.models import LogIngestRequest, LogQueryParams, LogLevel, ServiceName
from app.incident_models import IncidentState
from app.log_store import store
from app.incident_engine import engine

app = FastAPI(title="Tracium", description="Log Aggregation & Incident Correlation System")


MAX_PAYLOAD_SIZE_BYTES = 1_048_576  # 1MB
MAX_LOGS_PER_REQUEST = 1000
RATE_LIMIT_WINDOW_SECS = 60
RATE_LIMIT_MAX_REQUESTS = 60
RATE_LIMIT_MAX_LOGS = 5000


class RateLimiter:
    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.log_counts: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._lock = threading.Lock()

    def _clean_old(self, bucket: list, window: int):
        now = time()
        bucket[:] = [t for t in bucket if now - t < window]

    def check_rate_limit(self, client_id: str, log_count: int) -> tuple[bool, str]:
        now = time()
        window = RATE_LIMIT_WINDOW_SECS

        with self._lock:
            self._clean_old(self.requests[client_id], window)
            self.log_counts[client_id][:] = [(t, c) for t, c in self.log_counts[client_id] if now - t < window]

            total_logs = sum(c for _, c in self.log_counts[client_id])

            if len(self.requests[client_id]) >= RATE_LIMIT_MAX_REQUESTS:
                return False, f"Rate limit: max {RATE_LIMIT_MAX_REQUESTS} requests per {window}s"

            if total_logs + log_count > RATE_LIMIT_MAX_LOGS:
                return False, f"Rate limit: max {RATE_LIMIT_MAX_LOGS} logs per {window}s"

            self.requests[client_id].append(now)
            self.log_counts[client_id].append((now, log_count))

        return True, ""


rate_limiter = RateLimiter()


class FalsePositiveRequest(BaseModel):
    reason: str
    suppress_seconds: Optional[int] = 3600


class SuppressionRequest(BaseModel):
    pattern: str
    seconds: int = 3600
    reason: str


@app.middleware("http")
async def payload_size_limit(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/logs/ingest":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_PAYLOAD_SIZE_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": f"Payload too large. Max size: {MAX_PAYLOAD_SIZE_BYTES} bytes"},
            )
    response = await call_next(request)
    return response


@app.post("/logs/ingest")
async def ingest_logs(request: Request):
    body = await request.body()
    if len(body) > MAX_PAYLOAD_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={"error": f"Payload too large. Max: {MAX_PAYLOAD_SIZE_BYTES} bytes"},
        )

    client_id = request.client.host if request.client else "unknown"
    try:
        parsed = LogIngestRequest.model_validate_json(body)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid payload: {str(e)}"})

    if len(parsed.logs) > MAX_LOGS_PER_REQUEST:
        return JSONResponse(
            status_code=400,
            content={"error": f"Too many logs. Max: {MAX_LOGS_PER_REQUEST} per request"},
        )

    allowed, msg = rate_limiter.check_rate_limit(client_id, len(parsed.logs))
    if not allowed:
        return JSONResponse(status_code=429, content={"error": msg})

    ingested = store.ingest(parsed.logs)

    for log in parsed.logs:
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
        "rate_limits": {
            "max_payload_bytes": MAX_PAYLOAD_SIZE_BYTES,
            "max_logs_per_request": MAX_LOGS_PER_REQUEST,
            "max_requests_per_minute": RATE_LIMIT_MAX_REQUESTS,
            "max_logs_per_minute": RATE_LIMIT_MAX_LOGS,
        },
    }