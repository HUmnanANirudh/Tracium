from datetime import datetime
from app.log_store import store
from app.core.config import config


async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": store.get_services(),
        "stats": {
            "total_logs": len(store.logs),
            "total_incidents": len(store.incidents),
            "total_alerts": len(store.alerts),
        },
        "rate_limits": {
            "max_payload_bytes": config.max_payload_bytes,
            "max_logs_per_request": config.max_logs_per_request,
            "max_requests_per_minute": config.max_requests_per_minute,
            "max_logs_per_minute": config.max_logs_per_minute,
        },
    }