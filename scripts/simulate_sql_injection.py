import httpx
import time
from datetime import datetime, timezone

def main():
    print("Simulating SQL injection attack...")
    logs = []
    base_time = int(time.time()) - 180 
    
    import random
    attacker_ip = f"203.0.113.{random.randint(20, 89)}"

    logs.append({
        "service": "frontend",
        "level": "warning",
        "timestamp": datetime.fromtimestamp(base_time, tz=timezone.utc).isoformat(),
        "message": "Suspicious input detected: ' OR 1=1 --",
        "ip": attacker_ip,
        "eventType": "waf_alert"
    })
    
    for i in range(5):
        logs.append({
            "service": "backend",
            "level": "error",
            "timestamp": datetime.fromtimestamp(base_time + 10 + i, tz=timezone.utc).isoformat(),
            "message": "Database syntax error near 'OR 1=1'",
            "ip": attacker_ip,
            "eventType": "db_error"
        })

    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.post("/logs/ingest", json={"logs": logs})
        if response.status_code == 200:
            print("Successfully ingested SQL injection logs.")
        else:
            print(f"Failed to ingest: {response.text}")

if __name__ == "__main__":
    main()
