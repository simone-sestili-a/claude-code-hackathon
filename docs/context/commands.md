# Commands & Setup — IntakeAI

## Prerequisites
- Python 3.12+
- `ANTHROPIC_API_KEY` in environment (only required secret)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then set ANTHROPIC_API_KEY
```

## Common Commands

```bash
make setup              # install dependencies
make run                # demo mode — simulate multi-channel intake
make test               # pytest suite
make type-check         # mypy
make lint               # ruff
make eval               # full eval (normal + adversarial + boundary)
make eval-adversarial   # adversarial subset only
make mcp-server         # start FastMCP server standalone
make clean              # remove build artifacts
```

## Single Request Smoke Test

```bash
python -m src.coordinator.agent \
  --request '{"channel":"email","body":"Cannot login to VPN","user_id":"u001"}' \
  --dry-run
```

## MCP Server + Agent

```bash
python -m src.mcp_server.server &
python -m src.coordinator.agent --mcp --request-file examples/sample_request.json
```

## Non-Interactive CI Mode

```bash
claude --no-interactive \
  --tools "Read,Bash" \
  --disallow-tools "Write,Edit" \
  -p "Run the eval harness and report results" \
  --output-format json
```
