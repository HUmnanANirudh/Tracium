from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import (
    ingest_logs,
    query_logs,
    get_services,
    get_incidents,
    get_incident,
    update_incident_state,
    mark_false_positive,
    get_incident_timeline,
    get_incident_related_logs,
    get_incident_root_cause,
    create_suppression,
    get_suppressions,
    get_security_alerts,
    health,
)
from app.api.middleware import payload_size_middleware

app = FastAPI(
    title="Tracium",
    description="Mini SIEM-lite — Log Aggregation & Incident Correlation System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(BaseHTTPMiddleware, dispatch=payload_size_middleware)


app.add_api_route("/logs/ingest", ingest_logs, methods=["POST"])
app.add_api_route("/logs/query", query_logs, methods=["GET"])
app.add_api_route("/logs/services", get_services, methods=["GET"])

app.add_api_route("/incidents", get_incidents, methods=["GET"])
app.add_api_route("/incidents/{incident_id}", get_incident, methods=["GET"])
app.add_api_route("/incidents/{incident_id}/state", update_incident_state, methods=["PATCH"])
app.add_api_route("/incidents/{incident_id}/false-positive", mark_false_positive, methods=["POST"])
app.add_api_route("/incidents/{incident_id}/timeline", get_incident_timeline, methods=["GET"])
app.add_api_route("/incidents/{incident_id}/related-logs", get_incident_related_logs, methods=["GET"])
app.add_api_route("/incidents/{incident_id}/root-cause", get_incident_root_cause, methods=["GET"])

app.add_api_route("/suppressions", create_suppression, methods=["POST"])
app.add_api_route("/suppressions", get_suppressions, methods=["GET"])

app.add_api_route("/alerts/security", get_security_alerts, methods=["GET"])
app.add_api_route("/health", health, methods=["GET"])

from app.api.routes.agents import router as agents_router
app.include_router(agents_router)


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/tracium", include_in_schema=False)
async def serve_ui():
    with open("app/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        title="Tracium - Swagger UI",
        swagger_favicon_url=None,
    )