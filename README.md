# Tracium

Mini SIEM-lite — centralized log aggregation and incident correlation system.

## Stack

- **API**: FastAPI (Python)
- **Log Aggregation**: Loki + Promtail
- **Visualization**: Grafana
- **Orchestration**: Docker Compose

## Services

| Service | Description |
|---------|-------------|
| frontend | Web frontend logs |
| backend | API backend logs |
| auth | Authentication service logs |
| worker | Background worker logs |

## Quick Start

```bash
# Install dependencies
uv sync

# Run the API
uv run uvicorn app.main:app --reload

# Generate sample logs
python services/log_generator.py 500

# Run with Docker Compose (Loki + Grafana + API)
docker compose up
```

## Incident States

| State | Description |
|-------|-------------|
| open | Newly created |
| investigating | Under investigation |
| mitigated | Mitigated |
| resolved | Resolved |
| false_positive | False positive |

## Incident Deduplication

Incidents within a 5-minute window are aggregated using type-specific dedup keys. 100 failed logins = 1 incident with `event_count: 100`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/logs/ingest` | Ingest JSON logs |
| GET | `/logs/query` | Query logs with filters |
| GET | `/logs/services` | List available services |
| GET | `/incidents` | List incidents |
| GET | `/incidents/{id}` | Get incident details |
| POST | `/incidents/{id}/resolve` | Resolve an incident |
| GET | `/alerts/security` | Security alerts feed |
| GET | `/health` | Health check |

## Log Format

```json
{
  "service": "auth",
  "level": "error",
  "timestamp": "2026-05-20T10:30:00Z",
  "message": "JWT validation failed",
  "userId": "123",
  "ip": "192.168.1.100",
  "traceId": "abc123"
}
```

## Incident Rules

| Rule | Trigger | Severity |
|------|---------|----------|
| brute_force | 5+ failed logins in 5min from same IP | HIGH |
| auth_anomaly | Off-hours auth failure | MEDIUM |
| error_spike | 10+ errors in 1min | HIGH |
| latency_spike | p99 latency > 2s | MEDIUM |
| container_restart | Service restart within 5min | LOW |

## Grafana Dashboard

Access Grafana at `http://localhost:3000` (admin/admin) for:

- Log volume by service
- Error heatmaps
- Auth failure timeline
- Latency (p99) charts
- Live log stream

## Ports

| Service | Port |
|---------|------|
| API | 8000 |
| Loki | 3100 |
| Grafana | 3000 |
| Promtail | 9080 |