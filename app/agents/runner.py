from typing import Dict, Any
import uuid
import threading
from app.agents.graph import create_investigation_graph
from app.services.audit import audit_store
from langgraph.checkpoint.memory import MemorySaver

class AgentRunner:
    def __init__(self):
        # We need a shared checkpointer for the graph to resume
        self.checkpointer = MemorySaver()
        self.graph = create_investigation_graph(checkpointer=self.checkpointer)
        self.active_runs: Dict[str, Dict[str, Any]] = {}
        self.incident_runs: Dict[str, str] = {} # incident_id -> run_id
        self.run_threads: Dict[str, threading.Thread] = {}
        
    def start_investigation(self, incident_id: str) -> str:
        # Deduplicate
        if incident_id in self.incident_runs:
            existing_run = self.incident_runs[incident_id]
            if existing_run in self.active_runs:
                return existing_run

        run_id = f"run-{uuid.uuid4().hex[:8]}"
        self.incident_runs[incident_id] = run_id
        
        initial_state = {
            "incident_id": incident_id,
            "run_id": run_id,
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
        
        self.active_runs[run_id] = {
            "incident_id": incident_id,
            "status": "running",
            "state": initial_state
        }
        
        audit_store.record(run_id, "run_started", {"incident_id": incident_id})
        
        # Run graph in background thread
        thread = threading.Thread(target=self._run_graph, args=(run_id, initial_state))
        self.run_threads[run_id] = thread
        thread.start()
        
        return run_id
        
    def _run_graph(self, run_id: str, state_input: dict):
        config = {"configurable": {"thread_id": run_id}}
        try:
            # invoke or stream
            for event in self.graph.stream(state_input, config=config):
                # We could capture event outputs here for SSE streaming
                pass
                
            # After graph finishes (or pauses)
            state = self.graph.get_state(config)
            
            if len(state.next) > 0:
                # It means it is paused (e.g., interrupted before await_approval)
                self.active_runs[run_id]["status"] = "pending_approval"
                audit_store.record(run_id, "run_paused", {"reason": "awaiting_approval"})
            else:
                self.active_runs[run_id]["status"] = "completed"
                audit_store.record(run_id, "run_completed", {})
                
        except Exception as e:
            self.active_runs[run_id]["status"] = "failed"
            audit_store.record(run_id, "run_failed", {"error": str(e)})

    def approve_action(self, run_id: str, actor: str) -> bool:
        if run_id not in self.active_runs:
            return False
        if self.active_runs[run_id]["status"] != "pending_approval":
            return False
            
        audit_store.record(run_id, "approval_granted", {"actor": actor})
        
        config = {"configurable": {"thread_id": run_id}}
        
        # Update state to approved
        self.graph.update_state(config, {"approval_status": "approved"})
        
        self.active_runs[run_id]["status"] = "running"
        
        # Resume graph
        thread = threading.Thread(target=self._resume_graph, args=(run_id,))
        self.run_threads[run_id] = thread
        thread.start()
        return True
        
    def reject_action(self, run_id: str, actor: str, reason: str) -> bool:
        if run_id not in self.active_runs:
            return False
        if self.active_runs[run_id]["status"] != "pending_approval":
            return False
            
        audit_store.record(run_id, "approval_rejected", {"actor": actor, "reason": reason})
        
        config = {"configurable": {"thread_id": run_id}}
        
        # Update state to rejected
        self.graph.update_state(config, {"approval_status": f"rejected: {reason}"})
        
        self.active_runs[run_id]["status"] = "running"
        
        # Resume graph
        thread = threading.Thread(target=self._resume_graph, args=(run_id,))
        self.run_threads[run_id] = thread
        thread.start()
        return True
        
    def _resume_graph(self, run_id: str):
        config = {"configurable": {"thread_id": run_id}}
        try:
            # passing None resumes the graph from interrupted state
            for event in self.graph.stream(None, config=config):
                pass
                
            state = self.graph.get_state(config)
            
            if len(state.next) > 0:
                self.active_runs[run_id]["status"] = "pending_approval"
            else:
                self.active_runs[run_id]["status"] = "completed"
                audit_store.record(run_id, "run_completed", {})
                
        except Exception as e:
            self.active_runs[run_id]["status"] = "failed"
            audit_store.record(run_id, "run_failed", {"error": str(e)})
            
    def get_run(self, run_id: str) -> dict:
        if run_id not in self.active_runs:
            return None
            
        config = {"configurable": {"thread_id": run_id}}
        state = self.graph.get_state(config)
        
        # Exclude complex objects like messages for simple API return
        safe_state = {}
        if state and state.values:
            for k, v in state.values.items():
                if k == "messages": continue
                if hasattr(v, "model_dump"): safe_state[k] = v.model_dump()
                else: safe_state[k] = v
                
        return {
            "run_id": run_id,
            "incident_id": self.active_runs[run_id]["incident_id"],
            "status": self.active_runs[run_id]["status"],
            "state": safe_state
        }

runner = AgentRunner()
