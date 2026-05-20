import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path


SERVICES = ["frontend", "backend", "auth", "worker"]

LOG_MESSAGES = {
    "frontend": {
        "info": [
            "Page loaded successfully",
            "User navigated to dashboard",
            "Static assets served",
            "React hydration completed",
            "WebSocket connected",
        ],
        "error": [
            "Failed to fetch user data",
            "API timeout on request",
            "Component render failed",
            "State update error",
        ],
    },
    "backend": {
        "info": [
            "Request processed successfully",
            "Database query executed",
            "Cache hit for user session",
            "Health check passed",
            "Request completed in {latency}ms",
        ],
        "error": [
            "Database connection pool exhausted",
            "Request timeout after 30s",
            "Internal server error",
            "Serialization error",
        ],
        "warning": [
            "Slow query detected ({latency}ms)",
            "Cache miss rate above threshold",
            "Memory usage at 80%",
        ],
    },
    "auth": {
        "info": [
            "User authenticated successfully",
            "JWT token validated",
            "Session created",
            "Password reset email sent",
        ],
        "error": [
            "JWT validation failed",
            "Invalid credentials",
            "Token expired",
            "Account locked",
            "2FA verification failed",
        ],
    },
    "worker": {
        "info": [
            "Job completed successfully",
            "Task queued and processed",
            "Batch processing finished",
            "Email notification sent",
        ],
        "error": [
            "Job failed after 3 retries",
            "Task timeout",
            "Message processing error",
            "Dead letter queue reached",
        ],
        "warning": [
            "Job running longer than expected",
            "Queue depth above threshold",
        ],
    },
}


def generate_ip() -> str:
    return f"{random.randint(10, 192)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def generate_user_id() -> str:
    return str(random.randint(1000, 9999))


def generate_trace_id() -> str:
    return str(uuid.uuid4())[:16]


def generate_log(service: str, level: str = None) -> dict:
    messages = LOG_MESSAGES.get(service, LOG_MESSAGES["backend"])
    if level is None:
        level = random.choices(
            ["info", "warning", "error", "debug"],
            weights=[70, 10, 15, 5],
        )[0]

    msg_pool = messages.get(level, messages["info"])
    message = random.choice(msg_pool)
    if "{latency}" in message:
        message = message.format(latency=random.randint(10, 5000))

    log = {
        "service": service,
        "level": level,
        "timestamp": datetime.now().isoformat() + "Z",
        "message": message,
        "traceId": generate_trace_id(),
        "metadata": {},
    }

    if random.random() < 0.3:
        log["userId"] = generate_user_id()

    if random.random() < 0.3:
        log["ip"] = generate_ip()

    if service == "backend" and random.random() < 0.5:
        log["latencyMs"] = random.uniform(5, 5000)
        log["endpoint"] = random.choice(["/api/users", "/api/orders", "/api/products", "/health"])

    if service == "auth" and random.random() < 0.4:
        log["statusCode"] = random.choice([200, 401, 403, 500])

    return log


def generate_failed_auth_log() -> dict:
    return {
        "service": "auth",
        "level": "error",
        "timestamp": datetime.now().isoformat() + "Z",
        "message": random.choice([
            "JWT validation failed",
            "Invalid credentials",
            "Token expired",
            "2FA verification failed",
        ]),
        "userId": generate_user_id(),
        "ip": generate_ip(),
        "traceId": generate_trace_id(),
        "metadata": {"reason": random.choice(["expired", "invalid_signature", "malformed_token"])},
    }


def write_logs_to_file(logs: list[dict], filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "a") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")


if __name__ == "__main__":
    import sys

    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    out_dir = Path(__file__).parent / "logs"
    out_dir.mkdir(exist_ok=True)

    for i in range(count):
        service = random.choice(SERVICES)
        log = generate_log(service)
        write_logs_to_file([log], out_dir / f"{service}.log")

    print(f"Wrote {count} logs to {out_dir}")