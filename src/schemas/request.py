from typing import Literal
from pydantic import BaseModel


Channel = Literal["email", "slack", "form", "alert"]
Category = Literal["INFRA", "SECURITY", "ACCESS", "GENERAL_IT", "COMPLIANCE", "LEGAL_HOLD", "UNKNOWN"]
Priority = Literal["P1", "P2", "P3", "P4"]
ImpactBucket = Literal["LOW", "MEDIUM", "HIGH"]
AccountStatus = Literal["ACTIVE", "FROZEN", "SUSPENDED"]


class InboundRequest(BaseModel):
    channel: Channel
    body: str
    user_id: str
    subject: str = ""
    attachments: list[str] = []


class NormalizedRequest(BaseModel):
    request_id: str
    channel: Channel
    body: str
    subject: str
    user_id: str
    account_status: AccountStatus = "ACTIVE"
    is_duplicate: bool = False
    duplicate_of: str | None = None
