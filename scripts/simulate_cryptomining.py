import httpx
import time
from datetime import datetime, timezone

def main():
    print("Simulating Cryptomining activity...")
    logs = []
    base_time = int(time.time()) - 360 
    
    for i in range(15):
        logs.append({
            "service": "worker",
            "level": "warning",
            "timestamp": datetime.fromtimestamp(base_time + i*60, tz=timezone.utc).isoformat(),
            "message": "CPU utilization exceeded 99% for process 'xmrig'",
            "ip": "10.0.0.5",
            "eventType": "high_cpu"
        })
        
    logs.append({
        "service": "worker",
        "level": "warning",
        "timestamp": datetime.fromtimestamp(base_time + 120, tz=timezone.utc).isoformat(),
        "message": "Outbound connection to known mining pool port 3333",
        "ip": "10.0.0.5",
        "eventType": "network_anomaly"
    })

    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.post("/logs/ingest", json={"logs": logs})
        if response.status_code == 200:
            print("Successfully ingested cryptomining logs.")
        else:
            print(f"Failed to ingest: {response.text}")

if __name__ == "__main__":
    main()
