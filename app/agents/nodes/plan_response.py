import os
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import InvestigationState
from app.agents.llm import get_llm
from app.agents.models import ResponseProposal

def plan_response_node(state: InvestigationState) -> dict:
    # Read playbooks
    playbooks = ""
    playbooks_dir = os.getenv("PLAYBOOKS_DIR", "data/playbooks")
    if os.path.exists(playbooks_dir):
        for filename in os.listdir(playbooks_dir):
            if filename.endswith(".md"):
                with open(os.path.join(playbooks_dir, filename), "r") as f:
                    playbooks += f"\n--- {filename} ---\n{f.read()}\n"

    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(ResponseProposal)
    
    verdict = state.get("verdict")
    if verdict and verdict.classification == "false_positive":
        # Do not propose response for false positives
        return {"response_proposal": None, "step_count": state.get("step_count", 0) + 1}
    
    sys_msg = SystemMessage(
        content="You are a security responder. Based on the incident verdict and the provided playbooks, "
                "propose a containment response action. Pick exactly ONE action from the playbook that best fits. "
                "Output must follow the ResponseProposal schema. "
                "Do NOT invent actions not listed in the playbook."
    )
    
    human_msg = HumanMessage(
        content=f"Incident Snapshot:\n{state.get('incident_snapshot')}\n\n"
                f"Verdict:\n{verdict}\n\n"
                f"Playbooks:\n{playbooks}\n\n"
                f"Recommend the best response action."
    )
    
    try:
        proposal = structured_llm.invoke([sys_msg, human_msg])
        return {
            "response_proposal": proposal,
            "step_count": state.get("step_count", 0) + 1
        }
    except Exception as e:
        return {
            "errors": [f"Response planning failed: {str(e)}"],
            "step_count": state.get("step_count", 0) + 1
        }
