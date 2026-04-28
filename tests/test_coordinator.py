"""Tests for coordinator normalize + dry-run — no API key required."""

import asyncio

from src.schemas.request import InboundRequest
from src.coordinator.agent import normalize, run


def test_normalize_sets_request_id():
    raw = InboundRequest(channel="slack", body="My laptop won't boot", user_id="u042")
    normalized = normalize(raw)
    assert normalized.request_id != ""
    assert normalized.user_id == "u042"
    assert normalized.channel == "slack"


def test_normalize_preserves_body():
    raw = InboundRequest(channel="form", body="Need VPN access", user_id="u099")
    normalized = normalize(raw)
    assert normalized.body == "Need VPN access"


def test_dry_run_returns_ok():
    raw = InboundRequest(channel="email", body="VPN down", user_id="u001")
    normalized = normalize(raw)
    result = asyncio.run(run(normalized, dry_run=True))
    assert result["status"] == "ok"
    assert result["mode"] == "dry-run"
