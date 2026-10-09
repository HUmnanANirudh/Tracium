from langchain_core.messages import SystemMessage
from app.agents.state import InvestigationState
from app.log_store import store

def triage_node(state: InvestigationState) -> dict:
    incident_id = state.get("incident_id")
    incident = store.get_incident(incident_id)
    
    if not incident:
        return {"errors": ["Incident not found during triage."]}
    
    # In a real scenario, we might check suppressions, set scopes.
    # For now, just load the incident into context.
    return {
        "incident_snapshot": incident,
        "step_count": state.get("step_count", 0) + 1,
    }
