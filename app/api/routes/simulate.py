from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
import subprocess
import os

router = APIRouter(prefix="/simulate", tags=["simulate"])

def run_script(script_name: str):
    subprocess.Popen(["python3", f"scripts/{script_name}"])

@router.post("/{attack_type}")
async def simulate_attack(attack_type: str, background_tasks: BackgroundTasks):
    valid_attacks = {
        "brute_force": "simulate_brute_force.py",
        "sql_injection": "simulate_sql_injection.py",
        "cryptomining": "simulate_cryptomining.py",
        "attack_chain": "simulate_attack_chain.py",
        "benign": "simulate_benign_activity.py",
        "all": "run_demo.py"
    }
    
    if attack_type not in valid_attacks:
        return JSONResponse(status_code=400, content={"error": "Invalid attack type"})
        
    script = valid_attacks[attack_type]
    background_tasks.add_task(run_script, script)
    return {"status": "ok", "message": f"Simulating {attack_type}..."}
