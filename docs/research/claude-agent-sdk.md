# Claude Agent SDK: Ultra-Detailed Comprehensive Guide

## Table of Contents

1. [What is the Claude Agent SDK?](#what-is-the-claude-agent-sdk)
2. [Key Differences from Raw Anthropic API](#key-differences-from-raw-anthropic-api)
3. [Installation and Setup](#installation-and-setup)
4. [Authentication](#authentication)
5. [Agent Loop Architecture](#agent-loop-architecture)
6. [Stop Reasons and Result Handling](#stop-reasons-and-result-handling)
7. [Session Management](#session-management)
8. [Subagents: The Coordinator Pattern](#subagents-the-coordinator-pattern)
9. [Custom Tools and MCP Servers](#custom-tools-and-mcp-servers)
10. [Permissions and Hooks](#permissions-and-hooks)
11. [Advanced Patterns and Examples](#advanced-patterns-and-examples)

---

## What is the Claude Agent SDK?

The Claude Agent SDK (formerly known as the Claude Code SDK) is a Python and TypeScript/JavaScript framework that brings Claude Code's autonomous agent capabilities into your applications as a library. Instead of using the Claude Code CLI interactively, you can programmatically control Claude agents that autonomously:

- Read and write files
- Run terminal commands and scripts
- Edit code with precision
- Search codebases with glob and regex patterns
- Search and fetch content from the web
- Execute custom tools you define
- Spawn specialized subagents
- Ask clarifying questions and handle approvals

The Agent SDK includes the same agentic loop, built-in tools, context management, and hooks that power Claude Code itself. You get production-grade control over cost, permissions, reasoning depth, and tool execution without building your own tool loop.

### Core Value Proposition

**With the raw Anthropic API:** You implement the tool loop manually—send a prompt, parse tool calls, execute them, feed results back, repeat until done.

**With the Agent SDK:** Claude manages the entire loop autonomously. The SDK handles tool execution, parallelization, permission checks, hooks, and continuity across turns.

---

## Key Differences from Raw Anthropic API

### 1. **Tool Execution Loop**

**Anthropic Client SDK:**
```python
response = client.messages.create(...)
while response.stop_reason == "tool_use":
    results = []
    for tool_call in response.content:
        if tool_call.type == "tool_use":
            result = execute_tool(tool_call)  # You implement this
            results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": result})
    response = client.messages.create(
        messages=[...previous..., {"role": "user", "content": results}],
        ...
    )
```

**Agent SDK:**
```python
async for message in query(prompt="Fix the bug in auth.py"):
    print(message)  # Tools run automatically, no loop implementation needed
```

### 2. **Built-in Tools**

**Agent SDK includes:**
- File operations: `Read`, `Write`, `Edit`
- Search: `Glob`, `Grep`
- Execution: `Bash`
- Web: `WebSearch`, `WebFetch`
- Orchestration: `Agent` (subagents), `Skill`, `AskUserQuestion`
- MCP integration: connect external systems via the Model Context Protocol

**Client SDK:**
- You define tools yourself as JSON schemas
- You implement tool execution logic
- More control but more boilerplate

### 3. **Context Management**

**Agent SDK:**
- Automatic prompt caching (CLAUDE.md content cached across turns)
- Automatic context compaction when approaching token limit
- Sessions persist automatically to disk
- Easy resume/fork for multi-turn workflows

**Client SDK:**
- You manage context windows yourself
- You implement caching if needed
- No automatic session persistence

### 4. **Permissions and Approvals**

**Agent SDK:**
- Declarative permission rules (allow/deny/ask)
- Permission modes: `default`, `acceptEdits`, `bypassPermissions`, `plan`, `dontAsk`, `auto`
- Built-in hooks for custom approval logic
- Works with `.claude/settings.json` for persistent policy

**Client SDK:**
- You decide what the model can request
- You implement approval flow if needed
- No built-in permission system

### 5. **Subagents and Context Isolation**

**Agent SDK:**
- Define subagents with specialized instructions
- Each subagent runs in isolated context
- Parallel execution of multiple subagents
- Coordinator pattern: main agent delegates to specialists

**Client SDK:**
- No first-class subagent support
- You manage context isolation manually

---

## Installation and Setup

### Python

```bash
pip install claude-agent-sdk
```

Requires Python 3.9+

### TypeScript/JavaScript

```bash
npm install @anthropic-ai/claude-agent-sdk
```

The SDK bundles native Claude Code binaries as optional dependencies for your platform. If your package manager skips optional dependencies, set `pathToClaudeCodeExecutable` to a separately installed `claude` binary.

Node.js 16+ required.

---

## Authentication

The Agent SDK supports multiple authentication methods:

### 1. **Anthropic API Key (Recommended)**

Set the environment variable:
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

Get your API key from [Anthropic Console](https://platform.claude.com/)

### 2. **Amazon Bedrock**

```bash
export CLAUDE_CODE_USE_BEDROCK=1
# Configure AWS credentials (AWS CLI, environment variables, or IAM role)
```

### 3. **Google Vertex AI**

```bash
export CLAUDE_CODE_USE_VERTEX=1
# Configure Google Cloud credentials
gcloud auth application-default login
```

### 4. **Microsoft Azure AI Foundry**

```bash
export CLAUDE_CODE_USE_FOUNDRY=1
# Configure Azure credentials
az login
```

### Important Note on Third-Party Authentication

Anthropic does not allow third-party developers to offer `claude.ai` login or rate-limit integration for their products, including agents built on the Claude Agent SDK. Always use API key authentication methods for production deployments.

---

## Agent Loop Architecture

### How It Works Internally

The Agent SDK runs the same autonomous loop that powers Claude Code:

```
┌─────────────────────────────────────────┐
│ 1. Receive Prompt                       │
│    - User prompt + system prompt        │
│    - Tool definitions + conversation    │
│    - CLAUDE.md + project context        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 2. Evaluate and Respond                 │
│    - Claude generates response          │
│    - May include tool calls             │
│    - May include text                   │
└──────────────┬──────────────────────────┘
               │
               ├─► No tool calls? GO TO 5
               │
┌──────────────▼──────────────────────────┐
│ 3. Execute Tools                        │
│    - Run each tool call                 │
│    - Collect results                    │
│    - Can run read-only tools in parallel│
│    - State-modifying tools run serially │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 4. Feed Back to Claude                  │
│    - Include tool results in context    │
│    - GOTO 2 (next turn)                 │
└──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 5. Return Result                        │
│    - Final text response                │
│    - Token usage + cost                 │
│    - Session ID                         │
│    - Stop reason                        │
└──────────────────────────────────────────┘
```

### Turns vs Requests

A **turn** is one round trip: Claude responds (with or without tool calls), tools execute, and the result feeds back. Turns continue until Claude produces a response with no tool calls.

**Example:** "Fix failing tests in auth.ts"

- **Turn 1:** Claude calls `Bash` to run tests, gets failures
- **Turn 2:** Claude reads `auth.ts` and test files
- **Turn 3:** Claude calls `Edit` to fix code, reruns tests
- **Final Turn:** Claude responds with "Fixed the bug, all tests pass"

You can limit turns with `max_turns` / `maxTurns` (counts only tool-use turns) or `max_budget_usd` / `maxBudgetUsd` (stops when cost threshold hit).

### The Context Window

Everything accumulates in the context window across turns within a session:
- System prompt (small, fixed cost)
- CLAUDE.md files (fully loaded, but prompt-cached on first request)
- Tool definitions (each tool adds to context)
- Conversation history (grows with each turn)
- Tool inputs and outputs (can be large for verbose commands)

**Context stays between turns:** Your session doesn't reset. All prior reasoning, file reads, and decisions stay in Claude's context for follow-up questions.

**Automatic compaction:** When context approaches the limit, the SDK summarizes older history to free space. You can guide what gets summarized with a "Summary instructions" section in your CLAUDE.md.

---

## Stop Reasons and Result Handling

The `ResultMessage` tells you why the loop ended. The `subtype` field is your primary signal:

### Result Subtypes

| Subtype | Meaning | What to do |
|---------|---------|-----------|
| `success` | Agent finished normally | Read `result` field for output |
| `error_max_turns` | Hit the `maxTurns` limit | Resume with higher limit or accept partial result |
| `error_max_budget_usd` | Hit the cost limit | Resume with higher budget or accept partial result |
| `error_during_execution` | Unexpected error (API failure, cancelled) | Check logs, retry, or diagnose |
| `error_max_structured_output_retries` | Structured output validation failed | Adjust schema or reduce turns |

### Stop Reason Values

The `stop_reason` field (on both success and error subtypes) tells you why Claude stopped generating on its **final turn**:

| Stop Reason | Meaning |
|------------|---------|
| `end_turn` | Model finished normally (most common) |
| `max_tokens` | Hit output token limit | 
| `tool_use` | (Rare) Final output included tool calls |
| `refusal` | Model declined the request |
| `null` | Unknown or error state |

### Detecting Refusals

```python
if message.subtype == "success" and message.stop_reason == "refusal":
    print("Claude declined the request")
```

### Cost and Usage Tracking

All `ResultMessage` objects include:
- `total_cost_usd` (float, format as `${:.4f}`)
- `usage` (dict with `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`)
- `num_turns` (how many turns the agent took)
- `session_id` (for resuming later)

**Note:** In Python, `total_cost_usd` and `usage` may be `None` on error paths, so guard before using.

### Handling Results

```python
import asyncio
from claude_agent_sdk import query, ResultMessage

async def main():
    async for message in query(prompt="Your task"):
        if isinstance(message, ResultMessage):
            if message.subtype == "success":
                print(f"✓ Done: {message.result}")
            elif message.subtype == "error_max_turns":
                print(f"Hit turn limit. Resume session {message.session_id} to continue")
            elif message.subtype == "error_max_budget_usd":
                print(f"Hit budget. Spent: ${message.total_cost_usd:.4f}")
            else:
                print(f"Stopped: {message.subtype}")

asyncio.run(main())
```

---

## Session Management

### What is a Session?

A **session** is the conversation history that accumulates as your agent works. It contains:
- Your initial prompt
- Every tool call Claude made
- Every tool result
- Every response from Claude
- Metadata (session ID, cost, usage)

Sessions persist to disk automatically (at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`) so you can return to them later. The agent resumes with full context: files it read, analysis it performed, decisions it made.

### Important: Sessions Persist Conversation, Not Filesystem

A session saves the **conversation history**, not file changes. If a forked agent edits files, those changes are real and visible to all sessions in the same directory. To branch and revert file changes, use file checkpointing.

### Capture Session ID

The session ID is available on every `ResultMessage`:

```python
session_id = None
async for message in query(prompt="Analyze auth.py"):
    if isinstance(message, ResultMessage):
        session_id = message.session_id
        if message.subtype == "success":
            print(message.result)
```

In TypeScript, it's also available on the init `SystemMessage`:

```typescript
let sessionId: string | undefined;
for await (const message of query({...})) {
    if (message.type === "system" && message.subtype === "init") {
        sessionId = message.session_id;
    }
}
```

### Resume: Pick Up Where You Left Off

Pass `resume=session_id` to continue an existing session. The agent has full context from before:

```python
async for message in query(
    prompt="Now implement the refactoring you suggested",
    options=ClaudeAgentOptions(
        resume=session_id,
        allowed_tools=["Read", "Edit", "Write", "Glob", "Grep"],
    ),
):
    if isinstance(message, ResultMessage) and message.subtype == "success":
        print(message.result)
```

**Use resume when:**
- Following up on completed analysis without re-reading files
- Recovering from a limit (`error_max_turns`, `error_max_budget_usd`)
- Restarting your process and restoring conversation

**Gotcha:** The session file is stored under `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`, where `<encoded-cwd>` is the absolute working directory with non-alphanumeric characters replaced by `-`. If you resume from a different directory, the SDK looks in the wrong place. The session file also needs to exist on the current machine.

### Fork Session: Explore Alternatives

Forking creates a new session starting with a copy of the original's history but diverging from that point. The fork gets its own session ID; the original stays unchanged.

```python
forked_id = None
async for message in query(
    prompt="Instead of JWT, implement OAuth2 for the auth module",
    options=ClaudeAgentOptions(
        resume=session_id,  # Start from original session's history
        fork_session=True,   # Create a new diverging session
    ),
):
    if isinstance(message, ResultMessage):
        forked_id = message.session_id  # Distinct from original session_id
```

Now you have two session IDs:
- Original `session_id`: continue JWT implementation
- Forked `forked_id`: explore OAuth2 approach

Useful for A/B testing approaches, exploring alternatives, or recovering from mistakes without losing the original thread.

### Python: ClaudeSDKClient for Multi-Turn Conversations

In Python, use `ClaudeSDKClient` for multi-turn conversations within a single process. It tracks the session ID for you:

```python
async with ClaudeSDKClient(options=ClaudeAgentOptions(...)) as client:
    # First query
    await client.query("Analyze the auth module")
    async for message in client.receive_response():
        print(message)
    
    # Second query - automatically continues same session
    await client.query("Now refactor it to use JWT")
    async for message in client.receive_response():
        print(message)
```

Each `query()` call automatically continues the same session. No manual session ID tracking needed.

### TypeScript: Continue Mode

In TypeScript, pass `continue: true` to resume the most recent session:

```typescript
// First query creates a new session
for await (const message of query({ prompt: "Analyze auth.ts" })) {
    // ...
}

// Second query continues the most recent session
for await (const message of query({
    prompt: "Now refactor it to use JWT",
    options: { continue: true }
})) {
    // ...
}
```

### Resuming Across Machines

Session files are local to the machine that created them. To resume on a different host:

1. **Option 1:** Persist the session file (`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`) and restore it on the new machine before calling `resume`. The `cwd` must match.

2. **Option 2:** Don't rely on session resume. Capture the results you need (analysis, decisions, file diffs) as application state and pass them into a fresh session's prompt. Often more robust.

Both SDKs expose functions for enumerating sessions:
- Python: `list_sessions()`, `get_session_messages()`, `get_session_info()`, `rename_session()`, `tag_session()`
- TypeScript: `listSessions()`, `getSessionMessages()`, `getSessionInfo()`, `renameSession()`, `tagSession()`

---

## Subagents: The Coordinator Pattern

### What Are Subagents?

Subagents are separate agent instances that your main agent can spawn to handle focused subtasks. They run in isolated context, don't see the parent's conversation history, and only return their final result to the parent.

**Benefits:**
- **Context isolation:** A research subagent can explore 50 files without bloating the main conversation
- **Parallelization:** Run style checker, security scanner, test runner in parallel
- **Specialized instructions:** Each subagent has tailored system prompt and expertise
- **Tool restrictions:** Subagents can be locked to specific tools

### Critical: What Subagents Do NOT Inherit

Subagents get:
- Their own system prompt
- Project CLAUDE.md (loaded via settingSources)
- Tool definitions (or a subset)
- Their input from the Agent tool

Subagents do NOT get:
- Parent's conversation history or tool results
- Parent's system prompt
- Skills (unless explicitly listed in subagent definition)

**This is the key to context isolation.** The only channel from parent to subagent is the Agent tool's prompt string. Include any context the subagent needs directly in that prompt.

### Defining Subagents

Define subagents programmatically using the `agents` parameter:

#### Python

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    async for message in query(
        prompt="Use the code-reviewer agent to review this codebase",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Agent"],
            agents={
                "code-reviewer": AgentDefinition(
                    description="Expert code reviewer for security and quality",
                    prompt="""You are a code review specialist.
When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify coding standards
Be thorough but concise.""",
                    tools=["Read", "Grep", "Glob"],  # Read-only
                    model="sonnet",  # Optional: override main model
                ),
                "test-runner": AgentDefinition(
                    description="Runs and analyzes test suites",
                    prompt="Execute tests and provide clear analysis of results",
                    tools=["Bash", "Read", "Grep"],
                )
            },
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

#### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
    prompt: "Use the code-reviewer agent to review this codebase",
    options: {
        allowedTools: ["Read", "Grep", "Glob", "Agent"],
        agents: {
            "code-reviewer": {
                description: "Expert code reviewer for security and quality",
                prompt: `You are a code review specialist.
When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify coding standards
Be thorough but concise.`,
                tools: ["Read", "Grep", "Glob"],
                model: "sonnet"
            },
            "test-runner": {
                description: "Runs and analyzes test suites",
                prompt: "Execute tests and provide clear analysis of results",
                tools: ["Bash", "Read", "Grep"]
            }
        }
    }
})) {
    if ("result" in message) console.log(message.result);
}
```

### AgentDefinition Configuration

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `description` | string | Yes | Natural language description of when to use this agent |
| `prompt` | string | Yes | System prompt defining role and behavior |
| `tools` | string[] | No | Allowed tools. If omitted, inherits all tools |
| `disallowedTools` | string[] | No | Tools to block |
| `model` | string | No | Model override: `'sonnet'`, `'opus'`, `'haiku'`, or full ID |
| `skills` | string[] | No | Skill names available to this agent |
| `memory` | 'user' \| 'project' \| 'local' | No | Memory source |
| `mcpServers` | (string \| object)[] | No | MCP servers available |
| `maxTurns` | number | No | Max turns before stopping |
| `background` | boolean | No | Run as non-blocking background task |
| `effort` | 'low' \| 'medium' \| 'high' \| 'xhigh' \| 'max' | No | Reasoning effort level |
| `permissionMode` | PermissionMode | No | Permission mode for this agent |

### How Subagents Are Invoked

**Automatic invocation:** Claude decides when to use subagents based on task and their descriptions.

**Explicit invocation:** Mention in your prompt:
```
"Use the code-reviewer agent to check the authentication module"
```

### Detecting Subagent Invocation

Subagents are invoked via the `Agent` tool. Check for tool calls named `"Agent"` (or `"Task"` in older SDKs):

```python
if hasattr(message, "content"):
    for block in message.content:
        if getattr(block, "type", None) == "tool_use" and block.name in ("Task", "Agent"):
            print(f"Subagent invoked: {block.input.get('subagent_type')}")

# Messages from within subagent context have parent_tool_use_id
if hasattr(message, "parent_tool_use_id") and message.parent_tool_use_id:
    print("(running inside subagent)")
```

### Resuming Subagents

Subagents can be resumed. When a subagent completes, Claude receives its `agentId` in the Agent tool result. To resume:

1. Capture session ID from first query
2. Extract `agentId` from message content
3. Pass `resume: sessionId` and include agent definition in both queries

```python
async def extract_agent_id(text: str) -> str | None:
    import re
    match = re.search(r"agentId:\s*([a-f0-9-]+)", text)
    return match.group(1) if match else None

agent_id = None
session_id = None

# First query: run subagent
async for message in query(
    prompt="Use the Explore agent to find API endpoints",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Grep", "Glob", "Agent"]),
):
    if hasattr(message, "session_id"):
        session_id = message.session_id
    if hasattr(message, "content"):
        content_str = str(message.content)
        extracted = await extract_agent_id(content_str)
        if extracted:
            agent_id = extracted

# Second query: resume subagent
if agent_id and session_id:
    async for message in query(
        prompt=f"Resume agent {agent_id} and list top 3 complex endpoints",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Agent"],
            resume=session_id
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)
```

### Coordinator + Specialist Pattern Example

```python
# Coordinator agent delegates to specialists
async for message in query(
    prompt="Review this PR for security, performance, and test coverage",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Grep", "Glob", "Agent"],
        agents={
            "security-reviewer": AgentDefinition(
                description="Security vulnerability reviewer",
                prompt="Identify all security issues. Focus on authentication, injection, and data leaks.",
                tools=["Read", "Grep", "Glob"],
            ),
            "performance-reviewer": AgentDefinition(
                description="Performance analysis specialist",
                prompt="Check for algorithmic inefficiencies, N+1 queries, memory leaks.",
                tools=["Read", "Grep", "Glob"],
            ),
            "test-coverage-analyzer": AgentDefinition(
                description="Test coverage analyzer",
                prompt="Analyze test coverage. Check for gaps in critical paths.",
                tools=["Read", "Grep", "Glob"],
            ),
        },
    ),
):
    if hasattr(message, "result"):
        print(message.result)
```

Claude automatically runs all three specialists in parallel, then synthesizes findings into a single comprehensive review.

---

## Custom Tools and MCP Servers

### What Are Custom Tools?

Custom tools extend the Agent SDK by letting you define functions Claude can call. They're bundled in MCP (Model Context Protocol) servers that run in-process inside your application.

### Defining Custom Tools

#### Python

```python
from typing import Any
import httpx
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(
    "get_temperature",
    "Get current temperature at a location",
    {"latitude": float, "longitude": float},  # Simple schema
)
async def get_temperature(args: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": args["latitude"],
                "longitude": args["longitude"],
                "current": "temperature_2m",
                "temperature_unit": "fahrenheit",
            },
        )
        data = response.json()
    
    return {
        "content": [
            {
                "type": "text",
                "text": f"Temperature: {data['current']['temperature_2m']}°F",
            }
        ]
    }

weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_temperature],
)
```

#### TypeScript

```typescript
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const getTemperature = tool(
    "get_temperature",
    "Get current temperature at a location",
    {
        latitude: z.number().describe("Latitude coordinate"),
        longitude: z.number().describe("Longitude coordinate"),
    },
    async (args) => {
        const response = await fetch(
            `https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&current=temperature_2m&temperature_unit=fahrenheit`
        );
        const data = await response.json() as any;
        
        return {
            content: [{
                type: "text",
                text: `Temperature: ${data.current.temperature_2m}°F`
            }]
        };
    }
);

const weatherServer = createSdkMcpServer({
    name: "weather",
    version: "1.0.0",
    tools: [getTemperature]
});
```

### Tool Definition Structure

Each tool requires:

1. **Name:** Unique identifier Claude uses to call it
2. **Description:** What it does (Claude reads this to decide when to call)
3. **Input schema:** Arguments Claude provides
4. **Handler:** Async function that runs when called

#### Input Schemas

**Python (simple):**
```python
{"latitude": float, "longitude": float, "unit": str}
```

**Python (complex, with enums/optionals):**
```python
{
    "type": "object",
    "properties": {
        "unit_type": {
            "type": "string",
            "enum": ["length", "temperature", "weight"],
        },
        "from_unit": {"type": "string"},
        "to_unit": {"type": "string"},
        "value": {"type": "number"},
    },
    "required": ["unit_type", "from_unit", "to_unit", "value"],
}
```

**TypeScript (Zod):**
```typescript
{
    latitude: z.number().describe("Latitude coordinate"),
    longitude: z.number().describe("Longitude coordinate"),
    hours: z.number().int().min(1).max(24).default(12).describe("Hours to forecast")
}
```

### Tool Descriptions Best Practices

Clear descriptions help Claude decide when to call your tool:

**Bad:**
```
"Get data"
```

**Good:**
```
"Get the current temperature at a specific latitude/longitude. Returns temperature in Fahrenheit."
```

**Best:**
```
"Get the current temperature at a specific latitude/longitude in Fahrenheit. Use this when the user asks about current weather conditions or temperature at a location."
```

### Handler Return Format

All handlers return this structure:

```python
{
    "content": [
        {
            "type": "text",  # or "image" or "resource"
            "text": "Result text",  # for text blocks
        }
    ],
    "is_error": False,  # Optional: True if tool failed
}
```

### Tool Annotations

Optional metadata about tool behavior:

```python
from claude_agent_sdk import ToolAnnotations

@tool(
    "search_index",
    "Search the product index",
    {"query": str},
    annotations=ToolAnnotations(
        readOnlyHint=True,  # Tool doesn't modify anything
        idempotentHint=True,  # Same input = same output
        openWorldHint=False,  # Doesn't reach external systems
    )
)
async def search_index(args):
    # ...
```

| Annotation | Effect |
|------------|--------|
| `readOnlyHint: True` | Can run in parallel with other read-only tools |
| `idempotentHint: True` | Repeated calls have no additional effect |
| `destructiveHint: False` | Tool doesn't modify its environment (informational) |
| `openWorldHint: False` | Tool stays within your app (informational) |

### Error Handling in Tools

**Bad:** Let exceptions bubble up
```python
response = client.get("https://broken.url")  # Throws on error
result = response.json()  # Might throw
```
This stops the entire agent loop.

**Good:** Return `is_error: True` so Claude can handle it
```python
try:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        if response.status_code != 200:
            return {
                "content": [{
                    "type": "text",
                    "text": f"API error: {response.status_code}"
                }],
                "is_error": True,
            }
        data = response.json()
        return {"content": [{"type": "text", "text": json.dumps(data)}]}
except Exception as e:
    return {
        "content": [{"type": "text", "text": f"Failed: {str(e)}"}],
        "is_error": True,
    }
```

Claude sees the error and can retry, try a different tool, or explain to the user.

### Structured Error Responses

The `isError` pattern is the standard for tool failures in the Agent SDK. Return it as `"is_error": True` (Python) or `isError: true` (TypeScript):

```python
# When API returns 404
if response.status_code == 404:
    return {
        "content": [{
            "type": "text",
            "text": "User not found"
        }],
        "is_error": True,  # Structured error response
    }
```

This signals to Claude that the tool call failed but the loop should continue. Claude will typically:
- Log the error
- Try a different approach
- Ask for clarification
- Report the error to the user

### Using Custom Tools

Pass the server to `query()`:

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    async for message in query(
        prompt="What's the temperature in San Francisco?",
        options=ClaudeAgentOptions(
            mcp_servers={"weather": weather_server},
            allowed_tools=["mcp__weather__get_temperature"],  # Fully qualified name
        ),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(main())
```

### Tool Naming Convention

When MCP tools are exposed to Claude, they follow this format:

```
mcp__{server_name}__{tool_name}
```

Example: Tool `get_temperature` in server `weather` becomes `mcp__weather__get_temperature`

Use in `allowed_tools`:
```python
allowed_tools=["mcp__weather__get_temperature"]
# Or use wildcard:
allowed_tools=["mcp__weather__*"]  # All tools from weather server
```

### Multiple Tools in One Server

```python
@tool("get_temp", "Get temperature", {"lat": float, "lon": float})
async def get_temp(args):
    # ...

@tool("get_precip", "Get precipitation", {"lat": float, "lon": float})
async def get_precip(args):
    # ...

weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_temp, get_precip],  # Both tools in one server
)
```

### Returning Images and Resources

Tools can return more than text:

**Image blocks:**
```python
import base64

return {
    "content": [{
        "type": "image",
        "data": base64.b64encode(image_bytes).decode("ascii"),  # Base64 only, no prefix
        "mimeType": "image/png",  # Required
    }]
}
```

**Resource blocks:**
```python
return {
    "content": [{
        "type": "resource",
        "resource": {
            "uri": "file:///tmp/report.md",  # Label for Claude
            "mimeType": "text/markdown",
            "text": "# Report\n...",  # Actual content inline
        }
    }]
}
```

---

## Permissions and Hooks

### Permission System Overview

When Claude requests a tool, the SDK evaluates permissions in this order:

```
1. Run PreToolUse hooks (can allow/deny/continue)
   ↓
2. Check deny rules (disallowed_tools) → BLOCK if matched
   ↓
3. Apply permission mode
   - bypassPermissions → ALLOW
   - Other modes → continue
   ↓
4. Check allow rules (allowed_tools) → ALLOW if matched
   ↓
5. Call canUseTool callback (if not in dontAsk mode)
   ↓
6. Default: DENY
```

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Unmatched tools trigger `canUseTool` callback |
| `dontAsk` | Unmatched tools are denied without prompting |
| `acceptEdits` | Auto-approves file operations (Edit, Write, mkdir, rm, etc.) |
| `plan` | No tool execution; Claude plans only |
| `bypassPermissions` | All tools approved (use carefully!) |
| `auto` | Model classifier approves/denies (TypeScript only) |

### Configuring Permissions

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Grep"],  # Auto-approved
    disallowed_tools=["Bash"],  # Always blocked
    permission_mode="dontAsk",  # Deny if not pre-approved
)
```

### Allow and Deny Rules

**`allowed_tools`** lists tools that run without permission prompts:

```python
allowed_tools=["Read", "Glob", "Grep"]  # Auto-approved
```

**`disallowed_tools`** blocks specific tools, even in `bypassPermissions`:

```python
disallowed_tools=["Bash"]  # Always blocked
```

**With `bypassPermissions`:** `allowed_tools` does NOT constrain it. Every unlisted tool still runs because the permission mode allows it. To block specific tools with `bypassPermissions`, use `disallowed_tools`.

### Dynamic Permission Mode

Change permissions mid-session:

```python
q = query(
    prompt="Help me refactor this code",
    options=ClaudeAgentOptions(permission_mode="default"),
)

# After reviewing Claude's plan, enable edits
await q.set_permission_mode("acceptEdits")

async for message in q:
    print(message)
```

### Pre-Tool Hooks (PreToolUse)

Runs before a tool executes. Can allow, deny, or modify the tool call:

#### Python

```python
async def validate_bash_command(input_data, tool_use_id, context):
    """Block dangerous Bash commands."""
    command = input_data.get("tool_input", {}).get("command", "")
    
    if "rm -rf" in command or "sudo" in command:
        return {"hookSpecificOutput": {"permissionDecision": "deny"}}
    
    return {"hookSpecificOutput": {"permissionDecision": "allow"}}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[validate_bash_command])
        ]
    }
)
```

#### TypeScript

```typescript
const validateBashCommand: HookCallback = async (input, toolUseID, context) => {
    const command = (input as any).tool_input?.command ?? "";
    
    if (command.includes("rm -rf") || command.includes("sudo")) {
        return {
            hookSpecificOutput: { permissionDecision: "deny" }
        };
    }
    
    return {
        hookSpecificOutput: { permissionDecision: "allow" }
    };
};

const options = {
    hooks: {
        PreToolUse: [{
            matcher: "Bash",
            hooks: [validateBashCommand]
        }]
    }
};
```

### Post-Tool Hooks (PostToolUse)

Runs after a tool completes. Common uses: audit logging, side effects, data extraction:

#### Python

```python
from datetime import datetime

async def audit_file_changes(input_data, tool_use_id, context):
    """Log all file modifications."""
    tool_name = input_data.get("tool_name", "")
    if tool_name in ("Edit", "Write"):
        file_path = input_data.get("tool_input", {}).get("file_path", "unknown")
        with open("audit.log", "a") as f:
            f.write(f"{datetime.now().isoformat()}: {tool_name} {file_path}\n")
    
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PostToolUse": [
            HookMatcher(matcher="Edit|Write", hooks=[audit_file_changes])
        ]
    }
)
```

### Approval Patterns

#### Interactive Approval via canUseTool

Use `canUseTool` callback for runtime approval decisions:

```python
async def require_approval(tool_name: str, tool_input: dict) -> bool:
    """Ask user for approval."""
    print(f"\nTool: {tool_name}")
    print(f"Input: {tool_input}")
    response = input("Approve? (y/n): ")
    return response.lower() == "y"

options = ClaudeAgentOptions(
    permission_mode="default",
    can_use_tool=require_approval,
)
```

#### Escalation Pattern

Approve some tools, escalate others:

```python
async def selective_approval(tool_name: str, tool_input: dict) -> bool:
    """Auto-approve read-only, escalate dangerous."""
    if tool_name in ("Read", "Glob", "Grep"):
        return True  # Auto-approve
    
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if any(bad in command for bad in ["rm", "sudo", "kill"]):
            # Escalate to user
            print(f"ESCALATION: Bash command requested: {command}")
            return input("Approve? (y/n): ").lower() == "y"
    
    return False  # Default deny
```

---

## Advanced Patterns and Examples

### Example 1: Bug-Fixing Agent with Cost Limits

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def fix_bugs():
    session_id = None
    
    async for message in query(
        prompt="Find and fix the bug causing test failures in auth.py. Run tests to verify.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"],
            max_turns=30,  # Prevent runaway
            max_budget_usd=1.00,  # Stop if costs exceed $1
            effort="high",  # Use thorough reasoning for debugging
        ),
    ):
        if isinstance(message, ResultMessage):
            session_id = message.session_id
            
            if message.subtype == "success":
                print(f"✓ Fixed: {message.result}")
            elif message.subtype == "error_max_turns":
                print(f"Ran out of turns. Resume: {session_id}")
            elif message.subtype == "error_max_budget_usd":
                print(f"Budget exceeded: ${message.total_cost_usd:.4f}")
            
            if message.total_cost_usd:
                print(f"Total cost: ${message.total_cost_usd:.4f}")
                print(f"Turns taken: {message.num_turns}")

asyncio.run(fix_bugs())
```

### Example 2: Coordinator + Specialist Subagents for Code Review

```python
import asyncio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    ResultMessage,
)

async def review_pr():
    async for message in query(
        prompt="""Review this PR for:
1. Security vulnerabilities
2. Performance issues
3. Test coverage gaps

Use the specialist agents to investigate in parallel.""",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Agent"],
            setting_sources=["project"],  # Load CLAUDE.md
            agents={
                "security-reviewer": AgentDefinition(
                    description="Security specialist",
                    prompt="""You are a security auditor. Find vulnerabilities in:
- Authentication and authorization
- Input validation
- Cryptography
- API security
Focus on OWASP Top 10 issues.""",
                    tools=["Read", "Grep", "Glob"],
                ),
                "performance-reviewer": AgentDefinition(
                    description="Performance optimizer",
                    prompt="""Analyze performance. Check for:
- Algorithmic inefficiencies (O(n²) loops)
- N+1 query patterns
- Memory leaks
- Unnecessary allocations""",
                    tools=["Read", "Grep", "Glob"],
                ),
                "test-coverage-analyzer": AgentDefinition(
                    description="Test coverage analyst",
                    prompt="""Analyze test coverage. Report:
- Critical paths with no tests
- Percentage coverage by module
- Missing edge case tests""",
                    tools=["Read", "Grep", "Glob"],
                ),
            },
        ),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(review_pr())
```

### Example 3: Custom Tool with Error Handling

```python
import asyncio
import json
from typing import Any
import httpx
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions, ResultMessage

@tool(
    "fetch_user_data",
    "Fetch user information from API. Returns user data or error.",
    {"user_id": str},
)
async def fetch_user_data(args: dict[str, Any]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.example.com/users/{args['user_id']}",
                timeout=10.0,
            )
        
        # Handle non-200 responses
        if response.status_code == 404:
            return {
                "content": [{
                    "type": "text",
                    "text": f"User {args['user_id']} not found",
                }],
                "is_error": True,  # Structured error
            }
        
        if response.status_code != 200:
            return {
                "content": [{
                    "type": "text",
                    "text": f"API error {response.status_code}: {response.text}",
                }],
                "is_error": True,
            }
        
        user = response.json()
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(user, indent=2),
            }]
        }
    
    except httpx.TimeoutException:
        return {
            "content": [{
                "type": "text",
                "text": "Request timeout after 10 seconds",
            }],
            "is_error": True,
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to fetch user: {str(e)}",
            }],
            "is_error": True,
        }

api_server = create_sdk_mcp_server(
    name="api",
    version="1.0.0",
    tools=[fetch_user_data],
)

async def main():
    async for message in query(
        prompt="Fetch user 12345 and summarize their account",
        options=ClaudeAgentOptions(
            mcp_servers={"api": api_server},
            allowed_tools=["mcp__api__fetch_user_data"],
        ),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(main())
```

### Example 4: Fork Session to Explore Alternatives

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def explore_alternatives():
    session_id = None
    
    # First query: analyze architecture
    async for message in query(
        prompt="Analyze the architecture of this Python project and suggest improvements",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
        ),
    ):
        if isinstance(message, ResultMessage):
            session_id = message.session_id
            if message.subtype == "success":
                print("Architecture Analysis:")
                print(message.result)
    
    # Fork: explore refactoring approach A
    fork_a_id = None
    print("\n--- Approach A: Microservices ---")
    async for message in query(
        prompt="Create a detailed refactoring plan using microservices architecture",
        options=ClaudeAgentOptions(
            resume=session_id,
            fork_session=True,
            allowed_tools=["Read", "Glob", "Grep"],
        ),
    ):
        if isinstance(message, ResultMessage):
            fork_a_id = message.session_id
            if message.subtype == "success":
                print(message.result)
    
    # Fork again from original: explore refactoring approach B
    fork_b_id = None
    print("\n--- Approach B: Monolith with Modular Design ---")
    async for message in query(
        prompt="Create a refactoring plan that keeps the monolith but improves modularity",
        options=ClaudeAgentOptions(
            resume=session_id,  # Fork from original, not from fork_a
            fork_session=True,
            allowed_tools=["Read", "Glob", "Grep"],
        ),
    ):
        if isinstance(message, ResultMessage):
            fork_b_id = message.session_id
            if message.subtype == "success":
                print(message.result)
    
    print(f"\nSessions created:")
    print(f"  Original: {session_id}")
    print(f"  Approach A: {fork_a_id}")
    print(f"  Approach B: {fork_b_id}")

asyncio.run(explore_alternatives())
```

### Example 5: Resume and Recover from Limits

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def recover_from_limit():
    session_id = None
    
    # First attempt with low limit
    async for message in query(
        prompt="Refactor the entire payment module for testability",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Write", "Glob", "Grep"],
            max_turns=5,  # Deliberately low
        ),
    ):
        if isinstance(message, ResultMessage):
            session_id = message.session_id
            
            if message.subtype == "success":
                print(f"✓ Done: {message.result}")
                return
            elif message.subtype == "error_max_turns":
                print(f"Hit turn limit. Resuming with higher limit...\n")
    
    # Resume with higher limit
    async for message in query(
        prompt="Continue refactoring the payment module",
        options=ClaudeAgentOptions(
            resume=session_id,
            allowed_tools=["Read", "Edit", "Write", "Glob", "Grep"],
            max_turns=20,  # Higher limit
        ),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(f"✓ Completed: {message.result}")

asyncio.run(recover_from_limit())
```

### Example 6: Read-Only Agent with Approval Callback

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def require_approval(tool_name: str, tool_input: dict) -> bool:
    """Require user approval for any tool."""
    print(f"\n⚠️  Tool request: {tool_name}")
    print(f"   Input: {tool_input}")
    
    response = input("Approve? (y/n): ").strip().lower()
    return response == "y"

async def code_reviewer():
    async for message in query(
        prompt="Review this codebase for bugs and suggest fixes (don't make changes)",
        options=ClaudeAgentOptions(
            permission_mode="plan",  # No execution, plans only
            allowed_tools=["Read", "Glob", "Grep"],
        ),
    ):
        if isinstance(message, ResultMessage):
            if message.subtype == "success":
                print(f"Review Plan:\n{message.result}")

asyncio.run(code_reviewer())
```

---

## Complete Reference

### Python Quick Reference

**Installation:**
```bash
pip install claude-agent-sdk
```

**Two main APIs:**

1. **`query()`** - One-off interactions
```python
async for message in query(
    prompt="Your task",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Bash"],
        max_turns=10,
    )
):
    print(message)
```

2. **`ClaudeSDKClient`** - Multi-turn conversations
```python
async with ClaudeSDKClient(options=...) as client:
    await client.query("First question")
    async for msg in client.receive_response():
        print(msg)
    
    await client.query("Follow-up")
    async for msg in client.receive_response():
        print(msg)
```

**Session management:**
- `query(prompt=..., options=ClaudeAgentOptions(resume=session_id))`
- `fork_session=True` to branch
- Capture `session_id` from `ResultMessage`

**Message types:**
- `SystemMessage` - init, compact_boundary
- `AssistantMessage` - Claude's responses with tool calls
- `UserMessage` - Tool results fed back
- `ResultMessage` - Final result
- `StreamEvent` - Partial messages (if enabled)

### TypeScript Quick Reference

**Installation:**
```bash
npm install @anthropic-ai/claude-agent-sdk
```

**Main API:**
```typescript
for await (const message of query({
    prompt: "Your task",
    options: {
        allowedTools: ["Read", "Bash"],
        maxTurns: 10,
    }
})) {
    console.log(message);
}
```

**Session management:**
- `resume: sessionId` to continue
- `forkSession: true` to branch
- `continue: true` to resume most recent
- Capture `session_id` from result message

**Message types:**
- Check `.type` field: `"system"`, `"assistant"`, `"user"`, `"result"`, etc.
- Content blocks in `.message.content` for assistant/user messages

---

## Summary

The Claude Agent SDK provides a production-grade way to build autonomous AI agents that can read files, run commands, edit code, execute custom tools, and coordinate with specialized subagents. It abstracts away the tool-use loop implementation, provides built-in tools and hooks, manages sessions and context intelligently, and gives you fine-grained control over permissions and costs.

Key architectural concepts:
1. **Agent loop:** Claude evaluates, calls tools, gets results, repeats
2. **Sessions:** Persistent conversation history that can be resumed or forked
3. **Subagents:** Isolated specialists that don't see parent context
4. **Custom tools:** Your own functions wrapped in MCP servers
5. **Hooks:** Intercept and control tool calls
6. **Permissions:** Allow, deny, or require approval for tools

For production deployments, use:
- API key authentication via `ANTHROPIC_API_KEY`
- Allow/deny rules in `allowed_tools` and `disallowed_tools`
- Permission modes appropriate to your use case
- Cost limits (`max_budget_usd`) and turn limits (`max_turns`)
- Subagents to isolate work and reduce main context
- Hooks for auditing and validation
- Session IDs to enable resumption and recovery

This guide covers everything needed to build sophisticated autonomous agents for CI/CD, code review, refactoring, research, and custom domain-specific automation.

