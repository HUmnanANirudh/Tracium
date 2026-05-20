from fastapi import Query
from app.log_store import store


async def get_security_alerts(limit: int = Query(default=100, le=500)):
    return {"alerts": store.get_alerts(limit=limit)}