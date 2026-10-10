# Security Story: From Initial Breach to Data Exfiltration

## Scenario

An attacker executes a four-stage intrusion against the application:

1. Password Guessing: Repeated failed login attempts against the `auth` service.
2. Initial Access: One valid credential succeeds, granting account access.
3. Interactive Shell: Attacker runs terminal commands (`whoami`) on the `backend` service.
4. Data Exfiltration: Large outbound data transfers occur from the `worker` service.

---

## Log Telemetry

The attack produces this log sequence:

```
10:01:15 [auth] level=error message="Failed login attempt for user admin" ip=203.0.113.142 userId=admin eventType=login_failed
10:01:20 [auth] level=error message="Failed login attempt for user admin" ip=203.0.113.142 userId=admin eventType=login_failed
10:01:25 [auth] level=error message="Failed login attempt for user admin" ip=203.0.113.142 userId=admin eventType=login_failed
10:01:30 [auth] level=error message="Failed login attempt for user admin" ip=203.0.113.142 userId=admin eventType=login_failed
10:01:35 [auth] level=error message="Failed login attempt for user admin" ip=203.0.113.142 userId=admin eventType=login_failed
10:02:10 [auth] level=info  message="Successful login for user admin" ip=203.0.113.142 userId=admin eventType=login_success
10:02:30 [backend] level=warning message="Shell command executed: whoami" ip=203.0.113.142 userId=admin eventType=shell_execution
10:03:00 [backend] level=warning message="Large data transfer initiated" ip=203.0.113.142 userId=admin eventType=data_transfer
```

---

## Detection and Correlation Pipeline

```
[ Logs Generated ]
        |
        v
[ POST /logs/ingest ]
        |
        +-----------------------------------+
        |                                   |
        v                                   v
[ Written to /app/logs/app.json ]   [ IncidentEngine.analyze() ]
        |                                   |
        v                                   v
[ Promtail -> Loki -> Grafana ]     [ Incident Created: bf-203.0.113.142 ]
                                            |
                                            v
                                    [ LangGraph Investigation ]
                                            |
                                            v
                                    [ Policy Gate Approval ]
                                            |
                                            v
                                    [ Response Execution ]
```

---

## Step-by-Step Execution

### Step 1: Log Ingestion
Microservices send log batches to the ingestion endpoint:

```bash
POST /logs/ingest
Content-Type: application/json

{
  "logs": [
    {
      "service": "auth",
      "level": "error",
      "message": "Failed login attempt for user admin",
      "ip": "203.0.113.142",
      "userId": "admin",
      "eventType": "login_failed"
    }
  ]
}
```

### Step 2: Correlation Engine Flags Incident
The engine detects five failed logins from IP `203.0.113.142` inside the 5-minute sliding window:

- Rule Triggered: `check_brute_force`
- Action: Opens incident `bf-203.0.113.142-20261010` with severity `high`.
- Event Count: 5 events aggregated under key `brute_force:auth:203.0.113.142`.

### Step 3: Automated Investigation Starts
The backend starts a LangGraph background investigation:
- Queries the log store for all telemetry related to IP `203.0.113.142` and user `admin`.
- Checks threat intelligence: IP risk score is 93 (known botnet).
- Maps the behavior to MITRE ATT&CK technique `T1110` (Brute Force) and `T1059` (Command and Scripting Interpreter).

### Step 4: AI Verdict and Response Recommendation
Google Gemini processes the gathered evidence in a single turn and produces:

```json
{
  "verdict": {
    "classification": "true_positive",
    "confidence": 1.0,
    "confirmed_facts": [
      "Repeated failed logins recorded from IP 203.0.113.142 against user admin",
      "Successful authentication followed immediately by interactive shell command whoami",
      "Subsequent outbound data transfer from the compromised session"
    ],
    "inferred_relationships": [
      "Attacker obtained admin credentials through credential stuffing",
      "Shell execution confirms interactive remote access",
      "Subsequent file activity indicates data exfiltration"
    ],
    "reasoning": "The sequence of failed logins, successful authentication, interactive command execution, and outbound data movement demonstrates an active intrusion."
  },
  "response_proposal": {
    "action": "isolate_service",
    "target": "203.0.113.142",
    "risk_tier": "high",
    "justification": "Isolating the session and associated host prevents further data theft.",
    "rollback_plan": "Restore network routing after verifying credentials and patching access point.",
    "requires_approval": true
  }
}
```

### Step 5: Policy Gate Halts Execution
The policy gate in `app/agents/policy.py` checks the proposal:
- Action: `isolate_service`
- Risk Tier: `high`
- Policy Decision: High-risk operations cannot run autonomously.
- State: Graph execution pauses. Incident status updates to `pending_approval`.

### Step 6: Human Analyst Decision
The analyst opens the dashboard at `http://localhost:8000/tracium`:
- Reviews observations, inferences, and evidence logs.
- Clicks Approve Execution.
- The backend resumes the graph thread, calls `executor.execute("isolate_service", "203.0.113.142")`, updates the audit trail, and marks the run `completed`.

---

## State Transition Cycle

```
OPEN -> INVESTIGATING -> PENDING_APPROVAL -> COMPLETED
                              |
                              +-> REJECTED -> COMPLETED
```
