from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.runner import runner
from app.services.audit import audit_store

router = APIRouter(prefix="/agents", tags=["agents"])

class ApprovalRequest(BaseModel):
    actor: str = "analyst"

class RejectionRequest(BaseModel):
    actor: str = "analyst"
    reason: str

@router.post("/incidents/{incident_id}/run")
async def start_investigation(incident_id: str):
    run_id = runner.start_investigation(incident_id)
    return {"run_id": run_id, "status": "started"}

@router.get("/runs/{run_id}")
async def get_run_status(run_id: str):
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.post("/runs/{run_id}/approve")
async def approve_run(run_id: str, req: ApprovalRequest):
    success = runner.approve_action(run_id, req.actor)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot approve run. It may not exist or is not pending approval.")
    return {"status": "approved"}

@router.post("/runs/{run_id}/reject")
async def reject_run(run_id: str, req: RejectionRequest):
    success = runner.reject_action(run_id, req.actor, req.reason)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot reject run. It may not exist or is not pending approval.")
    return {"status": "rejected"}

@router.get("/runs/{run_id}/events")
async def get_run_events(run_id: str):
    events = [e for e in audit_store.events if e.run_id == run_id]
    return {"events": events}
