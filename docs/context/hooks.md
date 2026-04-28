# Hooks — IntakeAI

## The Core Distinction

> **Hook = deterministic hard stop. Prompt = probabilistic preference.**

If it must **never** happen → `PreToolUse` hook (runs before LLM, cannot be bypassed by the model).
If it **should not** happen but flexibility is acceptable → system prompt guidance.

Never use a prompt to enforce a security invariant. Never write a hook for a preference.
Every hook has a corresponding entry in `decisions/ADR-003-escalation-rules.md` explaining the classification.

## PreToolUse — Hard Stops (`src/hooks/pre_tool_use.py`)

Fires before every tool call. These patterns block unconditionally:

| Pattern | Error code | Block reason |
|---|---|---|
| Write tool on account with status `FROZEN` | `FROZEN_ACCOUNT` | Legal/financial hold |
| Any parameter containing raw PII pattern | `PII_EXFIL_GUARD` | Data exfiltration guard |
| `send_email` with external domain | `EXTERNAL_EMAIL_GUARD` | Exfiltration guard |
| `close_ticket` when category = SECURITY | `SECURITY_REQUIRES_HUMAN_CLOSE` | Security needs human close |
| Any action after `MAX_CONFIDENCE_RETRIES` hit | `LOOP_GUARD` | Infinite-loop guard |

Hook response format:
```json
{
  "decision": "block",
  "reason": "FROZEN_ACCOUNT",
  "message": "Account u456 is frozen. This request requires human review before any action."
}
```

## PostToolUse — Audit + Redaction (`src/hooks/post_tool_use.py`)

Fires after every successful tool call:
1. Log tool name, params (PII-redacted), result summary, timestamp to audit stream
2. Redact PII from tool output before it re-enters model context
3. On any write tool: emit event to audit stream

## Permission Modes

| Environment | Mode |
|---|---|
| Development | `default` (ask before write tools) |
| Demo / CI eval | `acceptEdits` (auto-approve reads, ask for writes) |
| Test harness | `bypassPermissions` (controlled env only, never production) |
