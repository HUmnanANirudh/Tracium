from app.agents.state import InvestigationState
from app.agents.tools.enrichment_tools import check_ip_reputation, get_mitre_attack_technique

def enrich_node(state: InvestigationState) -> dict:
    incident = state.get("incident_snapshot", {})
    details = incident.get("details", {})
    message = incident.get("message", "")
    
    enrichment_results = state.get("enrichment_results", {})
    
    # 1. IP Reputation
    ip = details.get("ip") or incident.get("sourceIp")
    if ip and ip not in enrichment_results:
        enrichment_results[ip] = check_ip_reputation.invoke({"ip_address": ip})
        
    # 2. MITRE mapping based on message/type
    incident_type = incident.get("type", "")
    keywords = f"{incident_type} {message}"
    mitre_info = get_mitre_attack_technique.invoke({"keyword": keywords})
    enrichment_results["mitre"] = mitre_info
    
    # Optionally, look into retrieved logs for more IPs to enrich.
    logs = state.get("retrieved_logs", [])
    for log in logs:
        log_ip = log.get("ip")
        if log_ip and log_ip not in enrichment_results:
            enrichment_results[log_ip] = check_ip_reputation.invoke({"ip_address": log_ip})
            
    return {
        "enrichment_results": enrichment_results,
        "step_count": state.get("step_count", 0) + 1
    }
