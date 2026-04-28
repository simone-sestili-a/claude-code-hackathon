"""PreToolUse hook — deterministic hard stops."""

import json
import re
import sys


PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",   # SSN
    r"\b4[0-9]{12}(?:[0-9]{3})?\b",  # Visa card
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",  # email (basic)
]

WRITE_TOOLS = {"create_ticket", "update_ticket", "send_response", "close_ticket"}
SECURITY_CLOSE_BLOCKED = {"close_ticket"}


def _contains_pii(text: str) -> bool:
    for pattern in PII_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _check(hook_input: dict) -> dict | None:
    """Return a block decision dict, or None to allow."""
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    account_status = tool_input.get("account_status") or tool_input.get("user", {}).get("account_status")
    if tool_name in WRITE_TOOLS and account_status == "FROZEN":
        return {"decision": "block", "reason": "FROZEN_ACCOUNT",
                "message": "Account is frozen. No write actions permitted until human review."}

    # External domain check runs before PII scan for send_response
    # (recipient is a structured field, not arbitrary user input)
    if tool_name == "send_response":
        recipient = tool_input.get("recipient", "")
        internal_domains = {"company.internal", "helpdesk.local"}
        domain = recipient.split("@")[-1] if "@" in recipient else ""
        if domain and domain not in internal_domains:
            return {"decision": "block", "reason": "EXTERNAL_EMAIL",
                    "message": f"External domain '{domain}' blocked. Humans send external emails."}

    # PII scan on all fields except structured routing fields (recipient, category, queue)
    excluded_keys = {"recipient", "category", "target_queue", "queue"}
    scan_input = {k: v for k, v in tool_input.items() if k not in excluded_keys}
    if _contains_pii(json.dumps(scan_input)):
        return {"decision": "block", "reason": "PII_DETECTED",
                "message": "PII pattern detected in tool parameters. Request blocked by security policy."}

    category = tool_input.get("category", "")
    if tool_name in SECURITY_CLOSE_BLOCKED and category == "SECURITY":
        return {"decision": "block", "reason": "SECURITY_CLOSE_BLOCKED",
                "message": "Security incidents cannot be auto-closed. Requires human review."}

    return None


def main() -> None:
    hook_input = json.load(sys.stdin)
    decision = _check(hook_input)
    if decision:
        print(json.dumps(decision))
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
