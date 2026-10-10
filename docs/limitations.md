# System Scope and Limitations

This document lists the technical trade-offs, scope constraints, and production requirements for the Tracium project.

---

## 1. Log Storage and Querying

### In-Memory Storage
- Current State: The `LogStore` class stores logs in Python memory for fast lookups.
- Impact: Restarting the container clears all stored logs.
- Production Requirement: Replace the in-memory array with an indexed datastore such as PostgreSQL, TimescaleDB, or ClickHouse.

### Loki Query Constraints
- Current State: Loki indexes logs using service labels, while Promtail tails `/app/logs/app.json`.
- Impact: Complex analytical joins across disparate streams require post-processing.
- Production Requirement: For long-term analytical aggregations across months of data, route logs to an analytical store alongside Loki.

---

## 2. Threat Detection

### Rule-Based Correlation
- Current State: Detection rules use static thresholds (5 failed logins in 5 minutes, 10 errors in 1 minute, latency above 2 seconds).
- Impact: The system cannot establish dynamic baselines for user behavior.
- Production Requirement: Combine deterministic rules with statistical or machine-learning models to flag baseline shifts.

### Single-Instance Processing
- Current State: All correlation rules run inside a single FastAPI process.
- Impact: Scaling to multiple nodes without shared storage would cause split-brain deduplication.
- Production Requirement: Use Redis or Apache Kafka to coordinate deduplication keys and event streams across multiple worker instances.

---

## 3. Autonomous Execution

### Simulated Containment Actions
- Current State: The `SimulatedResponseExecutor` records containment actions in the audit store without modifying real firewalls or cloud security groups.
- Impact: The system safely demonstrates containment logic during tests, but does not alter infrastructure.
- Production Requirement: Connect the executor to cloud APIs (such as AWS Security Groups, Cloudflare WAF, or Kubernetes Network Policies) using authenticated credentials.

### API Security
- Current State: API routes operate without authentication headers in the local development setup.
- Impact: Suitable for demonstration and evaluation, but unsafe for public networks.
- Production Requirement: Require TLS encryption, mutual authentication, and JSON Web Tokens for all ingestion and management endpoints.

---

## 4. Language Model Integration

### Quota and Rate Limits
- Current State: Free-tier Gemini accounts enforce request limits (5 requests per minute, 20 requests per day on preview models).
- Design Choice: Tracium uses a unified single-turn investigation schema on `gemini-3.1-flash-lite`. Each incident uses exactly one API call.
- Production Requirement: Use production-tier Gemini API credentials with enterprise quota allocations for high-throughput environments.
