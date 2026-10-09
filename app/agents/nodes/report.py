from app.agents.state import InvestigationState
from app.services.audit import audit_store

def report_node(state: InvestigationState) -> dict:
    run_id = state.get("run_id", "unknown")
    
    # Compile a final report
    report = {
        "incident_id": state.get("incident_id"),
        "verdict": state.get("verdict").model_dump() if state.get("verdict") else None,
        "response_proposal": state.get("response_proposal").model_dump() if state.get("response_proposal") else None,
        "errors": state.get("errors", []),
        "step_count": state.get("step_count", 0)
    }
    
    audit_store.record(
        run_id=run_id,
        event_type="investigation_report",
        details=report
    )
    
    return {
        "step_count": state.get("step_count", 0) + 1
    }
