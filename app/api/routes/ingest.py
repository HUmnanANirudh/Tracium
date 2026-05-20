from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
from app.models import LogIngestRequest
from app.core.config import config, limiter


async def ingest_logs(request: Request):
    body = await request.body()
    if len(body) > config.max_payload_bytes:
        return JSONResponse(
            status_code=413,
            content={"error": f"Payload too large. Max: {config.max_payload_bytes} bytes"},
        )

    client_id = request.client.host if request.client else "unknown"
    try:
        parsed = LogIngestRequest.model_validate_json(body)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid payload: {str(e)}"})

    if len(parsed.logs) > config.max_logs_per_request:
        return JSONResponse(
            status_code=400,
            content={"error": f"Too many logs. Max: {config.max_logs_per_request} per request"},
        )

    allowed, msg = limiter.check(client_id, len(parsed.logs), config)
    if not allowed:
        return JSONResponse(status_code=429, content={"error": msg})

    from app.log_store import store
    from app.incident_engine import engine

    ingested = store.ingest(parsed.logs)

    for log in parsed.logs:
        incidents, alerts = engine.analyze(log)
        for inc in incidents:
            store.add_incident(inc)
        for alert in alerts:
            store.add_alert(alert)

    return {"status": "ok", "ingested": ingested}