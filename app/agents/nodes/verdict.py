import os
import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import InvestigationState
from app.agents.llm import get_llm
from app.agents.models import InvestigationOutcome

def verdict_node(state: InvestigationState) -> dict:
    # Read playbooks so verdict & response containment can be planned in a single unified turn
    playbooks = ""
    playbooks_dir = os.getenv("PLAYBOOKS_DIR", "data/playbooks")
    if os.path.exists(playbooks_dir):
        for filename in os.listdir(playbooks_dir):
            if filename.endswith(".md"):
                with open(os.path.join(playbooks_dir, filename), "r") as f:
                    playbooks += f"\n--- {filename} ---\n{f.read()}\n"

    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(InvestigationOutcome)
    
    # Build context from previous messages
    investigation_summary = "\n".join([m.content for m in state["messages"][-5:] if isinstance(m.content, str)])
    
    sys_msg = SystemMessage(
        content="You are a senior security analyst and automated incident responder.\n"
                "Based on the investigation telemetry, issue a Verdict and (if applicable) a Response Proposal.\n"
                "1. Distinguish between true_positive, false_positive, and inconclusive.\n"
                "2. CRITICAL: You must explicitly document what you see (Observation) and what it means (Inference).\n"
                "   - In `confirmed_facts`, describe exactly what you see in the logs (IPs, users, counts, event sequences).\n"
                "   - In `inferred_relationships`, explain what these facts mean (intent, threat vector, attack hypothesis).\n"
                "   - In `reasoning`, synthesize facts and inferences into a concise executive summary.\n"
                "3. If and only if the classification is `true_positive`, propose a containment action in `response_proposal` "
                "from the provided playbooks (block_ip, disable_user, isolate_service, notify). "
                "In `justification`, explain why based on inferences. "
                "If false_positive or inconclusive, set `response_proposal` to null."
    )
    
    human_msg = HumanMessage(
        content=f"Investigation Summary:\n{investigation_summary}\n\n"
                f"Incident Snapshot:\n{state.get('incident_snapshot')}\n\n"
                f"Enrichment Context:\n{state.get('enrichment_results')}\n\n"
                f"Related Incidents:\n{state.get('related_incident_ids')}\n\n"
                f"Playbooks for Response Containment:\n{playbooks}\n\n"
                f"Analyze the evidence and provide the InvestigationOutcome (Verdict and ResponseProposal)."
    )
    
    try:
        outcome = structured_llm.invoke([sys_msg, human_msg])
        verdict = outcome.verdict
        proposal = outcome.response_proposal
        
        # Extract retrieved logs from tool messages
        retrieved_logs = []
        for msg in state.get("messages", []):
            if hasattr(msg, "name") and msg.name == "search_logs" and hasattr(msg, "content"):
                try:
                    logs = json.loads(msg.content)
                    if isinstance(logs, list):
                        retrieved_logs.extend(logs)
                except Exception:
                    pass

        valid_log_ids = {log.get("id") for log in retrieved_logs if "id" in log}
        valid_incident_ids = set(state.get("related_incident_ids", []))
        if state.get("incident_id"):
            valid_incident_ids.add(state.get("incident_id"))
            
        validated_evidence_ids = []
        for eid in verdict.evidence_ids:
            if eid in valid_log_ids or eid in valid_incident_ids:
                validated_evidence_ids.append(eid)
            
        verdict.evidence_ids = validated_evidence_ids

        return {
            "verdict": verdict,
            "response_proposal": proposal,
            "step_count": state.get("step_count", 0) + 1
        }
    except Exception as e:
        return {
            "errors": [f"Verdict generation failed: {str(e)}"],
            "step_count": state.get("step_count", 0) + 1
        }

