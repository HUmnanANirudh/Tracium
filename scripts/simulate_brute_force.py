import httpx
import time
from datetime import datetime, timezone

def main():
    print("Simulating brute force attack...")
    logs = []
    base_time = int(time.time()) - 300 # 5 minutes ago
    
    for i in range(12):
        logs.append({
            "service": "auth",
            "level": "error",
            "timestamp": datetime.fromtimestamp(base_time + i*5, tz=timezone.utc).isoformat(),
            "message": f"Failed login attempt for user admin",
            "userId": "admin",
            "ip": "203.0.113.100",
            "eventType": "login_failed"
        })
    
    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.post("/logs/ingest", json={"logs": logs})
        if response.status_code == 200:
            print("Successfully ingested brute force logs.")
        else:
            print(f"Failed to ingest: {response.text}")

if __name__ == "__main__":
    main()
