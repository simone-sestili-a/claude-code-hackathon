# Tool Design — IntakeAI

## The 4-5 Tool Limit
Each specialist has at most **5 tools**. Reliability drops past this. If you feel the need for a 6th, split the specialist.

## When to Reach for Which Approach

| Situation | Use |
|---|---|
| Coordinator / specialist agent loop | `claude_agent_sdk.query()` — stateless, single request |
| Multi-turn conversation, session resume | `ClaudeSDKClient` with session ID |
| Exposing tools to a fresh Claude session | FastMCP server — never inline tool definitions |
| Hard-blocking a dangerous pattern | `PreToolUse` hook (see `docs/context/hooks.md`) |

## Tool Description Template

Every tool description answers these five questions:
1. **What it does** — one sentence
2. **What it does NOT do** — equally important, one sentence
3. **Input format** — with a concrete example
4. **When to reach for it** — trigger conditions
5. **Edge cases** — what returns empty or error and why

## Error Response Shape (always)

```python
class ToolResult(BaseModel):
    success: bool
    data: dict | None = None
    is_error: bool = False
    error_code: str | None = None      # "NOT_FOUND" | "FROZEN_ACCOUNT" | "PII_DETECTED"
    error_reason: str | None = None    # For humans / logs
    retry_guidance: str | None = None  # What the agent should try next
```

The agent uses `error_code` for recovery logic. `error_reason` is for humans.
All error codes are defined in `src/tools/error_codes.py`.

## Tool Annotations

```python
# Read-only — enables PreToolUse hook to distinguish read vs write
@tool(readOnlyHint=True, idempotentHint=True)
def lookup_ticket(ticket_id: str) -> ToolResult: ...

# Write — hook will inspect these
@tool(readOnlyHint=False, idempotentHint=False)
def create_ticket(request: CreateTicketRequest) -> ToolResult: ...
```

## MCP Server Tools

Exposed via FastMCP in `src/mcp_server/server.py`:

| Tool name | Type | Description |
|---|---|---|
| `mcp__helpdesk__lookup_ticket` | read | Fetch ticket by ID or fuzzy description |
| `mcp__helpdesk__get_user_context` | read | User profile, history, flagged status |
| `mcp__helpdesk__get_asset_context` | read | CI/asset from CMDB |
| `mcp__helpdesk__search_knowledge_base` | read | Semantic search over KB articles |
| `mcp__helpdesk__create_ticket` | write | Create ticket (PII-blocked by hook) |
| `mcp__helpdesk__update_ticket` | write | Update status, priority, queue |
| `mcp__helpdesk__send_response` | write | Send response (external domain blocked) |
