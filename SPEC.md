# Tracium - Log Aggregation & Incident Correlation System

## Overview

A mini SIEM-lite system for centralized log aggregation, structured logging, incident correlation, and security anomaly detection.

## Stack

- **API**: FastAPI (Python)
- **Log Aggregation**: Loki (via Promtail log files)
- **Visualization**: Grafana
- **Container Orchestration**: Docker Compose

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

## Services

1. **frontend** - Web frontend logs
2. **backend** - API backend logs
3. **auth** - Authentication service logs
4. **worker** - Background worker logs

## Log Format

```json
{
  "service": "auth-service",
  "level": "error",
  "timestamp": "2026-05-20T10:30:00Z",
  "userId": "123",
  "ip": "192.168.1.100",
  "message": "JWT validation failed",
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

## Incident Deduplication

Incidents are deduplicated within a 5-minute window using type-specific keys:

| Incident Type | Deduplication Key |
|--------------|-------------------|
| brute_force | `{type}:auth:{ip}` |
| error_spike | `{type}:{service}` |
| latency_spike | `{type}:{service}` |
| auth_anomaly | `{type}:auth:{userId}` |
| container_restart | `{type}:{service}` |

Aggregated incidents track `event_count` to count correlated events.

## Incident Rules

| Rule | Description | Severity |
|------|-------------|----------|
| brute_force | 5+ failed logins in 5 min from same IP | HIGH |
| auth_anomaly | Unusual auth failure pattern | MEDIUM |
| error_spike | 10+ errors in 1 min | HIGH |
| latency_spike | p99 latency > 2s | MEDIUM |
| container_restart | Service restart detected | LOW |

## Security Detection

- Brute force: same IP, 5+ failures in 5 min window
- Suspicious IPs: known malicious patterns, geo-anomaly
- Auth anomalies: unusual failure ratios, off-hours activity

## API Endpoints

- `POST /logs/ingest` - Ingest logs from services
- `GET /logs/query` - Query logs with filters
- `GET /logs/services` - List services
- `GET /incidents` - List active incidents
- `GET /incidents/{id}` - Incident details
- `GET /alerts/security` - Security alerts
- `GET /health` - Health check

## Dashboard Features

- Service drilldown filtering
- Error heatmaps
- Timeline analysis
- Incident timeline
- Security alert feed