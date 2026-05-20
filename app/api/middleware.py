from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import config


async def payload_size_middleware(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/logs/ingest":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > config.max_payload_bytes:
            return JSONResponse(
                status_code=413,
                content={"error": f"Payload too large. Max: {config.max_payload_bytes} bytes"},
            )
    response = await call_next(request)
    return response