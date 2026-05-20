# Tracium Limitations

This document describes known limitations of the Tracium system for log aggregation and incident correlation.

## Log Storage

### Loki Not Ideal for Deep Analytics

Loki is optimized for log aggregation and label-based filtering, not deep analytics:

- **Limited query expressiveness**: Loki's LogQL is powerful but doesn't replace SQL-based analytics
- **No join operations**: Cannot correlate across multiple log streams efficiently
- **Aggregation latency**: Complex aggregations require pre-computation or external tools
- **Alternative**: For deep analytics, consider Elasticsearch or ClickHouse

### Limited Retention

- **In-memory store**: The `LogStore` class holds all logs in memory
- **No persistence**: Logs are lost on restart
- **Memory pressure**: Unlimited growth will cause OOM
- **Production need**: Use Loki's storage engine or external database for persistence

## Anomaly Detection

### No ML Anomaly Detection

The current incident correlation system uses rule-based detection only:

- **Static thresholds**: All thresholds (5 failed logins, 10 errors/min, p99 > 2s) are hardcoded
- **No learning**: System cannot adapt to baselines
- **No behavioral analysis**: No user/service baseline comparison
- **Future work**: Integrate ML models (isolation forest, LSTM, etc.) for anomaly scoring

### No Distributed Consensus

- **Single-node architecture**: All processing happens on one instance
- **No coordination**: Multiple instances would have split-brain on deduplication
- **Clock dependency**: Uses `datetime.utcnow()` which can skew across nodes
- **Production need**: Redis or etcd for distributed state; NTP for clock sync

## Architecture

### Single-Node Architecture

The FastAPI application runs as a single process:

- **No horizontal scaling**: Cannot scale behind a load balancer without state sharing
- **No hot standby**: No failover mechanism
- **Resource limits**: Single-process memory and CPU caps

### Simulated Environment

This is a demonstration/portfolio system:

- **Mock data**: `services/log_generator.py` produces synthetic logs
- **No real integrations**: No actual SSH, firewall, or cloud provider integrations
- **Toy-grade**: Suitable for learning and demonstration, not production deployment

## Security Considerations

- **No authentication**: API endpoints are open (no JWT, API keys)
- **No encryption**: Logs may contain sensitive data in plaintext
- **No audit logging**: API access is not audited
- **CORS open**: Middleware allows all origins

## Performance

- **In-memory scanning**: Log queries iterate over all logs linearly
- **No indexing**: No indices on service, level, timestamp fields
- **O(n) queries**: Query complexity scales with log volume

## Future Improvements

| Area | Improvement |
|------|-------------|
| Storage | Replace in-memory store with TimescaleDB or Elasticsearch |
| Analytics | Add Elasticsearch for Kibana-powered analytics |
| ML | Integrate Eldarica or similar for anomaly scoring |
| Scaling | Add Redis for distributed state; Kubernetes for HA |
| Security | Add API authentication, TLS, audit logging |
| Retention | Implement log rotation and archival policies |