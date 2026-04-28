# Coding Conventions — IntakeAI

## Python Style
- Type hints on every function signature
- Pydantic v2 for all data crossing agent boundaries
- No bare `except:` — catch specific exceptions
- No comments unless the WHY is non-obvious (hidden constraint, hook invariant, SDK quirk)
- 100 char line limit · ruff enforces style · mypy enforces types

## Naming

| Concept | Convention | Example |
|---|---|---|
| Tool functions | verb-first snake_case | `lookup_ticket`, `create_ticket` |
| MCP tool names | `mcp__{server}__{action}` | `mcp__helpdesk__lookup_ticket` |
| Schema classes | PascalCase + domain suffix | `TriageResult`, `SpecialistResult` |
| Constants | UPPER_SNAKE_CASE | `MAX_VALIDATION_RETRIES = 3` |

## Async
All agent calls use `async/await`. `asyncio.run()` only in `__main__` blocks.

## Imports
```python
# stdlib → third-party → local
import asyncio
from claude_agent_sdk import query
from src.schemas.request import NormalizedRequest
```

## Commit Format
`<type>(<scope>): <short description>`

| Type | When |
|---|---|
| `feat` | New capability (tool, specialist, eval case) |
| `fix` | Bug in agent logic, tool, or hook |
| `arch` | Architecture decision or structural change |
| `eval` | Eval dataset or harness |
| `docs` | CLAUDE.md, ADRs, README |
| `test` | Unit tests |
| `chore` | Deps, config, tooling |

## Plan Mode Policy
Use **Plan Mode** (shift+tab) before: adding/splitting a specialist, changing escalation thresholds, any hook change, coordinator routing logic.
Direct execution for: eval cases, tool descriptions, type fixes, unit tests.

## CLAUDE.md Hierarchy
- `CLAUDE.md` (this repo root) — shared, in VCS, minimal
- `docs/context/*.md` — detail docs, read on demand
- `src/specialists/CLAUDE.md` — (optional) specialist-specific additions only
