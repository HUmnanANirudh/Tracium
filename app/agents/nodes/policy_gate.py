from app.agents.state import InvestigationState
from app.agents.policy import validate_action

def policy_gate_node(state: InvestigationState) -> dict:
    proposal = state.get("response_proposal")
    
    if not proposal:
        return {"step_count": state.get("step_count", 0) + 1}
        
    run_id = state.get("run_id", "unknown")
    is_permitted, requires_approval, reason = validate_action(proposal, run_id)
    
    # We can store the policy result in state to decide next routing steps
    # For now, let's just append an error if not permitted.
    errors = state.get("errors", [])
    if not is_permitted:
        errors.append(reason)
        
    # We update the requires_approval flag on the proposal based on policy
    proposal.requires_approval = requires_approval
    
    return {
        "response_proposal": proposal,
        "errors": errors,
        "step_count": state.get("step_count", 0) + 1
    }
