# Tracium - Log Aggregation & Incident Correlation System

## Overview

A mini SIEM-lite system for centralized log aggregation, structured logging, incident correlation, and security anomaly detection.

## Stack

- **API**: FastAPI (Python)
- **Log Aggregation**: Loki (via Promtail log files)
- **Visualization**: Grafana
- **Orchestration**: Docker Compose

## Architecture

```
[Services: frontend, backend, auth, worker]
         ↓ (JSON structured logs to files)
      Promtail
         ↓
       Loki
         ↓
     Grafana
         ↓
  FastAPI Incident Engine
```

## Project Structure

```
app/
├── api/
│   ├── __init__.py
│   ├── middleware.py       # Payload size limiting
│   └── routes/
│       ├── __init__.py     # Route exports
│       ├── alerts.py       # Security alerts endpoint
│       ├── health.py       # Health check endpoint
│       ├── incidents.py    # Incident CRUD + investigation
│       ├── ingest.py       # Log ingestion + rate limiting
│       ├── logs.py         # Log querying
│       └── suppressions.py # Suppression rule management
├── core/
│   └── config.py          # RateLimitConfig + RateLimiter
├── incident_engine.py    # IncidentEngine (correlation rules)
├── incident_models.py    # Incident, SecurityAlert, SuppressionRule, TimelineEntry
├── log_store.py          # LogStore (in-memory storage)
├── models.py             # LogEntry, LogIngestRequest, LogQueryParams
└── main.py               # Route wiring only
```

## Services

1. **frontend** - Web frontend logs
2. **backend** - API backend logs
3. **auth** - Authentication service logs
4. **worker** - Background worker logs

## Log Format

```json
{
  "service": "auth",
  "level": "error",
  "timestamp": "2026-05-20T10:30:00Z",
  "message": "JWT validation failed",
  "userId": "123",
  "ip": "192.168.1.100",
  "traceId": "abc123",
  "metadata": {}
}
```

## Incident States

- `OPEN` - Newly created, unacknowledged
- `INVESTIGATING` - Under active investigation
- `MITIGATED` - Mitigating actions applied
- `RESOLVED` - Issue resolved
- `FALSE_POSITIVE` - Marked as false positive

## Investigation Features

Each incident supports a complete investigation workflow:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/incidents/{id}` | Initial incident details |
| GET | `/incidents/{id}/timeline` | Ordered sequence of correlated events |
| GET | `/incidents/{id}/related-logs` | All logs tied to incident (IP, userId, traceId) |
| GET | `/incidents/{id}/root-cause` | Root cause analysis + recommended actions |

### Timeline

Returns ordered sequence of events that triggered/contributed to the incident.

### Related Logs

Returns logs correlated by:
- Same dedup key (IP for brute_force, userId for auth_anomaly)
- Same service
- Same traceId (if available)

### Root Cause Analysis

Returns structured analysis including:
- `initial_event`: First event in the chain
- `contributing_factors`: What enabled the incident
- `impact_assessment`: Risk levels for account/lateral/data impact
- `recommended_actions`: Concrete steps to resolve and prevent

## Incident Deduplication

Incidents are deduplicated within a 5-minute window using type-specific keys:

| Incident Type | Deduplication Key |
|--------------|-------------------|
| brute_force | `brute_force:auth:{ip}` |
| error_spike | `error_spike:{service}` |
| latency_spike | `latency_spike:{service}` |
| auth_anomaly | `auth_anomaly:auth:{userId}` |
| container_restart | `container_restart:{service}` |

Aggregated incidents track `event_count` to count correlated events.

## False Positive Handling

When an incident is marked as false positive:

1. Incident state set to `FALSE_POSITIVE`
2. `false_positive_reason` stored on incident
3. Dedup key added to suppression list (default 1 hour)
4. Future alerts with same dedup key are suppressed for the suppression window
5. Confidence score for that dedup key is degraded (70% → 40% → 10% per subsequent FP)

### Confidence Score

Calculated per incident based on event severity and FP history:

| Incident Type | High Confidence Trigger | Score Impact |
|--------------|------------------------|--------------|
| brute_force | 10+ attempts | -20% per FP |
| error_spike | 20+ errors | -30% per FP |
| latency_spike | p99 > 5s | -30% per FP |

Score range: 0.0 - 1.0 (1.0 = highest confidence)

## Timeline Reconstruction

Each incident includes a `timeline` array showing correlated log events leading up to and including the incident trigger:

```json
{
  "timeline": [
    {"sequence": 1, "timestamp": "10:01:00", "service": "auth", "level": "error", "message": "Login failed"},
    {"sequence": 2, "timestamp": "10:02:00", "service": "auth", "level": "error", "message": "Login failed"},
    {"sequence": 3, "timestamp": "10:03:00", "service": "backend", "level": "warning", "message": "Privilege escalation"},
    {"sequence": 4, "timestamp": "10:04:00", "service": "worker", "level": "error", "message": "Crypto miner detected"}
  ]
}
```

Timeline captures all events within a 5-minute window before incident creation.

## Rate Limiting

The ingest endpoint is protected against abuse:

| Limit | Value |
|-------|-------|
| Max payload size | 1MB |
| Max logs per request | 1000 |
| Max requests per minute | 60 |
| Max logs per minute | 5000 |

Returns `413` for oversized payloads, `429` for rate limit exceeded.

## Incident Rules

| Rule | Description | Severity |
|------|-------------|----------|
| brute_force | 5+ failed logins in 5 min from same IP | HIGH |
| auth_anomaly | Off-hours auth failure | MEDIUM |
| error_spike | 10+ errors in 1 min | HIGH |
| latency_spike | p99 latency > 2s | MEDIUM |
| container_restart | Service restart detected | LOW |

## Security Detection

- Brute force: same IP, 5+ failures in 5 min window
- Suspicious IPs: known malicious patterns, geo-anomaly
- Auth anomalies: unusual failure ratios, off-hours activity

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/logs/ingest` | Ingest JSON logs |
| GET | `/logs/query` | Query logs with filters |
| GET | `/logs/services` | List services |
| GET | `/incidents` | List incidents (filter by state) |
| GET | `/incidents/{id}` | Get incident details |
| PATCH | `/incidents/{id}/state` | Update incident state |
| POST | `/incidents/{id}/false-positive` | Mark as false positive |
| GET | `/incidents/{id}/timeline` | Get incident timeline |
| GET | `/incidents/{id}/related-logs` | Get related logs |
| GET | `/incidents/{id}/root-cause` | Get root cause analysis |
| POST | `/suppressions` | Create suppression rule |
| GET | `/suppressions` | List active suppressions |
| GET | `/alerts/security` | Security alerts feed |
| GET | `/health` | Health check |

## Dashboard Features

- Service drilldown filtering
- Error heatmaps
- Timeline analysis
- Incident timeline
- Security alert feed

## Documentation

- [`docs/security-story.md`](docs/security-story.md) - Complete attack scenario with investigation workflow
- [`docs/limitations.md`](docs/limitations.md) - Known limitations and future improvements