from typing import Annotated, TypedDict
from operator import add
from app.agents.models import Evidence, Verdict, ResponseProposal

class InvestigationState(TypedDict):
    incident_id: str
    run_id: str
    
    # Context
    incident_snapshot: dict
    retrieved_logs: list[dict]
    evidence: list[Evidence]
    
    # Enrichment
    entities: list[str]
    related_incident_ids: list[str]
    enrichment_results: dict
    
    # Verdict & Response
    verdict: Verdict | None
    response_proposal: ResponseProposal | None
    
    # Limits & Execution
    messages: Annotated[list, add]
    errors: list[str]
    step_count: int
