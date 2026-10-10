# Tracium

**Tracium** is a cloud-native, agentic AI security operations framework and SIEM-lite. It combines automated log correlation, distributed observability (Loki + Promtail + Grafana), and an autonomous **LangGraph-powered AI Security Copilot** backed by **Google Gemini** for instant threat triage, contextual root-cause inference, and human-in-the-loop response containment.

---

## Quick Access Links

Once the containers are running, access the services:

| Service | URL | Credentials / Notes |
| :--- | :--- | :--- |
| **Tracium Security Operations Center** | [`http://localhost:8000/tracium`](http://localhost:8000/tracium) | Real-time threat queue, AI investigation & approval UI |
| **Grafana Observability Dashboard** | [`http://localhost:3000`](http://localhost:3000) | Username: `admin` \| Password: `admin` |
| **Interactive API Documentation (Swagger)** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | Complete OpenAPI specification & live test console |
| **Alternative API Docs (ReDoc)** | [`http://localhost:8000/redoc`](http://localhost:8000/redoc) | Read-only schema & contract reference |
| **Loki Log Ingestion / Query API** | [`http://localhost:3100`](http://localhost:3100) | LogQL query engine endpoint |

---

## Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │              Incoming Telemetry              │
                      └──────────────────────┬───────────────────────┘
                                             │
                                   POST /logs/ingest
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │     Tracium Ingestion     │
                               │  (FastAPI Rate Limiter)   │
                               └─────────────┬─────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      │                                             │
                      ▼                                             ▼
          ┌───────────────────────┐                     ┌───────────────────────┐
          │     Log Store &       │                     │    Incident Engine    │
          │  Promtail Log File    │                     │  (Correlation Rules)  │
          └───────────┬───────────┘                     └───────────┬───────────┘
                      │                                             │
          ┌───────────┴───────────┐                                 │ Open Incident
          ▼                       ▼                                 ▼
    ┌───────────┐           ┌───────────┐               ┌───────────────────────┐
    │ Promtail  │           │ In-Memory │               │    Agentic AI Copilot │
    └─────┬─────┘           │ Store API │               │ (LangGraph + Gemini)  │
          ▼                 └───────────┘               └───────────┬───────────┘
    ┌───────────┐                                                   │
    │   Loki    │                                                   ▼
    └─────┬─────┘                                       ┌───────────────────────┐
          │                                             │  Threat Ops Dashboard │
          ▼                                             │   (http://.../tracium)│
    ┌───────────┐                                       └───────────────────────┘
    │  Grafana  │
    └───────────┘
```

1. **Dual-Path Telemetry Pipeline**:
   - Ingested logs are stored in-memory for real-time SIEM correlation and appended to `/app/logs/app.json`.
   - Promtail scrapes the structured log file and forwards events to **Grafana Loki** for historical querying and LogQL metrics.
2. **Deterministic Correlation Engine**:
   - Real-time rules aggregate related anomalies (brute force, SQL injection, cryptomining, container restarts) using sliding 5-minute deduplication windows.
3. **Agentic AI Security Copilot (LangGraph + Google Gemini)**:
   - Evaluates incident telemetry, enriches IP reputation and MITRE ATT&CK techniques, reconstructs the timeline, infers threat intent, and proposes playbook-driven response containment actions requiring human analyst approval.

---

## Prerequisites

- **Docker** (v24.0+) & **Docker Compose** (v2.20+)
- **Python 3.11+** (if executing simulation scripts directly on host)
- **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))

---

## Step-by-Step Setup & Replication

### 1. Clone & Configure Environment

Clone the repository and create your `.env` configuration file in the project root:

```bash
git clone https://github.com/HUmnanANirudh/Tracium.git
cd Tracium

# Create .env with your Gemini API Key
cat << 'EOF_ENV' > .env
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=info
EOF_ENV
```

> **Note**: Tracium uses the fast and capable `gemini-3.1-flash-lite` model, optimized to run with unified single-turn investigation to remain safely within the free tier request limits.

### 2. Launch the Stack with Docker Compose

Build and launch all services (`api`, `loki`, `promtail`, `grafana`):

```bash
sudo -E docker compose up -d --build
```

Verify that all containers are healthy:

```bash
docker compose ps
```

Expected output:
```
NAME                IMAGE                    COMMAND                  SERVICE    STATUS
tracium-api         tracium-api              "uv run uvicorn app.…"   api        Up (healthy)
tracium-grafana     grafana/grafana:11.4.0   "/run.sh"                grafana    Up
tracium-loki        grafana/loki:3.2.0       "/usr/bin/loki -conf…"   loki       Up
tracium-promtail    grafana/promtail:3.2.0   "/usr/bin/promtail -…"   promtail   Up
```

### 3. Open the Threat Operations Dashboard

Open your browser and navigate to:
**[http://localhost:8000/tracium](http://localhost:8000/tracium)**

The interface displays:
- **Top Navigation Bar**: 1-click simulation triggers and live threat counter.
- **Left Panel (Alert Queue)**: Real-time incident feed with status tags, event counts, and severity badges.
- **Right Panel (Investigation Context)**: Deep AI analysis, observation points, attack hypothesis, playbook response proposal, and execution trace.

---

## Replicating Attack Scenarios

You can simulate attacks using any of the three methods below:

### Method A: 1-Click Buttons in the Web UI
At the top of `http://localhost:8000/tracium`, click any simulation button:
- **Benign**: Generates routine logins, page views, and API calls with latency metrics.
- **Brute Force**: Ingests rapid consecutive login failures from a single IP address (`203.0.113.100`).
- **SQLi**: Simulates SQL injection probing against sensitive endpoints.
- **Cryptomining**: Emits high CPU and abnormal worker execution patterns.
- **APT Chain**: Simulates a multi-stage attack (reconnaissance → brute force → privilege escalation → exfiltration).
- **Simulate All**: Runs the full suite with automated throttling to demo end-to-end SIEM capability.

### Method B: Running Python CLI Scripts
Execute individual attack generators directly:

```bash
# 1. Normal benign activity (verified by AI as False Positive)
python3 scripts/simulate_benign_activity.py

# 2. Brute force credential stuffing
python3 scripts/simulate_brute_force.py

# 3. SQL injection attack
python3 scripts/simulate_sql_injection.py

# 4. Cryptomining anomaly
python3 scripts/simulate_cryptomining.py

# 5. Advanced Persistent Threat (APT) multi-stage attack chain
python3 scripts/simulate_attack_chain.py

# 6. Complete end-to-end demo
python3 scripts/run_demo.py
```

### Method C: Direct REST API Triggers
Trigger attacks programmatically via curl:

```bash
curl -X POST http://localhost:8000/simulate/brute_force
curl -X POST http://localhost:8000/simulate/sql_injection
curl -X POST http://localhost:8000/simulate/benign
```

---

## What the AI Agent Does

When an incident appears in the queue, selecting it displays the complete AI reasoning cycle:

1. **What I See (Observations)**:
   - Factual summary extracted directly from raw telemetry (source IP, targeted service, failed attempt count, log IDs).
2. **What It Means (Inferences)**:
   - Synthesizes the threat hypothesis (e.g. *"Attacker is conducting automated dictionary attacks against user 'admin' using an external IP with malicious threat-intel history"*).
3. **Thinking & Verdict**:
   - Classifies the incident as **True Positive**, **False Positive**, or **Inconclusive** along with a calculated confidence percentage.
4. **Recommended Containment (Human-in-the-Loop)**:
   - Matches findings against predefined incident playbooks (`data/playbooks/`).
   - Recommends an action (e.g., `block_ip`, `isolate_service`, `disable_user`) with risk tier and rollback instructions.
   - For high-risk actions, the agent pauses in `pending_approval` state until the analyst clicks **Approve Execution** or **Reject**.
5. **Audit Trail**:
   - Live timeline of agent actions, tool calls, and state transitions (`run_started`, `verdict_generated`, `approval_granted`, `run_completed`).

---

## Exploring the Grafana Observability Dashboard

Navigate to **[http://localhost:3000](http://localhost:3000)** (Login: `admin` / `admin`).

The pre-provisioned dashboard **"Tracium - Log Dashboard"** provides:
- **Log Volume by Service**: Stacked bar chart tracking activity across `auth`, `backend`, `frontend`, and `worker`.
- **Error Heatmap**: Real-time error rate spikes across services.
- **Auth Failure Timeline**: Track credential access attempts grouped by source IP.
- **Service Latency (p99)**: Latency distribution calculated from unmarshaled log payloads (`latencyMs`).
- **Live Log Stream**: Direct streaming LogQL log viewer powered by Loki (`{job="tracium"}`).

---

## REST API Reference

Full interactive documentation is available at **[`http://localhost:8000/docs`](http://localhost:8000/docs)**.

### Key Endpoints

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **UI** | `GET` | `/tracium` | Tracium Threat Ops Frontend |
| **Ingestion** | `POST` | `/logs/ingest` | Ingest batched JSON log entries with rate limiting |
| **Logs** | `GET` | `/logs/query` | Filter logs by service, level, IP, user, or time window |
| **Incidents** | `GET` | `/incidents` | List correlated incidents |
| | `GET` | `/incidents/{id}` | Retrieve incident details and timeline |
| | `PATCH`| `/incidents/{id}/state`| Update incident state (`open`, `investigating`, `resolved`) |
| | `POST` | `/incidents/{id}/false-positive` | Mark as false positive & register auto-suppression rule |
| **AI Agent** | `POST` | `/agents/incidents/{id}/run` | Manually launch an AI investigation run |
| | `GET` | `/agents/runs` | List active and historical agent runs |
| | `GET` | `/agents/runs/{id}` | Inspect investigation state, verdict, and proposed action |
| | `POST` | `/agents/runs/{id}/approve` | Approve containment action execution |
| | `POST` | `/agents/runs/{id}/reject` | Reject containment action with reason |
| | `GET` | `/agents/runs/{id}/events` | View execution trace and audit logs |
| **Simulate** | `POST` | `/simulate/{attack_type}` | Trigger background attack simulation scripts |
| **Health** | `GET` | `/health` | Ingestion engine health and store stats |

---

## Project Structure

```
Tracium/
├── app/
│   ├── agents/                 # LangGraph Agentic AI Framework
│   │   ├── graph.py            # Graph workflow definition & state machine
│   │   ├── llm.py              # Gemini model configuration
│   │   ├── models.py           # Verdict, Evidence & Response Pydantic models
│   │   ├── runner.py           # Threaded background runner & checkpointer
│   │   ├── state.py            # InvestigationState schema
│   │   ├── nodes/              # Graph execution nodes (triage, investigate, verdict, etc.)
│   │   └── tools/              # Telemetry search & threat intel tools
│   ├── api/                    # FastAPI routes & middleware
│   │   ├── routes/             # Ingestion, incidents, runs, simulations
│   │   └── middleware.py       # Payload size limiting
│   ├── core/                   # Rate limiting & global settings
│   ├── static/                 # Threat Ops Web Dashboard
│   │   ├── index.html          # Clean, modern single-page dashboard
│   │   └── js/                 # Modular vanilla ES components
│   ├── incident_engine.py      # SIEM correlation rules engine
│   ├── incident_models.py      # Incident and security alert schemas
│   ├── log_store.py            # In-memory log store + file persistence
│   ├── models.py               # Log telemetry models
│   └── main.py                 # FastAPI application root
├── data/
│   └── playbooks/              # Response containment playbooks (Markdown)
├── dashboards/                 # Grafana provisioning & dashboard JSON
├── datasources/                # Grafana Loki datasource configuration
├── promtail/                   # Promtail scrape configuration
├── scripts/                    # Simulation scripts (benign, brute force, sqli, etc.)
├── tests/                      # Pytest test suite & policy evaluations
├── docker-compose.yaml         # Complete stack orchestration
├── Dockerfile                  # API container definition
└── pyproject.toml              # UV / Python dependency management
```

---

## Troubleshooting & FAQ

### 1. Gemini Quota Limit (`RESOURCE_EXHAUSTED 429`)
- The AI pipeline is pre-configured with **unified single-turn investigations**, using **exactly 1 Gemini request per incident** (down from 5–6 calls previously).
- To keep your rate limits safe, click simulations one at a time or use the built-in 15-second throttle in `scripts/run_demo.py`.

### 2. Grafana Dashboard Shows "No Data"
- If Grafana panels appear empty on first launch:
- Run a simulation (e.g. click **Benign** or **Simulate All**). Promtail will scrape the generated `/app/logs/app.json` file and stream it into Loki within 5 seconds.
- In Grafana, verify the time picker in the top right is set to **"Last 15 minutes"** or **"Last 1 hour"**.

### 3. Restarting or Rebuilding the Environment
If you modify backend Python code or configurations:

```bash
# Quick restart
sudo -E docker compose restart api

# Full clean rebuild
sudo -E docker compose down
sudo -E docker compose up -d --build
```
