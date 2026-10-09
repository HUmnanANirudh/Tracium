from langgraph.graph import StateGraph, END
from app.agents.state import InvestigationState
from app.agents.nodes.triage import triage_node
from app.agents.nodes.investigate import investigate_node
from app.agents.nodes.enrich import enrich_node
from app.agents.nodes.correlate import correlate_node
from app.agents.nodes.verdict import verdict_node

def create_investigation_graph():
    builder = StateGraph(InvestigationState)
    
    builder.add_node("triage", triage_node)
    builder.add_node("investigate", investigate_node)
    builder.add_node("enrich", enrich_node)
    builder.add_node("correlate", correlate_node)
    builder.add_node("verdict", verdict_node)
    
    builder.set_entry_point("triage")
    builder.add_edge("triage", "investigate")
    builder.add_edge("investigate", "enrich")
    builder.add_edge("enrich", "correlate")
    builder.add_edge("correlate", "verdict")
    builder.add_edge("verdict", END)
    
    return builder.compile()
