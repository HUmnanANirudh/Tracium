import httpx
import time
from datetime import datetime, timezone

def main():
    print("Simulating attack chain...")
    logs = []
    base_time = int(time.time()) - 600 # 10 mins ago
    
    # 1. Brute force
    for i in range(12):
        logs.append({
            "service": "auth",
            "level": "error",
            "timestamp": datetime.fromtimestamp(base_time + i*5, tz=timezone.utc).isoformat(),
            "message": f"Failed login attempt for user admin",
            "userId": "admin",
            "ip": "192.168.1.102",
            "eventType": "login_failed"
        })
    
    # 2. Successful login
    logs.append({
        "service": "auth",
        "level": "info",
        "timestamp": datetime.fromtimestamp(base_time + 70, tz=timezone.utc).isoformat(),
        "message": f"Successful login for user admin",
        "userId": "admin",
        "ip": "192.168.1.102",
        "eventType": "login_success"
    })

    # 3. Suspicious shell
    logs.append({
        "service": "backend",
        "level": "warning",
        "timestamp": datetime.fromtimestamp(base_time + 90, tz=timezone.utc).isoformat(),
        "message": f"Shell command executed: whoami",
        "userId": "admin",
        "ip": "192.168.1.102",
        "eventType": "shell_execution"
    })

    # 4. Exfiltration
    for i in range(5):
        logs.append({
            "service": "backend",
            "level": "warning",
            "timestamp": datetime.fromtimestamp(base_time + 120 + i*10, tz=timezone.utc).isoformat(),
            "message": f"Large data transfer initiated",
            "userId": "admin",
            "ip": "192.168.1.102",
            "eventType": "data_transfer"
        })

    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.post("/api/ingest", json={"logs": logs})
        if response.status_code == 200:
            print("Successfully ingested attack chain logs.")
        else:
            print(f"Failed to ingest: {response.text}")

if __name__ == "__main__":
    main()
