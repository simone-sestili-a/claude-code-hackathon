"""Tests for Pydantic schemas — no API key required."""

import pytest
from pydantic import ValidationError

from src.schemas.request import InboundRequest, NormalizedRequest
from src.schemas.triage_result import TriageResult
from src.tools.error_codes import ToolResult


def test_inbound_request_valid():
    req = InboundRequest(channel="email", body="VPN is down", user_id="u001")
    assert req.channel == "email"
    assert req.attachments == []


def test_inbound_request_invalid_channel():
    with pytest.raises(ValidationError):
        InboundRequest(channel="fax", body="test", user_id="u001")


def test_triage_result_confidence_bounds():
    with pytest.raises(ValidationError):
        TriageResult(
            request_id="r1",
            category="INFRA",
            priority="P1",
            confidence=1.5,  # > 1.0 — invalid
            impact_bucket="HIGH",
            target_queue="infra",
            escalate=True,
            reasoning_summary="test",
        )


def test_triage_result_valid():
    result = TriageResult(
        request_id="r1",
        category="ACCESS",
        priority="P3",
        confidence=0.92,
        impact_bucket="LOW",
        target_queue="access-self-service",
        escalate=False,
        reasoning_summary="Password reset — high confidence, low impact.",
    )
    assert result.escalate is False
    assert result.auto_resolved is False


def test_tool_result_error():
    r = ToolResult(success=False, is_error=True, error_code="NOT_FOUND",
                   error_reason="Ticket T999 not found", retry_guidance="Try lookup by user_id instead.")
    assert r.is_error is True
    assert r.error_code == "NOT_FOUND"
