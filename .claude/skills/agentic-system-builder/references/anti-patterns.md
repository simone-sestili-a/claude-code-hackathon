# Claude Agent SDK — Anti-Patterns and Corrections

Source: `claude-agent-sdk-skill-autoupdated/rules/claude-agent-sdk-py.md` (v0.1.69)

---

## Wrong package name

```python
# WRONG
from anthropic import ClaudeSDKClient
from claude_agent_sdk import query   # underscore — wrong package name

# CORRECT
from claude_code_sdk import ClaudeSDKClient, query, tool, create_sdk_mcp_server
```

---

## No context manager for ClaudeSDKClient

```python
# WRONG — client never cleaned up, can leak subprocess
client = ClaudeSDKClient(options)
result = await client.query("...")

# CORRECT
async with ClaudeSDKClient(options=options) as client:
    await client.query("...")
    async for msg in client.receive_response():
        ...
```

---

## Disconnect hang (100% CPU)

```python
# WRONG — can hang forever (Issue #378)
async with ClaudeSDKClient(options) as client:
    await client.query("...")

# CORRECT — wrap in timeout
import asyncio
async with asyncio.timeout(120):
    async with ClaudeSDKClient(options=options) as client:
        await client.query("...")
        ...

# ALTERNATIVE — env var for graceful shutdown
import os
os.environ["CLAUDE_CODE_STREAM_CLOSE_TIMEOUT"] = "10000"  # ms
```

---

## camelCase options (TypeScript habit)

```python
# WRONG
options = ClaudeCodeOptions(
    permissionMode="bypassPermissions",
    maxTurns=10,
    systemPrompt="...",
    allowedTools=["Read"],
)

# CORRECT — always snake_case in Python
options = ClaudeCodeOptions(
    permission_mode="bypassPermissions",
    max_turns=10,
    system_prompt="...",
    allowed_tools=["Read"],
)
```

---

## Using `allowed_tools` to restrict tools (it doesn't)

```python
# WRONG — allowed_tools is a permission pre-approval list, NOT a restriction
options = ClaudeCodeOptions(allowed_tools=[])         # falsy, silently omitted
options = ClaudeCodeOptions(allowed_tools=["Read"])   # only pre-approves "Read", still can use others

# CORRECT — use tools= to control which tools are available
options = ClaudeCodeOptions(tools=[])                 # disables all tools
options = ClaudeCodeOptions(tools=["Read", "Grep"])   # only these two enabled
options = ClaudeCodeOptions(tools=None)               # default toolset (omits --tools)
```

---

## Forgetting "Task" in allowed_tools for subagents

```python
# WRONG — coordinator can't delegate to subagents
options = ClaudeCodeOptions(allowed_tools=["Read", "Write"])

# CORRECT — Task tool enables subagent delegation
options = ClaudeCodeOptions(allowed_tools=["Task", "Read", "Write"])
```

---

## Breaking out of `query()` generator early

```python
# WRONG — RuntimeError that cascades to CancelledError (Issue #454)
async for msg in query(prompt="...", options=options):
    if isinstance(msg, ResultMessage):
        result = msg.result
        break  # ← DO NOT break

# CORRECT — let generator exhaust naturally (it ends after ResultMessage)
async for msg in query(prompt="...", options=options):
    if isinstance(msg, ResultMessage):
        result = msg.result
```

---

## Using `can_use_tool` for permission enforcement (it never fires)

```python
# WRONG — can_use_tool callbacks are never invoked (Issue #469)
options = ClaudeCodeOptions(can_use_tool=my_handler)  # silent no-op

# CORRECT — use PreToolUse HookMatcher
from claude_code_sdk import HookMatcher

options = ClaudeCodeOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Write|Edit", hooks=[my_permission_hook]),
        ]
    }
)
```

---

## Wrong `@tool` decorator signature

```python
# WRONG — bare function, wrong return type, args not a dict
def get_user(user_id: str) -> str:
    return f"User {user_id}"

# CORRECT — @tool decorator, handler takes dict, returns content dict
from claude_code_sdk import tool
from typing import Annotated, Any

@tool("get_user", "Get user by ID", {
    "user_id": Annotated[str, "The user's unique ID"],
})
async def get_user(args: dict[str, Any]) -> dict[str, Any]:
    user_id = args["user_id"]
    return {"content": [{"type": "text", "text": f"User {user_id}: Jane Doe"}]}
```

---

## TypedDict attribute access (fails at runtime)

```python
# WRONG — TypedDicts are plain dicts at runtime (Issue #623)
config = ThinkingConfigEnabled(type="enabled", budget_tokens=20000)
config.budget_tokens  # AttributeError

# CORRECT — use dict key access
config["budget_tokens"]  # ✅
```

Types that are TypedDict (plain dict at runtime): `ThinkingConfig*`, `SyncHookJSONOutput`,
`AsyncHookJSONOutput`, `HookSpecificOutput*`, `McpStdioServerConfig`, `McpSSEServerConfig`,
`McpHttpServerConfig`, `SandboxSettings`.

Types that are dataclasses (dot-notation OK): `AgentDefinition`, `HookMatcher`, `TextBlock`,
`ResultMessage`.

---

## ANTHROPIC_LOG=debug corrupts JSON protocol

```python
# WRONG — corrupts JSON wire format between SDK and CLI
options = ClaudeCodeOptions(env={"ANTHROPIC_LOG": "debug"})

# CORRECT — use stderr callback for debug output
import logging
logger = logging.getLogger("claude-sdk")
options = ClaudeCodeOptions(
    stderr=lambda data: logger.debug(f"CLI: {data}")
)
```

---

## StructuredOutput wrapping bug

```python
# WRONG — agent non-deterministically wraps JSON in {"output": {...}} (Issue #571)
options = ClaudeCodeOptions(system_prompt="Analyze the data")

# BETTER — use output_format parameter instead of StructuredOutput tool
options = ClaudeCodeOptions(
    output_format={"type": "json_schema", "schema": your_schema}
)

# OR — add explicit instruction if using StructuredOutput tool
options = ClaudeCodeOptions(
    system_prompt="Analyze the data. CRITICAL: When using StructuredOutput, provide the JSON object directly — do NOT wrap in {'output': {...}}"
)
```
