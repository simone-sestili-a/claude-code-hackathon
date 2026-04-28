# Scope Boundaries — What We Are NOT Automating

> Legal-facing view of agent scope. Do not cross these without explicit team decision.

| Excluded | Reason |
|---|---|
| Security incident response | Human judgment required; forensics chain of custody |
| Sending external communications | Reputation risk — drafts generated, humans send |
| Bulk access revocation | Irreversible; requires CAB approval |
| Any action on frozen accounts | Legal/financial hold — hard-stopped by PreToolUse hook |
| Auto-closing P1 incidents | Masks SLA reality; post-incident review required |
| Compliance / KYC document handling | Regulatory scope; requires certified human process |
| Overriding another human's escalation (within 24h) | Agent cannot countermand a human routing decision |
| Password resets for admin / service accounts | Privilege escalation risk; requires L3 approval |

## Open Placeholders

| ID | Location | What's missing |
|---|---|---|
| `[TODO-01]` | `evals/datasets/normal_traffic.json` | 200+ labeled tickets across all categories |
| `[TODO-02]` | `evals/datasets/adversarial.json` | 50+ prompt injection + social engineering cases |
| `[TODO-03]` | `evals/datasets/boundary_cases.json` | 30+ threshold/ambiguity boundary cases |
| `[TODO-04]` | `src/tools/cmdb_tools.py` | Real CMDB connector (currently mocked) |
| `[TODO-05]` | `src/tools/action_tools.py` | Real ticket system connector (writes to local JSON) |
| `[TODO-06]` | `src/mcp_server/server.py` | MCP server not yet registered in agent config |
| `[TODO-07]` | `decisions/ADR-005-eval-strategy.md` | Stratified sampling rationale incomplete |
| `[TODO-08]` | Challenge 8 — The Loop | Human override → labeled example feedback loop |
| `[TODO-09]` | `presentation.html` | HTML deck to be generated with Claude Code |
