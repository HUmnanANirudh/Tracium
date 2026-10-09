from app.agents.state import InvestigationState
from app.log_store import store

def correlate_node(state: InvestigationState) -> dict:
    incident = state.get("incident_snapshot", {})
    details = incident.get("details", {})
    
    current_id = incident.get("id")
    target_ip = details.get("ip") or incident.get("sourceIp")
    target_user = details.get("userId") or incident.get("userId")
    
    related_ids = set(state.get("related_incident_ids", []))
    
    if target_ip or target_user:
        # Search for other incidents with same IP or user
        all_incidents = store.get_incidents()
        for inc in all_incidents:
            if inc["id"] == current_id:
                continue
                
            inc_ip = inc.get("details", {}).get("ip") or inc.get("sourceIp")
            inc_user = inc.get("details", {}).get("userId") or inc.get("userId")
            
            if (target_ip and target_ip == inc_ip) or (target_user and target_user == inc_user):
                related_ids.add(inc["id"])
                
    return {
        "related_incident_ids": list(related_ids),
        "step_count": state.get("step_count", 0) + 1
    }
