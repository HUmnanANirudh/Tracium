import httpx
import time
from datetime import datetime, timezone

def main():
    print("Simulating benign activity...")
    logs = []
    base_time = int(time.time()) - 60
    
    import random
    user_ip = f"203.0.113.{random.randint(200, 254)}"

    # Successful logins
    for i in range(2):
        logs.append({
            "service": "auth",
            "level": "info",
            "timestamp": datetime.fromtimestamp(base_time + i*5, tz=timezone.utc).isoformat(),
            "message": f"Successful login for user alice",
            "userId": "alice",
            "ip": user_ip,
            "eventType": "login_success"
        })
    
    # Normal frontend traffic
    for i in range(10):
        logs.append({
            "service": "frontend",
            "level": "info",
            "timestamp": datetime.fromtimestamp(base_time + i*2, tz=timezone.utc).isoformat(),
            "message": f"Page view /home",
            "ip": user_ip,
            "eventType": "page_view"
        })
        
    # Normal backend traffic with latency
    for i in range(10):
        logs.append({
            "service": "backend",
            "level": "info",
            "timestamp": datetime.fromtimestamp(base_time + i*2, tz=timezone.utc).isoformat(),
            "message": f"Processed API request",
            "ip": user_ip,
            "latencyMs": 45.5 + i,
            "eventType": "api_request"
        })

    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.post("/logs/ingest", json={"logs": logs})
        if response.status_code == 200:
            print("Successfully ingested benign activity logs.")
        else:
            print(f"Failed to ingest: {response.text}")

if __name__ == "__main__":
    main()
