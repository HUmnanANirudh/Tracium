from typing import Optional
from langchain_core.tools import tool
from app.log_store import store

@tool
def get_incident(incident_id: str) -> Optional[dict]:
    """
    Get detailed information about a specific incident.
    Args:
        incident_id: The unique ID of the incident
    Returns:
        The incident dictionary or None if not found.
    """
    return store.get_incident(incident_id)

@tool
def search_incidents(service: Optional[str] = None, state: Optional[str] = None) -> list[dict]:
    """
    Search for recent incidents.
    Args:
        service: The service the incident occurred in
        state: The current state of the incident
    Returns:
        A list of matching incidents.
    """
    return store.get_incidents(service=service, state=state)
