import httpx
import time
from datetime import datetime, timezone

def main():
    print("Simulating benign activity...")
    logs = []
    base_time = int(time.time()) - 60
    
    # Just a few failed logins, not enough to trigger brute force
    for i in range(3):
        logs.append({
            "service": "auth",
            "level": "error",
            "timestamp": datetime.fromtimestamp(base_time + i*5, tz=timezone.utc).isoformat(),
            "message": f"Failed login attempt for user john",
            "userId": "john",
            "ip": "192.168.1.101",
            "eventType": "login_failed"
        })
    
    # Normal frontend traffic
    for i in range(10):
        logs.append({
            "service": "frontend",
            "level": "info",
            "timestamp": datetime.fromtimestamp(base_time + i*2, tz=timezone.utc).isoformat(),
            "message": f"Page view /home",
            "ip": "203.0.113.5",
            "eventType": "page_view"
        })

    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.post("/logs/ingest", json={"logs": logs})
        if response.status_code == 200:
            print("Successfully ingested benign activity logs.")
        else:
            print(f"Failed to ingest: {response.text}")

if __name__ == "__main__":
    main()
