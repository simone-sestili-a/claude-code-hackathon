# IntakeAI — Claude Code Brief
**Scenario 5: Agentic IT Helpdesk Triage (Claude Agent SDK required)**

## Mission
Replace hand-triage of ~200 IT helpdesk requests/day. The agent classifies, enriches, routes, and acts — it does not chat.
Stack: Python 3.12 · Claude Agent SDK · FastMCP · Pydantic v2
Models: `claude-opus-4-7` (coordinator) · `claude-sonnet-4-6` (specialists)

## Hard Constraints — Never Cross These
- Use Claude Agent SDK, not the raw Anthropic client SDK
- No external emails sent — generate drafts only, humans send
- No actions on accounts with status `FROZEN` (hook enforces this)
- No auto-close on P1 or SECURITY category tickets
- `ANTHROPIC_API_KEY` is the only required secret

## How to Verify Your Work
```bash
make type-check          # run first — fast
make test                # unit tests
python -m src.coordinator.agent --request '{"channel":"email","body":"VPN down","user_id":"u001"}' --dry-run
make eval                # run before marking any challenge complete
```
If you cannot run `make test`, say so — do not claim the change works.

## Key Decisions (read before architecting anything)
- Task subagents do **not** inherit coordinator context — always pass context explicitly
- Hook = deterministic hard stop · Prompt = probabilistic preference (never mix)
- Validation-retry loop lives in the coordinator only (max 3 retries, log each)
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
