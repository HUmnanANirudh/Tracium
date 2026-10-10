# Tracium Project Overview

## 1. What Tracium Is

Tracium is a log aggregation and incident response system. It connects three core tools:
- Central Log Ingestion: A FastAPI service that accepts structured JSON logs from microservices (`frontend`, `backend`, `auth`, `worker`).
- Log Observability: Promtail and Grafana Loki aggregate logs to display traffic volume, error rates, and p99 latencies in Grafana.
- Automated Investigation Engine: A LangGraph state machine using Google Gemini (`gemini-3.1-flash-lite`) that investigates open alerts, checks threat intelligence, infers attacker intent, and recommends containment steps.
- Policy Control Gate: A safety check that requires human approval before executing any high-risk action.

---

## 2. Why We Built It

Security teams face three direct operational problems:

1. Alert Noise: Rule engines produce many false alerts. Analysts spend most of their time checking harmless logs by hand.
2. Slow Response: When an attacker penetrates a system, manual triage takes 30 to 45 minutes. Attackers can move across a network in minutes.
3. Divided Tools: Developers monitor performance in Grafana, while security staff work in separate incident consoles. Context is lost between teams.

Tracium reduces the triage process from 45 minutes to 3 seconds. It filters false alerts automatically and displays performance metrics alongside security findings.

---

## 3. How the System Works

### Ingestion and Correlation
1. Services send logs to `POST /logs/ingest`.
2. The correlation engine evaluates incoming logs against sliding 5-minute windows:
   - 5 or more failed logins from one IP triggers a Brute Force incident.
   - SQL syntax errors paired with input warnings trigger a SQL Injection incident.
   - High CPU use (>99%) and connections to mining ports trigger a Cryptomining incident.
   - Routine successful logins trigger a Benign Activity incident.
3. Incidents use dynamic keys to aggregate repeated events without generating duplicate cards.

### Dual Pipeline
Every log sent to Tracium serves two purposes:
- It is written to `/app/logs/app.json`. Promtail reads this file and sends entries to Loki for Grafana display (`http://localhost:3000`).
- It is stored in memory to provide context for the investigation engine.

### The AI Investigation Cycle
When an incident opens, LangGraph runs this workflow:
1. Evidence Gathering: Python queries the log store for events matching the incident IP and user. This step uses zero LLM calls.
2. Threat Enrichment: The system checks local threat records for the IP and maps the activity to the MITRE ATT&CK framework (such as `T1110 - Brute Force`).
3. Single-Turn Analysis (Google Gemini): The model reviews the facts, history, and playbooks in one prompt:
   - Observations (What I See): Concrete facts drawn from the logs.
   - Inferences (What It Means): Attacker intent and threat progression.
   - Verdict: Classification (`True Positive`, `False Positive`, or `Inconclusive`) with a confidence rating.
   - Response Proposal: A containment action picked from local playbooks (`data/playbooks/`).
4. Policy Gate:
   - Low-risk actions (such as blocking an external IP) run immediately.
   - High-risk actions (such as isolating an internal host or disabling an account) halt the process. The dashboard shows Approve and Reject buttons. The action runs only after an analyst approves it.

---

## 4. Why We Simulate Attacks

Testing automated security responses requires realistic attack traffic without endangering live production data. The project includes five simulation scripts:

1. Benign Activity (`scripts/simulate_benign_activity.py`):
   Sends legitimate logins and normal page requests with latency values.
   Proves the AI correctly labels harmless traffic as a False Positive and takes no destructive action.

2. Brute Force (`scripts/simulate_brute_force.py`):
   Sends eight consecutive failed logins for user admin from an external IP.
   Proves threshold detection, threat intelligence enrichment, and automated low-risk IP blocking.

3. SQL Injection (`scripts/simulate_sql_injection.py`):
   Sends web application firewall alerts alongside database syntax errors.
   Proves correlation across frontend and backend services.

4. Cryptomining (`scripts/simulate_cryptomining.py`):
   Sends worker logs showing 99% CPU use by process `xmrig` and outbound traffic to port 3333.
   Proves resource abuse detection and confirms that high-risk actions (`isolate_service`) pause for human approval.

5. APT Chain (`scripts/simulate_attack_chain.py`):
   Sends a multi-stage attack: password guessing, successful login, interactive shell command (`whoami`), and data transfer.
   Proves the engine connects multiple separate log events into a single coherent timeline.

---

## 5. What We Aim to Achieve

1. Clear Incident Summaries: Replace raw log text with structured records showing observations, inferences, and required fixes.
2. Predictable AI Execution: Keep evidence gathering and policy validation in deterministic Python code. Use the language model only for contextual inference and synthesis.
3. Controlled Automation: Enforce strict policy gates so autonomous code cannot isolate production systems without human consent.
4. Shared Operational Visibility: Maintain traditional Grafana monitoring for operations while giving security analysts an automated investigation console.
