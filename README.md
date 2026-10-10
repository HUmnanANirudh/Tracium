# Tracium

Tracium is a log aggregation and automated incident response system. It combines log ingestion, real-time alert correlation, Grafana observability (Loki and Promtail), and an automated security investigation engine powered by LangGraph and Google Gemini.

---

## Service Addresses

When the Docker containers run, access the services at these addresses:

| Service | Address | Notes |
| :--- | :--- | :--- |
| Tracium Web Dashboard | [http://localhost:8000/tracium](http://localhost:8000/tracium) | Live alert feed, AI findings, and response approval |
| Grafana Dashboard | [http://localhost:3000](http://localhost:3000) | Username: `admin` | Password: `admin` |
| Interactive API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI test console |
| Schema Reference (ReDoc) | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Read-only API reference |
| Loki Query API | [http://localhost:3100](http://localhost:3100) | LogQL query endpoint |

---

## Project Documentation

Detailed guides live in the `docs/` directory:

- [Project Overview](docs/project-overview.md): Technical summary explaining what the system does, why we built it, why we simulate attacks, and what it achieves.
- [Security Story Walkthrough](docs/security-story.md): An end-to-end trace of a multi-stage attack from password guessing to data theft.
- [System Scope and Limitations](docs/limitations.md): Technical trade-offs, design boundaries, and future production requirements.

---

## Architecture

```
                      +----------------------------------------------+
                      |              Incoming Telemetry              |
                      +----------------------┬-----------------------+
                                             |
                                   POST /logs/ingest
                                             |
                                             v
                               +---------------------------+
                               |     Tracium Ingestion     |
                               |  (FastAPI Rate Limiter)   |
                               +-------------┬-------------+
                                             |
                      +----------------------┴----------------------+
                      |                                             |
                      v                                             v
          +-----------------------+                     +-----------------------+
          |     Log Store &       |                     |    Incident Engine    |
          |  Promtail Log File    |                     |  (Correlation Rules)  |
          +-----------┬-----------+                     +-----------┬-----------+
                      |                                             |
          +-----------┴-----------+                                 | Open Incident
          v                       v                                 v
    +-----------+           +-----------+               +-----------------------+
    | Promtail  |           | In-Memory |               |    AI Agent Engine    |
    +-----┬-----+           | Store API |               | (LangGraph + Gemini)  |
          v                 +-----------+               +-----------┬-----------+
    +-----------+                                                   |
    |   Loki    |                                                   v
    +-----┬-----+                                       +-----------------------+
          |                                             |  Threat Ops Dashboard |
          v                                             |   (http://.../tracium)|
    +-----------+                                       +-----------------------+
    |  Grafana  |
    +-----------+
```

1. Dual Log Pipeline:
   - The API writes ingested logs to `/app/logs/app.json`.
   - Promtail tails this file and streams records to Grafana Loki for search and dashboard metrics.
   - The API also keeps logs in memory for fast correlation and incident analysis.
2. Correlation Engine:
   - Python correlation rules inspect incoming logs within a 5-minute sliding window.
   - Matching patterns generate incidents (brute force, SQL injection, cryptomining, container restarts).
3. AI Security Engine (LangGraph + Google Gemini):
   - When an incident opens, LangGraph starts an investigation.
   - It enriches the target IP, maps the behavior to the MITRE ATT&CK matrix, gathers log evidence, asks Gemini for root-cause analysis, and recommends a playbook containment action.
   - A policy gate requires human approval before executing any high-risk action.

---

## Prerequisites

- Docker (v24.0+) and Docker Compose (v2.20+)
- Python 3.11+ (if running simulation scripts from the host)
- Google Gemini API Key (from Google AI Studio)

---

## Setup and Installation

### 1. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cat << 'EOF' > .env
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=info
EOF
```

### 2. Start the Stack

Build and start the containers:

```bash
sudo -E docker compose up -d --build
```

Verify that all four containers run:

```bash
docker compose ps
```

Expected output:
```
NAME                IMAGE                    COMMAND                  SERVICE    STATUS
tracium-api         tracium-api              "uv run uvicorn app.…"   api        Up
tracium-grafana     grafana/grafana:11.4.0   "/run.sh"                grafana    Up
tracium-loki        grafana/loki:3.2.0       "/usr/bin/loki -conf…"   loki       Up
tracium-promtail    grafana/promtail:3.2.0   "/usr/bin/promtail -…"   promtail   Up
```

### 3. Open the Dashboard

Open your web browser and visit:
[http://localhost:8000/tracium](http://localhost:8000/tracium)

- Top Bar: Buttons to trigger simulations and view total incident counts.
- Left Column: Queue of active alerts.
- Main Area: Investigation context, facts, inferences, recommended actions, and approval controls.

---

## Running Attack Simulations

You can run simulations in three ways:

### Method 1: Web Interface Buttons
Click any simulation button at the top of the Tracium dashboard:
- Benign: Sends normal logins and routine page requests with latency values.
- Brute Force: Sends repeated failed password attempts against user admin.
- SQLi: Sends database syntax errors and web application firewall alerts.
- Cryptomining: Sends worker logs showing 99% CPU use and mining pool network traffic.
- APT Chain: Sends a four-stage sequence (password guessing, login, shell command, data transfer).
- Simulate All: Runs every test in sequence with a 15-second pause between each.

### Method 2: Python Command Line
Run the scripts directly from your terminal:

```bash
python3 scripts/simulate_benign_activity.py
python3 scripts/simulate_brute_force.py
python3 scripts/simulate_sql_injection.py
python3 scripts/simulate_cryptomining.py
python3 scripts/simulate_attack_chain.py
python3 scripts/run_demo.py
```

Each script picks a random IP or host address on every run so each execution produces a new alert card at the top of the queue.

### Method 3: REST API Calls
Trigger tests using curl:

```bash
curl -X POST http://localhost:8000/simulate/brute_force
curl -X POST http://localhost:8000/simulate/cryptomining
curl -X POST http://localhost:8000/simulate/benign
```

---

## How the AI Engine Works

When an incident opens, the system runs this process:

1. Facts (What I See):
   Extracts concrete data from logs (source IP, targeted service, attempt count, event IDs).
2. Inference (What It Means):
   Explains the attacker's intent and maps the activity to MITRE ATT&CK techniques.
3. Verdict:
   Classifies the incident as `True Positive`, `False Positive`, or `Inconclusive` with a confidence score.
4. Response Plan:
   Picks an action from local playbooks (`data/playbooks/`), such as `block_ip`, `isolate_service`, or `disable_user`.
5. Human Approval Gate:
   - Low-risk external actions (such as blocking an external botnet IP) run automatically.
   - High-risk actions (such as isolating an internal host or disabling an account) pause execution in `pending_approval` state.
   - The web dashboard displays Approve Execution and Reject buttons. The system takes no action until an analyst clicks a button.
6. Audit Trail:
   Records every state change and decision (`run_started`, `verdict_generated`, `approval_granted`, `action_executed`).

---

## Grafana Dashboard

Open [http://localhost:3000](http://localhost:3000) (Login: `admin` / `admin`).

The pre-built dashboard Tracium - Log Dashboard includes:
- Log Volume by Service: Bar chart tracking lines from auth, backend, frontend, and worker.
- Error Heatmap: Error frequency across services over time.
- Auth Failure Timeline: Failed authentication attempts grouped by source IP.
- Service Latency (p99): 99th percentile response times read from log fields (`latencyMs`).
- Live Log Stream: Direct streaming log viewer from Loki.

---

## API Reference Summary

Interactive API documentation runs at [http://localhost:8000/docs](http://localhost:8000/docs).

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/tracium` | Web application dashboard |
| `POST` | `/logs/ingest` | Ingest batch of JSON log records |
| `GET` | `/logs/query` | Filter logs by service, level, IP, or time |
| `GET` | `/incidents` | List detected incidents |
| `GET` | `/incidents/{id}` | Read incident details and timeline |
| `PATCH`| `/incidents/{id}/state`| Update incident state |
| `POST` | `/incidents/{id}/false-positive` | Mark false positive and suppress future alerts |
| `POST` | `/agents/incidents/{id}/run` | Start AI investigation |
| `GET` | `/agents/runs` | List investigation runs |
| `GET` | `/agents/runs/{id}` | Inspect investigation state and verdict |
| `POST` | `/agents/runs/{id}/approve` | Approve response action |
| `POST` | `/agents/runs/{id}/reject` | Reject response action |
| `GET` | `/agents/runs/{id}/events` | Read audit trail events |
| `POST` | `/simulate/{attack_type}` | Run an attack simulation |
| `GET` | `/health` | Ingestion engine health and store counts |

---

## Project Structure

```
Tracium/
├── app/
│   ├── agents/                 # LangGraph investigation engine
│   │   ├── graph.py            # State graph definition
│   │   ├── llm.py              # Gemini client setup
│   │   ├── models.py           # Pydantic models for verdicts and proposals
│   │   ├── runner.py           # Threaded background runner
│   │   ├── state.py            # Investigation state definition
│   │   ├── nodes/              # Graph execution nodes
│   │   └── tools/              # Log query and threat intel tools
│   ├── api/                    # HTTP routes and middleware
│   │   ├── routes/             # Ingestion, incidents, runs, simulation routes
│   │   └── middleware.py       # Request size limit middleware
│   ├── core/                   # Rate limiting settings
│   ├── static/                 # Web dashboard assets
│   │   ├── index.html          # Dashboard page
│   │   └── js/                 # Modular ES scripts
│   ├── incident_engine.py      # Rule correlation engine
│   ├── incident_models.py      # Incident data classes
│   ├── log_store.py            # In-memory log database
│   ├── models.py               # Log entry models
│   └── main.py                 # Application entry point
├── data/
│   └── playbooks/              # Containment playbook files
├── dashboards/                 # Grafana dashboard configurations
├── datasources/                # Grafana Loki datasource configuration
├── promtail/                   # Promtail configuration
├── scripts/                    # Attack simulation scripts
├── tests/                      # Automated test suite
├── docker-compose.yaml         # Container stack configuration
├── Dockerfile                  # API service image definition
└── pyproject.toml              # Python project configuration
```

---

## Troubleshooting

### Gemini Quota Errors (`429 RESOURCE_EXHAUSTED`)
- The investigation engine runs in a single turn, using one API request per incident.
- To stay within free-tier limits, run simulations individually or use the 15-second pause in `scripts/run_demo.py`.

### Grafana Shows No Data
- Run a simulation (such as Benign or Brute Force) to generate logs. Promtail forwards entries to Loki within five seconds.
- In Grafana, verify the time range in the top-right corner covers the last 15 minutes.

### Restarting the Services
To apply changes to code or configuration:

```bash
# Restart API service
sudo -E docker compose restart api

# Rebuild full stack
sudo -E docker compose down
sudo -E docker compose up -d --build
```
