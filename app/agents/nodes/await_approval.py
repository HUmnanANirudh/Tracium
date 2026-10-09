from app.agents.state import InvestigationState

def await_approval_node(state: InvestigationState) -> dict:
    # This node is just a placeholder to allow LangGraph to pause execution.
    # The actual approval state change happens when the user resumes the graph with input.
    return {"step_count": state.get("step_count", 0) + 1}
