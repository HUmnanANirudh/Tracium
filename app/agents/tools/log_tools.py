import json
from typing import Optional
from langchain_core.tools import tool
from datetime import datetime
from app.log_store import store
from app.models import LogQueryParams

@tool
def search_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    userId: Optional[str] = None,
    ip: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    Search logs for specific criteria.
    Args:
        service: The service name (frontend, backend, auth, worker)
        level: Log level (info, warning, error, critical, debug)
        userId: The user ID to search for
        ip: The IP address to search for
        search: A keyword search within the log message
        limit: Maximum number of logs to return (default 50, max 100)
    Returns:
        A list of matching logs.
    """
    limit = min(limit, 100)
    
    params_dict = {"limit": limit}
    if service: params_dict["service"] = service
    if level: params_dict["level"] = level
    if userId: params_dict["userId"] = userId
    if ip: params_dict["ip"] = ip
    if search: params_dict["search"] = search
    
    params = LogQueryParams(**params_dict)
    
    results = store.query(params)
    
    # Strip out timestamps, traceIds, and metadata to save LLM tokens
    slim_logs = []
    for log in results:
        slim = {}
        for k in ["id", "service", "level", "message", "userId", "ip"]:
            if k in log and log[k] is not None:
                slim[k] = log[k]
        slim_logs.append(slim)
        
    return json.dumps(slim_logs)
