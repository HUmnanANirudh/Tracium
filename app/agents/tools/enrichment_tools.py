from langchain_core.tools import tool
import hashlib

@tool
def check_ip_reputation(ip_address: str) -> dict:
    """
    Check the reputation of an IP address using a mocked service.
    Returns reputation score (0-100, higher is worse), known tags, and history.
    """
    # Deterministic mock based on IP hash
    hashed = int(hashlib.md5(ip_address.encode()).hexdigest(), 16)
    score = hashed % 100
    
    tags = []
    if score > 80:
        tags.append("malicious")
        tags.append("botnet")
    elif score > 50:
        tags.append("suspicious")
        tags.append("tor_exit_node")
        
    return {
        "ip": ip_address,
        "risk_score": score,
        "tags": tags,
        "provider": "MockThreatIntel"
    }

@tool
def get_mitre_attack_technique(keyword: str) -> list[dict]:
    """
    Map a keyword (e.g., 'brute force', 'shell', 'exfiltration') to MITRE ATT&CK techniques.
    """
    mapping = {
        "brute": [{"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}],
        "login": [{"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}],
        "shell": [{"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution"}],
        "exfiltration": [{"id": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration"}],
        "data": [{"id": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration"}],
    }
    
    results = []
    keyword = keyword.lower()
    for key, val in mapping.items():
        if key in keyword:
            results.extend(val)
            
    return results if results else [{"id": "Unknown", "name": "Unmapped", "tactic": "Unknown"}]
