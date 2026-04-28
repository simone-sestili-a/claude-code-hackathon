"""Tests for PreToolUse hook — no API key required."""

from src.hooks.pre_tool_use import _check


def _make_input(tool_name: str, **kwargs) -> dict:
    return {"tool_name": tool_name, "tool_input": kwargs}


# --- Frozen account ---

def test_frozen_account_blocks_write():
    inp = _make_input("create_ticket", account_status="FROZEN", title="Need help")
    result = _check(inp)
    assert result is not None
    assert result["reason"] == "FROZEN_ACCOUNT"


def test_active_account_allows_write():
    inp = _make_input("create_ticket", account_status="ACTIVE", title="Need help")
    assert _check(inp) is None


def test_frozen_account_allows_read():
    inp = _make_input("lookup_ticket", account_status="FROZEN", ticket_id="T001")
    assert _check(inp) is None


# --- PII detection ---

def test_ssn_in_params_blocked():
    inp = _make_input("update_ticket", notes="SSN is 123-45-6789")
    result = _check(inp)
    assert result is not None
    assert result["reason"] == "PII_DETECTED"


def test_no_pii_passes():
    inp = _make_input("update_ticket", notes="Ticket escalated to infra team")
    assert _check(inp) is None


# --- External email ---

def test_external_email_blocked():
    inp = _make_input("send_response", recipient="user@gmail.com", body="Hello")
    result = _check(inp)
    assert result is not None
    assert result["reason"] == "EXTERNAL_EMAIL"


def test_internal_email_allowed():
    inp = _make_input("send_response", recipient="user@company.internal", body="Hello")
    assert _check(inp) is None


# --- Security close blocked ---

def test_security_close_blocked():
    inp = _make_input("close_ticket", ticket_id="T001", category="SECURITY")
    result = _check(inp)
    assert result is not None
    assert result["reason"] == "SECURITY_CLOSE_BLOCKED"


def test_non_security_close_allowed():
    inp = _make_input("close_ticket", ticket_id="T001", category="ACCESS")
    assert _check(inp) is None
