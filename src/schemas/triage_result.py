from pydantic import BaseModel, Field
from src.schemas.request import Category, Priority, ImpactBucket


class TriageResult(BaseModel):
    request_id: str
    category: Category
    priority: Priority
    confidence: float = Field(ge=0.0, le=1.0)
    impact_bucket: ImpactBucket
    target_queue: str
    escalate: bool
    escalation_reason: str | None = None
    auto_resolved: bool = False
    auto_resolve_action: str | None = None
    reasoning_summary: str
    draft_response: str = ""
    retry_count: int = 0
    audit_log_ref: str = ""
