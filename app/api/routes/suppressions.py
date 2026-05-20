from pydantic import BaseModel
from app.incident_engine import engine


class SuppressionRequest(BaseModel):
    pattern: str
    seconds: int = 3600
    reason: str


async def create_suppression(body: SuppressionRequest):
    rule = engine.dedup.suppress(
        pattern=body.pattern,
        seconds=body.seconds,
        reason=body.reason,
    )
    return {"status": "ok", "rule": rule.model_dump()}


async def get_suppressions():
    return {"suppressions": engine.dedup.suppressions}