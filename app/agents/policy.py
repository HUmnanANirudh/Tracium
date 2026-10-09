from app.agents.models import ResponseProposal
from app.services.audit import audit_store

def validate_action(proposal: ResponseProposal, run_id: str) -> tuple[bool, bool, str]:
    """
    Validates a response proposal against deterministic policy rules.
    Returns: (is_permitted, requires_approval, reason)
    """
    is_permitted = True
    requires_approval = proposal.requires_approval
    reason = "Action meets policy criteria."
    
    # 1. Block IP Policy
    if proposal.action == "block_ip":
        # Cannot block internal IPs (mocking 10.0.x.x)
        if proposal.target.startswith("10.") or proposal.target.startswith("192.168.0."):
            is_permitted = False
            reason = "Policy violation: Cannot block internal network IPs."
        elif proposal.risk_tier in ["low", "medium"]:
            requires_approval = False
            
    # 2. Disable User Policy
    elif proposal.action == "disable_user":
        if proposal.target.lower() in ["admin", "root", "system"]:
            is_permitted = False
            reason = "Policy violation: Cannot automatically disable critical system accounts."
        else:
            requires_approval = True
            
    # 3. Isolate Service Policy
    elif proposal.action == "isolate_service":
        requires_approval = True
        
    # 4. Notify Policy
    elif proposal.action == "notify":
        requires_approval = False
        
    else:
        is_permitted = False
        reason = f"Policy violation: Unknown action {proposal.action}"
        
    # Override: High risk always requires approval if permitted
    if is_permitted and proposal.risk_tier == "high":
        requires_approval = True
        
    audit_store.record(
        run_id=run_id,
        event_type="policy_evaluation",
        details={
            "action": proposal.action,
            "target": proposal.target,
            "is_permitted": is_permitted,
            "requires_approval": requires_approval,
            "reason": reason
        }
    )
    
    return is_permitted, requires_approval, reason
