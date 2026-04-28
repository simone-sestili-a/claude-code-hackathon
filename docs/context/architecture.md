# Architecture — IntakeAI

## Agent Loop

```
Inbound Request (email / Slack / form / alert)
       │
       ▼
┌──────────────────────────────────────┐
│          COORDINATOR AGENT           │
│  model: claude-opus-4-7              │
│  1. Normalize & deduplicate          │
│  2. Classify category + priority     │
│  3. Enrich (user, asset, history)    │
│  4. Route → Task tool → specialist   │
│  5. Validate output (schema + retry) │
│  6. Write audit log (reasoning chain)│
└────────────┬─────────────────────────┘
             │  Task tool — context passed explicitly per call
     ┌───────┼──────────┬──────────┐
     ▼       ▼          ▼          ▼
  INFRA   SECURITY   ACCESS   GENERAL IT
(claude-sonnet-4-6 · 4-5 tools each)
```

## Non-Negotiable Rules

1. **Task subagents do NOT inherit coordinator context.** Every specialist prompt is self-contained. Use the template below — never improvise.
2. **`stop_reason` is always checked.** `end_turn` → proceed; `max_tokens` / `error_*` → log + escalate.
3. **Coordinator owns routing.** Specialists signal wrong queue via structured output; coordinator re-routes.
4. **Validation-retry is in coordinator only.** Max 3 retries. Log retry count + error type per request.
5. **Log reasoning chain, not just the answer.** `thinking` / `reasoning_summary` goes to audit log.

## Subagent Prompt Template

```python
task_prompt = f"""
You are the {specialist_name} specialist for IT helpdesk triage.

## Your Mandate
{specialist_mandate}

## The Request
{normalized_request_json}

## Enrichment Context
- User: {user_context}
- Asset: {asset_context}
- Account status: {account_status}
- Related open tickets: {related_tickets}

## Classification from Coordinator
- Category: {category}
- Initial priority: {initial_priority}
- Confidence: {confidence}

## Your Tools
{tool_list_with_descriptions}

## Required Output Schema
Return ONLY valid JSON matching this exact schema:
{output_schema_json}
"""
```

## When to Use Subagents (Opus 4.7 — must be explicit)

Opus 4.7 does not fan out autonomously. Say it explicitly.

**Use parallel subagents when:**
- Processing multiple inbound requests at once → "use parallel subagents, one per request"
- Running eval across the full dataset → "fan out to subagents, one per eval category"
- Task touches more than 3 specialist files

**Do not use subagents for:**
- Modifying a single function or tool
- Adding one eval case or fixing a type annotation

## Repository Structure

```
src/
├── coordinator/
│   ├── agent.py          # Entry point — full coordinator loop
│   ├── classifier.py     # Category + priority classification
│   ├── enrichment.py     # User / asset context
│   ├── router.py         # Routes to specialists, owns task prompts
│   ├── validator.py      # Schema validation + retry loop
│   └── logger.py         # Structured audit log
├── specialists/
│   ├── infra.py          # Infrastructure / P1 severity
│   ├── security.py       # Security incidents
│   ├── access.py         # IAM / password resets
│   └── general_it.py    # How-to / general support
├── tools/                # see docs/context/tools.md
├── hooks/                # see docs/context/hooks.md
├── mcp_server/
│   ├── server.py         # FastMCP server definition
│   └── schemas.py        # Pydantic I/O models
└── schemas/
    ├── request.py        # Normalized inbound request
    ├── triage_result.py  # Coordinator output
    └── specialist_result.py
```
