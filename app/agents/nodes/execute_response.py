from app.agents.state import InvestigationState
from app.agents.tools.response_tools import executor
from app.services.audit import audit_store

def execute_response_node(state: InvestigationState) -> dict:
    proposal = state.get("response_proposal")
    errors = state.get("errors", [])
    
    # If there are errors (e.g., policy rejected it), we don't execute
    if not proposal or errors:
        return {"step_count": state.get("step_count", 0) + 1}
        
    run_id = state.get("run_id", "unknown")
    
    # Check approval status
    if proposal.requires_approval:
        approval_status = state.get("approval_status")
        if approval_status != "approved":
            # Record rejection or expiration
            audit_store.record(
                run_id=run_id,
                event_type="action_rejected",
                details={"action": proposal.action, "target": proposal.target, "reason": approval_status or "unapproved"}
            )
            return {"step_count": state.get("step_count", 0) + 1, "errors": errors + [f"Action not approved: {approval_status}"]}
            
    result = executor.execute(proposal.action, proposal.target, run_id)
    
    # Normally we'd store execution result in state too
    
    return {
        "step_count": state.get("step_count", 0) + 1
    }
