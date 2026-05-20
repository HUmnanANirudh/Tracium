from fastapi import Query
from datetime import datetime
from typing import Optional
from app.models import LogQueryParams, LogLevel, ServiceName
from app.log_store import store


async def query_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    search: Optional[str] = None,
    userId: Optional[str] = None,
    ip: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
):
    params = LogQueryParams(
        service=ServiceName(service) if service else None,
        level=LogLevel(level) if level else None,
        start_time=start_time,
        end_time=end_time,
        search=search,
        userId=userId,
        ip=ip,
        limit=limit,
        offset=offset,
    )
    return {"logs": store.query(params), "count": len(store.query(params))}


async def get_services():
    return {"services": store.get_services()}