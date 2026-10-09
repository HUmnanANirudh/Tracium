import json
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from app.agents.state import InvestigationState
from app.agents.llm import get_llm
from app.agents.tools.log_tools import search_logs
from app.agents.tools.incident_tools import get_incident, search_incidents

def investigate_node(state: InvestigationState) -> dict:
    llm = get_llm(temperature=0)
    tools = [search_logs, get_incident, search_incidents]
    
    agent = create_react_agent(llm, tools)
    
    sys_msg = SystemMessage(
        content="You are an AI Security Investigator. Use tools to find logs and incidents to investigate "
                "the current incident. Only gather factual evidence. Do NOT invent logs."
    )
    
    incident_str = json.dumps(state["incident_snapshot"])
    human_msg = HumanMessage(
        content=f"Investigate the following incident:\n{incident_str}\n"
                f"Identify source IPs, related logs, and relevant anomalies. "
                f"Limit your search to gather sufficient evidence."
    )
    
    result = agent.invoke({"messages": [sys_msg, human_msg]})
    
    # We store the final messages back so we can pass context forward if needed.
    return {
        "messages": result["messages"],
        "step_count": state.get("step_count", 0) + 1
    }
