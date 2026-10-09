import pytest
import os
import json
from app.log_store import store
from app.agents.graph import create_investigation_graph
from tests.eval_dataset import EVAL_DATASET
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

class JustificationScore(BaseModel):
    score: int # 1 to 5
    reasoning: str

@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
def test_agent_evals():
    results = []
    
    # LLM for judge
    judge_llm = ChatGroq(model=os.getenv("GROQ_MODEL", "llama3-8b-8192"), temperature=0)
    structured_judge = judge_llm.with_structured_output(JustificationScore)
    
    for case in EVAL_DATASET:
        # 1. Setup store
        store.incidents.clear()
        store.logs.clear()
        
        store.add_incident(case["incident"])
        store.ingest(case["logs"])
        
        graph = create_investigation_graph()
        initial_state = {
            "incident_id": case["incident"].id,
            "run_id": f"eval-{case['scenario']}",
            "messages": [],
            "errors": [],
            "step_count": 0,
            "evidence": [],
            "entities": [],
            "related_incident_ids": [],
            "retrieved_logs": [],
            "enrichment_results": {},
            "approval_status": None
        }
        
        config = {"configurable": {"thread_id": f"eval-{case['scenario']}"}}
        final_state = graph.invoke(initial_state, config=config)
        
        verdict = final_state.get("verdict")
        proposal = final_state.get("response_proposal")
        
        # 2. Check Verdict
        verdict_passed = verdict is not None and verdict.classification == case["expected_verdict"]
        
        # 3. Check Evidence Extraction
        evidence_passed = False
        if verdict and len(verdict.evidence_ids) > 0:
            evidence_passed = True
            
        # 4. LLM-as-a-judge for Justification (if proposal exists)
        judge_score = 0
        judge_reasoning = ""
        if proposal and proposal.justification:
            sys_msg = SystemMessage("You are evaluating the quality of an automated security response justification. Score it from 1 (poor) to 5 (excellent). It should clearly state the threat and the reason for the action.")
            human_msg = HumanMessage(f"Justification: {proposal.justification}\nAction: {proposal.action}\nTarget: {proposal.target}\nScore this.")
            try:
                eval_result = structured_judge.invoke([sys_msg, human_msg])
                judge_score = eval_result.score
                judge_reasoning = eval_result.reasoning
            except Exception:
                pass
                
        results.append({
            "scenario": case["scenario"],
            "expected_verdict": case["expected_verdict"],
            "actual_verdict": verdict.classification if verdict else "None",
            "verdict_passed": verdict_passed,
            "evidence_extracted": evidence_passed,
            "judge_score": judge_score,
            "judge_reasoning": judge_reasoning
        })
        
        # We assert that the verdict matches so the test fails if the LLM gets it wrong.
        # But for flaky LLMs we might want a softer failure or just the report.
        # For this requirement, we'll assert it.
        assert verdict_passed, f"Verdict mismatch in scenario {case['scenario']}"
        assert evidence_passed, f"No evidence extracted in {case['scenario']}"
        
    # Write report
    with open("eval_report.json", "w") as f:
        json.dump({"results": results}, f, indent=2)
