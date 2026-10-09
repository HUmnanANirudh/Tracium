from app.agents.state import InvestigationState
from app.log_store import store

def triage_node(state: InvestigationState) -> dict:
    incident_id = state.get("incident_id")
    incident = store.get_incident(incident_id)
    
    if not incident:
        return {"errors": ["Incident not found during triage."]}
    
    # In a real scenario, we might check suppressions, set scopes.
    # For now, just load the incident into context.
    # Strip timeline to prevent TPM rate limits
    slim_incident = {k: v for k, v in incident.items() if k != "timeline"}
    
    return {
        "incident_snapshot": slim_incident,
        "step_count": state.get("step_count", 0) + 1,
    }
