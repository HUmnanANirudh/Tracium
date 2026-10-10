import json
from langchain_core.messages import AIMessage, ToolMessage
from app.agents.state import InvestigationState
from app.agents.tools.log_tools import search_logs

def investigate_node(state: InvestigationState) -> dict:
    incident = state.get("incident_snapshot", {})
    details = incident.get("details", {})
    ip = details.get("ip") or incident.get("sourceIp")
    user_id = details.get("userId") or incident.get("userId")
    service = incident.get("service")
    
    # Query parameters based on incident metadata
    search_args = {}
    if ip:
        search_args["ip"] = ip
    if user_id:
        search_args["userId"] = user_id
    if service and not ip:
        svc = service.replace("ServiceName.", "").lower()
        search_args["service"] = svc
    search_args["limit"] = 50
    
    # Deterministic log search without burning unnecessary LLM calls
    logs_json = search_logs.invoke(search_args)
    try:
        retrieved_logs = json.loads(logs_json)
        if not isinstance(retrieved_logs, list):
            retrieved_logs = []
    except Exception:
        retrieved_logs = []
        
    tool_call_id = "call_search_logs"
    ai_msg = AIMessage(
        content=f"Searching logs for security telemetry related to incident {incident.get('id', '')}...",
        tool_calls=[{"name": "search_logs", "args": search_args, "id": tool_call_id}]
    )
    tool_msg = ToolMessage(
        name="search_logs",
        content=logs_json,
        tool_call_id=tool_call_id
    )
    summary_msg = AIMessage(
        content=f"Log investigation complete. Retrieved {len(retrieved_logs)} log events matching criteria {search_args}."
    )
    
    return {
        "messages": [ai_msg, tool_msg, summary_msg],
        "retrieved_logs": retrieved_logs,
        "step_count": state.get("step_count", 0) + 1
    }

