import json
from typing import Optional
from langchain_core.tools import tool
from app.log_store import store

@tool
def get_incident(incident_id: str) -> str:
    """
    Get detailed information about a specific incident.
    Args:
        incident_id: The unique ID of the incident
    Returns:
        The incident as JSON, or {"error": ...} if not found.
    """
    incident = store.get_incident(incident_id)
    if not incident:
        return json.dumps({"error": "incident not found"})
        
    # Strip timeline to prevent TPM rate limits
    slim_incident = {k: v for k, v in incident.items() if k != "timeline"}
    return json.dumps(slim_incident)

@tool
def search_incidents(service: Optional[str] = None, state: Optional[str] = None) -> str:
    """
    Search for recent incidents.
    Args:
        service: The service the incident occurred in
        state: The current state of the incident
    Returns:
        A JSON list of matching incidents (timelines omitted; use get_incident for detail).
    """
    incidents = store.get_incidents(service=service, state=state, limit=20)
    # ponytail: timelines dropped to bound tokens; get_incident returns the full record
    return json.dumps([{k: v for k, v in i.items() if k != "timeline"} for i in incidents])
