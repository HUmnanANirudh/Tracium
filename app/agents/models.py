from typing import Literal, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    evidence_id: str
    source: str
    timestamp: Optional[str] = None
    summary: str
    related_incident_ids: list[str] = Field(default_factory=list)


class Verdict(BaseModel):
    classification: Literal[
        "true_positive",
        "false_positive",
        "inconclusive",
    ]
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]
    reasoning: str
    confirmed_facts: list[str] = Field(default_factory=list)
    inferred_relationships: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class ResponseProposal(BaseModel):
    action: Literal[
        "block_ip",
        "disable_user",
        "isolate_service",
        "notify",
    ]
    target: str
    risk_tier: Literal["low", "medium", "high"]
    justification: str
    rollback_plan: str
    requires_approval: bool = True


class InvestigationOutcome(BaseModel):
    verdict: Verdict
    response_proposal: Optional[ResponseProposal] = None

