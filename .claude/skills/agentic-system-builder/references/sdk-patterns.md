# Claude Agent SDK — Python Patterns

Package: `claude-code-sdk` (PyPI) — import as `claude_code_sdk`
Latest stable: check `pip show claude-code-sdk`

---

## Imports

```python
# Core
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient, query

# Subagents
from claude_code_sdk import AgentDefinition

# Custom MCP tools
from claude_code_sdk import tool, create_sdk_mcp_server

# Hooks
from claude_code_sdk import HookMatcher, HookContext, HookInput

# Message types
from claude_code_sdk import ResultMessage
```

---

## One-Shot Query (`query()`)

Use for stateless, single-turn calls — specialist agents, fire-and-forget tasks.

```python
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions, ResultMessage

async def run_specialist(prompt: str, context: str) -> str | None:
    options = ClaudeCodeOptions(
        model="claude-sonnet-4-6",
        system_prompt=f"You are a specialist. Context: {context}",
        tools=["Read", "Grep"],           # restrict tool availability
        permission_mode="bypassPermissions",
        max_turns=10,
    )
    # Let the generator exhaust naturally — don't break early
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage):
            return msg.result if msg.subtype == "success" else None
    return None
```

---

## Multi-Turn Client (`ClaudeSDKClient`)

Use for the coordinator — supports `continue_conversation=True` and hooks.

```python
import asyncio
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient, ResultMessage

async def run_coordinator(prompt: str) -> tuple[str | None, list]:
    options = ClaudeCodeOptions(
        model="claude-opus-4-7",
        system_prompt="You are the coordinator...",
        allowed_tools=["Task", "Read", "Write", "Bash"],  # Task enables subagent delegation
        permission_mode="default",
        max_turns=50,
    )

    result = None
    messages = []

    # Wrap in timeout to prevent disconnect hang (Issue #378)
    async with asyncio.timeout(120):
        async with ClaudeSDKClient(options=options) as agent:
            await agent.query(prompt=prompt)
            async for msg in agent.receive_response():
                messages.append(msg)
                if isinstance(msg, ResultMessage):
                    result = msg.result if msg.subtype == "success" else None

    return result, messages
```

---

## Subagents (`AgentDefinition`)

Specialists receive NO coordinator context — pass everything explicitly in the prompt template.

```python
from claude_code_sdk import ClaudeCodeOptions, AgentDefinition, query

options = ClaudeCodeOptions(
    allowed_tools=["Task", "Read"],       # Task = coordinator can delegate
    agents={
        "classifier": AgentDefinition(
            description="Classify the inbound request into a category",
            prompt="Classify the following request into one of: IT, HR, SECURITY, FACILITIES. Return JSON: {\"category\": \"...\", \"confidence\": 0.0-1.0}",
            tools=["Read"],               # tools= restricts what specialist can use
            model="claude-haiku-4-5-20251001",
        ),
        "enricher": AgentDefinition(
            description="Enrich a classified request with metadata",
            prompt="Given this classified request, add priority, SLA, and routing queue. Return JSON: {\"priority\": \"P1|P2|P3\", \"queue\": \"...\", \"sla_hours\": N}",
            tools=[],                     # no tools — pure reasoning
            model="claude-sonnet-4-6",
        ),
    },
)
```

---

## Custom MCP Tools (`@tool` + `create_sdk_mcp_server`)

```python
from typing import Annotated, Any
from claude_code_sdk import tool, create_sdk_mcp_server, ClaudeCodeOptions, query

@tool("lookup_user", "Look up a user by ID", {
    "user_id": Annotated[str, "The user's unique identifier"],
})
async def lookup_user(args: dict[str, Any]) -> dict[str, Any]:
    user_id = args["user_id"]
    # ... real lookup logic ...
    return {"content": [{"type": "text", "text": f"User {user_id}: Jane Doe, dept=IT"}]}

@tool("create_ticket", "Create a new helpdesk ticket", {
    "title": Annotated[str, "Ticket title"],
    "body": Annotated[str, "Ticket body"],
    "priority": Annotated[str, "P1, P2, or P3"],
})
async def create_ticket(args: dict[str, Any]) -> dict[str, Any]:
    # ... real create logic ...
    return {"content": [{"type": "text", "text": f"Ticket TKT-001 created"}]}


async def main():
    server = create_sdk_mcp_server(
        name="helpdesk",
        version="1.0.0",
        tools=[lookup_user, create_ticket],
    )

    options = ClaudeCodeOptions(
        mcp_servers={"helpdesk": server},
        allowed_tools=["mcp__helpdesk__lookup_user", "mcp__helpdesk__create_ticket"],
    )
    # ... query ...
```

MCP tool names follow `mcp__{server}__{function}` convention.

---

## Hooks (`HookMatcher`)

Use hooks for deterministic enforcement. `can_use_tool` is non-functional — always use `HookMatcher`.

```python
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient, HookMatcher, HookContext, HookInput
from typing import Any

async def block_frozen_accounts(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    tool_input = input_data.get("tool_input", {})
    if tool_input.get("account_status") == "FROZEN":
        return {
            "hookSpecificOutput": {
                "hookEventName": input_data["hook_event_name"],
                "permissionDecision": "deny",
                "permissionDecisionReason": "Account FROZEN — write blocked",
            }
        }
    return {}  # empty dict = allow

async def audit_logger(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    print(f"[audit] {input_data.get('tool_name')} called")
    return {}

options = ClaudeCodeOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="create_ticket|update_ticket", hooks=[block_frozen_accounts]),
            HookMatcher(hooks=[audit_logger]),   # no matcher = all tools
        ],
    }
)
```

Hook return values:
- `{}` → allow
- `{"hookSpecificOutput": {"hookEventName": "...", "permissionDecision": "deny", "permissionDecisionReason": "..."}}` → block
- `{"hookSpecificOutput": {"hookEventName": "...", "additionalContext": "..."}}` → allow + inject context

---

## Options Reference

| Parameter | Type | Notes |
|---|---|---|
| `model` | `str` | Full model ID: `"claude-opus-4-7"`, `"claude-sonnet-4-6"`, `"claude-haiku-4-5-20251001"` |
| `system_prompt` | `str` | Overrides CLAUDE.md if provided |
| `allowed_tools` | `list[str]` | Pre-approves permissions; must include `"Task"` for subagents |
| `tools` | `list[str] \| None` | Restricts availability; `None` = all defaults; `[]` = no tools |
| `permission_mode` | `str` | `"default"`, `"plan"`, `"acceptEdits"`, `"bypassPermissions"` |
| `max_turns` | `int` | Default 50 |
| `mcp_servers` | `dict` | MCP server config |
| `agents` | `dict[str, AgentDefinition]` | Named subagents |
| `hooks` | `dict` | `HookMatcher` lists per event |
| `cwd` | `str` | Working directory for file operations |
