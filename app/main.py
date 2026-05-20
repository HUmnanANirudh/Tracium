from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import (
    ingest_logs,
    query_logs,
    get_services,
    get_incidents,
    get_incident,
    update_incident_state,
    mark_false_positive,
    create_suppression,
    get_suppressions,
    get_security_alerts,
    health,
)
from app.api.middleware import payload_size_middleware

app = FastAPI(title="Tracium", description="Log Aggregation & Incident Correlation System")


app.add_middleware(BaseHTTPMiddleware, dispatch=payload_size_middleware)


app.add_api_route("/logs/ingest", ingest_logs, methods=["POST"])
app.add_api_route("/logs/query", query_logs, methods=["GET"])
app.add_api_route("/logs/services", get_services, methods=["GET"])

app.add_api_route("/incidents", get_incidents, methods=["GET"])
app.add_api_route("/incidents/{incident_id}", get_incident, methods=["GET"])
app.add_api_route("/incidents/{incident_id}/state", update_incident_state, methods=["PATCH"])
app.add_api_route("/incidents/{incident_id}/false-positive", mark_false_positive, methods=["POST"])

app.add_api_route("/suppressions", create_suppression, methods=["POST"])
app.add_api_route("/suppressions", get_suppressions, methods=["GET"])

app.add_api_route("/alerts/security", get_security_alerts, methods=["GET"])
app.add_api_route("/health", health, methods=["GET"])