from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import InvestigationState
from app.agents.nodes.triage import triage_node
from app.agents.nodes.investigate import investigate_node
from app.agents.nodes.enrich import enrich_node
from app.agents.nodes.correlate import correlate_node
from app.agents.nodes.verdict import verdict_node
from app.agents.nodes.plan_response import plan_response_node
from app.agents.nodes.policy_gate import policy_gate_node
from app.agents.nodes.await_approval import await_approval_node
from app.agents.nodes.execute_response import execute_response_node
from app.agents.nodes.report import report_node

def route_after_policy(state: InvestigationState) -> str:
    proposal = state.get("response_proposal")
    errors = state.get("errors", [])
    
    if errors or not proposal:
        return "report"
    
    if getattr(proposal, "requires_approval", False):
        return "await_approval"
    
    return "execute_response"

def create_investigation_graph(checkpointer=None):
    builder = StateGraph(InvestigationState)
    
    builder.add_node("triage", triage_node)
    builder.add_node("investigate", investigate_node)
    builder.add_node("enrich", enrich_node)
    builder.add_node("correlate", correlate_node)
    builder.add_node("verdict", verdict_node)
    builder.add_node("plan_response", plan_response_node)
    builder.add_node("policy_gate", policy_gate_node)
    builder.add_node("await_approval", await_approval_node)
    builder.add_node("execute_response", execute_response_node)
    builder.add_node("report", report_node)
    
    builder.set_entry_point("triage")
    builder.add_edge("triage", "investigate")
    builder.add_edge("investigate", "enrich")
    builder.add_edge("enrich", "correlate")
    builder.add_edge("correlate", "verdict")
    builder.add_edge("verdict", "plan_response")
    builder.add_edge("plan_response", "policy_gate")
    
    builder.add_conditional_edges(
        "policy_gate",
        route_after_policy,
        {
            "await_approval": "await_approval",
            "execute_response": "execute_response",
            "report": "report"
        }
    )
    
    builder.add_edge("await_approval", "execute_response")
    builder.add_edge("execute_response", "report")
    builder.add_edge("report", END)
    
    if checkpointer is None:
        checkpointer = MemorySaver()
        
    return builder.compile(checkpointer=checkpointer, interrupt_before=["await_approval"])
