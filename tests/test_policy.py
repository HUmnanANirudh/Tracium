from app.agents.policy import validate_action
from app.agents.models import ResponseProposal

def test_policy_rejects_admin_disable():
    proposal = ResponseProposal(
        action="disable_user",
        target="admin",
        risk_tier="high",
        justification="Suspected compromise",
        rollback_plan="Re-enable admin",
        requires_approval=True
    )
    is_permitted, requires_approval, reason = validate_action(proposal, "test-run-1")
    assert not is_permitted
    assert "critical system account" in reason.lower()

def test_policy_rejects_internal_ip_block():
    proposal = ResponseProposal(
        action="block_ip",
        target="10.0.0.5",
        risk_tier="medium",
        justification="Scanner",
        rollback_plan="Unblock",
        requires_approval=False
    )
    is_permitted, requires_approval, reason = validate_action(proposal, "test-run-2")
    assert not is_permitted
    assert "internal" in reason.lower()
