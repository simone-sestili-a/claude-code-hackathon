# Escalation Rules — IntakeAI

Vague escalation rules ("when the agent isn't sure") produce inconsistent behavior.
Every rule uses: **category AND confidence threshold AND impact bucket**.

## Impact Buckets

| Bucket | Threshold | Examples |
|---|---|---|
| LOW | < $1k | Password reset, how-to question |
| MEDIUM | $1k–$10k | Laptop replacement, software license |
| HIGH | > $10k | Server outage, data breach, bulk access revoke |

## Decision Matrix

```
             CONFIDENCE
             ≥ 0.85    0.70–0.84    < 0.70
           ┌──────────┬──────────┬──────────┐
  LOW      │ AUTOMATE │ AUTOMATE │ ESCALATE │
  MEDIUM   │ AUTOMATE │ ESCALATE │ ESCALATE │
  HIGH     │ ESCALATE │ ESCALATE │ ESCALATE │
           └──────────┴──────────┴──────────┘
```

**Always escalate regardless of confidence or impact:**
- `category ∈ {SECURITY, COMPLIANCE, LEGAL_HOLD}`
- `account_status = FROZEN`
- Validation retry count ≥ 3

## Autonomous Decisions (agent acts alone)

| Decision | Condition |
|---|---|
| Classify priority P1–P4 | Confidence ≥ 0.85 |
| Route to internal queue | Confidence ≥ 0.80 AND impact ∈ {LOW, MEDIUM} |
| Auto-resolve password reset | Matches reset pattern AND user not flagged |
| Auto-resolve "how do I" | KB answer confidence ≥ 0.90 |
| Mark as duplicate | Match score ≥ 0.95 with open ticket |
| Enrich with context | Always (read-only) |

## Escalation Payload Shape

```json
{
  "escalation_reason": "LOW_CONFIDENCE_HIGH_IMPACT",
  "category": "INFRA",
  "priority": "P2",
  "confidence": 0.72,
  "impact_bucket": "HIGH",
  "reasoning_summary": "...",
  "recommended_queue": "infra-senior",
  "draft_response": "...",
  "full_audit_log_ref": "audit-2026-04-28-abc123"
}
```
