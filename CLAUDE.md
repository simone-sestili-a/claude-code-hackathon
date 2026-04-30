# DocumentAI — Claude Code Brief
**AI Ticket Management System — pipeline multi-agente per l'elaborazione automatizzata di ticket con allegati PDF**

## Mission
Automatizzare l'elaborazione di ticket di fondi pensione italiani contenenti allegati PDF multipagina. Il sistema classifica l'intento, estrae dati strutturati da ogni pagina in parallelo, rileva e separa le sub-richieste distinte, e restituisce un report strutturato.
Stack: Python 3.12 · Claude Agent SDK · FastAPI · uv · Pydantic v2
Models: `claude-haiku-4-5-20251001` (coordinator/classifier) · `claude-sonnet-4-6` (specialists)

## Hard Constraints — Never Cross These
- Use Claude Agent SDK, not the raw Anthropic client SDK
- Never add a new flow without registering it in `src/flows/__init__.py`
- Never return unvalidated Pydantic models as API responses
- `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` (LiteLLM proxy) is the only required secret

## How to Verify Your Work
```bash
uv run pytest tests/ -v                          # run first — unit tests
uv run mypy src/ --ignore-missing-imports        # type check
uv run ruff check src/ tests/                    # lint
uv run uvicorn src.api:app --reload --port 8000  # start API — docs at /docs
```
If you cannot run `uv run pytest`, say so — do not claim the change works.

## Key Decisions (read before architecting anything)
- Task subagents do **not** inherit coordinator context — always pass context explicitly
- Hook = deterministic hard stop · Prompt = probabilistic preference (never mix)
- Flows are pluggable: add a new flow in `src/flows/<name>/` without touching coordinator, API, or session store
- Every decision must be replayable from the audit log alone

## Learned Rules
> When Claude does something wrong, the fix goes here. End corrections with: *"Update CLAUDE.md so you don't make that mistake again."*

_(empty — grows as the team works)_

## Go Deeper — Read Only What You Need
| Topic | Context doc |
|---|---|
| Architecture, agent loop, subagent prompts | `docs/context/architecture.md` |
| Tool design, MCP, error codes | `docs/context/tools.md` |
| Hooks (PreToolUse / PostToolUse patterns) | `docs/context/hooks.md` |
| Escalation matrix, impact buckets | `docs/context/escalation.md` |
| Eval harness, metrics, CI thresholds | `docs/context/evaluation.md` |
| Commands, setup, environment | `docs/context/commands.md` |
| Coding conventions, naming, commits | `docs/context/conventions.md` |
| What NOT to automate (legal scope) | `docs/context/scope-boundaries.md` |

## Before Responding — Check Docs

After every change, before replying, ask: *did this affect anything documented in `docs/context/`?*

If yes: update only the affected lines in the relevant file — surgical edits, not rewrites.

| If you changed… | Check |
|---|---|
| Agent loop, subagent template, routing logic | `docs/context/architecture.md` |
| Tool definitions, MCP tools, error codes | `docs/context/tools.md` |
| Hook patterns, block rules, permission modes | `docs/context/hooks.md` |
| Escalation thresholds, impact buckets | `docs/context/escalation.md` |
| Eval metrics, datasets, CI thresholds | `docs/context/evaluation.md` |
| Make targets, commands, setup steps | `docs/context/commands.md` |
| Naming, conventions, commit format, plan mode policy | `docs/context/conventions.md` |
| Scope exclusions, TODO placeholders | `docs/context/scope-boundaries.md` |

If nothing changed in those areas, skip this step — don't update docs for the sake of it.
