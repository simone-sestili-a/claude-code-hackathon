---
name: agentic-system-builder
description: Generate a complete, production-ready agentic system using the Claude Agent SDK (Python) with a FastAPI REST layer, tailored to the user's project. Use this skill whenever the user wants to build an AI agent, agentic workflow, Claude-powered backend, autonomous assistant, or any system with orchestration/subagents. Trigger on: "build an agent", "create an agentic system", "I need an agent that", "Claude Agent SDK project", "agentic IT helpdesk", "autonomous workflow", or any description of a multi-step AI system. Always use this skill instead of writing agent code from scratch.
---

# Agent Builder

Generates a complete Claude Agent SDK + FastAPI project from a short description.

---

## Phase 1 — Interview the User

Before writing any code, ask these questions in a single block (don't ask one at a time):

1. **Project name** — what do you want to call this agent?
2. **Domain / purpose** — one paragraph: what does the agent do? What problems does it solve?
3. **Input type** — what does the user or system send to the agent? (free text, JSON, form data, file, etc.)
4. **Output type** — what does the agent return? (structured JSON, natural language, action confirmation, etc.)
5. **Specialist subagents needed?** — are there distinct sub-tasks that should run as isolated specialists (e.g., classify + enrich + route)?
6. **Custom tools needed?** — does the agent need domain-specific tools beyond standard file/bash/web? (e.g., search a CRM, query a database, call an external API)
7. **Hard constraints** — what should the agent never do? (send emails autonomously, write to production DB without confirmation, etc.)
8. **Validation / human-in-the-loop** — any decisions that require human confirmation before execution?

Summarize the answers, confirm with the user, then generate.

---

## Phase 2 — Generate the Project

### File Structure to Generate

```
{project_name}/
├── CLAUDE.md                         # Agent context + rules
├── pyproject.toml                    # hatchling build backend
├── Makefile                          # setup, test, type-check, run
├── .env.example                      # ANTHROPIC_API_KEY placeholder
├── src/
│   ├── __init__.py
│   ├── agent.py                      # Core agent: send_query() + send_query_simple()
│   ├── api.py                        # FastAPI app (wraps agent.py)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── request.py                # Pydantic v2 input models
│   │   └── response.py               # Pydantic v2 output models
│   ├── tools/                        # Custom @tool functions (if needed)
│   │   └── __init__.py
│   ├── specialists/                  # AgentDefinition subagents (if needed)
│   │   └── __init__.py
│   └── hooks/
│       ├── __init__.py
│       └── pre_tool_use.py           # Hard-stop PreToolUse hook
└── tests/
    ├── test_schemas.py
    └── test_hooks.py
```

Generate every file — no placeholders, no TODOs, no empty shells. Every file must be functional.

---

## Phase 3 — Generation Rules

### Agent Core (`src/agent.py`)

Use the **`ClaudeSDKClient` pattern** for the coordinator (multi-turn capable). Use the **`query()` pattern** for one-shot specialist calls.

See `references/sdk-patterns.md` for exact import and usage patterns.

Key rules:
- Import from `claude_code_sdk` (the boilerplate uses this package name)
- Always use `async with ClaudeSDKClient(options=options) as agent:` — never instantiate without context manager
- Add `asyncio.timeout(30)` wrapper to prevent disconnect hangs
- Always include `"Task"` in `allowed_tools` when the coordinator must delegate to subagents
- Use `tools=` (not `allowed_tools=`) to restrict which tools an agent may invoke
- Use snake_case for all options: `permission_mode`, `max_turns`, `system_prompt`, `allowed_tools`
- For PreToolUse permission enforcement, use `HookMatcher` — never use `can_use_tool` (it never fires)
- Don't break out of `query()` generator early — let it exhaust naturally to avoid event loop poisoning

### Coordinator System Prompt

Write a tight, tool-first system prompt that:
- States the agent's role and domain in one sentence
- Lists what the agent must ALWAYS do (tool-first, structured output, route to specialists)
- Lists what the agent must NEVER do (derived from user's hard constraints)
- Names the available specialists (if any)

### Subagents (`src/specialists/`)

For each specialist:
```python
AgentDefinition(
    description="One sentence: what this specialist does",
    prompt="Full specialist system prompt. Context must be passed explicitly — specialists don't inherit coordinator state.",
    tools=["Read", "Grep"],          # tools= restricts availability
    model="claude-sonnet-4-6",
)
```

Pass subagent definitions via `agents={"name": AgentDefinition(...)}` in coordinator options.

### Custom Tools (`src/tools/`)

```python
from claude_code_sdk import tool
from typing import Annotated, Any

@tool("tool_name", "Short description", {
    "param": Annotated[str, "Parameter description"],
})
async def tool_name(args: dict[str, Any]) -> dict[str, Any]:
    # ... logic ...
    return {"content": [{"type": "text", "text": result}]}
```

Wrap in `create_sdk_mcp_server()` and pass as `mcp_servers={"server_name": server}` in options.

### FastAPI Layer (`src/api.py`)

See `references/fastapi-template.md` for the full template. Always include:
- `GET /` — health check
- `POST /query` — full query with `QueryRequest` / `QueryResponse` Pydantic models
- `POST /query/simple` — returns `{"result": str}` only
- `GET /styles` — list available output styles
- CORS middleware with `allow_origins=["*"]` (document that production should restrict this)

### Hard Stops (`src/hooks/pre_tool_use.py`)

Generate a `_check()` function that implements every constraint from the user's "never do" list as deterministic regex/condition checks. The hook must:
- Read `sys.stdin` as JSON
- Return `{"decision": "block", "reason": "CODE", "message": "..."}` and `sys.exit(0)` to block
- `sys.exit(0)` with no output to allow

### CLAUDE.md

Write a minimal CLAUDE.md (≤70 lines) following progressive disclosure:
- Mission (2-3 sentences)
- Hard Constraints (bullet list of never-do items)
- How to Verify (`make type-check && make test`, `--dry-run` smoke test)
- Key Decisions (3-5 architectural decisions that future Claude must know)
- Pointer table to `docs/context/` for deep dives (architecture, tools, hooks)

Do NOT put detailed architecture in CLAUDE.md — it's read on every call.

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "claude-code-sdk>=0.0.14",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23", "mypy>=1.9", "ruff>=0.4"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Makefile

```makefile
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip

.PHONY: setup test type-check run

setup:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev]" -q

test:
	$(VENV)/bin/pytest tests/ -v

type-check:
	$(VENV)/bin/mypy src/ --ignore-missing-imports

run:
	$(PYTHON) -m uvicorn src.api:app --reload --port 8000
```

---

## Phase 4 — Verify Before Handing Off

After generating all files:
1. Run `make type-check` — fix any type errors before reporting done
2. Run `make test` — fix failing tests before reporting done
3. Smoke test: `python -c "import src.agent; print('OK')"` to verify imports resolve
4. Report: list every generated file, note any TODO items that require the user's domain-specific values (API keys, DB connection strings, business rules)

If tests or type-check cannot run (missing dependencies), say so explicitly — do not claim success.

---

## References

- `references/sdk-patterns.md` — exact import and usage patterns for `query()`, `ClaudeSDKClient`, `AgentDefinition`, `@tool`, `HookMatcher`
- `references/fastapi-template.md` — full FastAPI template with all four endpoints
- `references/anti-patterns.md` — common SDK mistakes and their corrections
