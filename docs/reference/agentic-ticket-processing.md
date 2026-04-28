# Agentic Ticket Processing — Implementation Guide

> Reference pattern for building agentic document-processing workflows with the Claude Agent SDK.
> Describes a system that processes ticket PDFs, extracts structured subrequests, validates them with a human, and persists the results.

---

## What This System Does

**Input:** Ticket PDF  
**Output:** Structured, human-validated subrequests persisted to a data store

**Core principles:**
- Agent = iterative loop (observe → plan → act → evaluate)
- Tool-first architecture — no guessing, only tool calls
- Stateless, parallelizable sub-tasks
- Human-in-the-loop validation before any write
- Structured outputs (JSON) at every boundary

---

## Architecture

### Processing Flow

```
Orchestrator Agent
  │
  ├─ split_pdf_tool           → list of pages
  ├─ extract_page_tool × N    → page summaries (parallel)
  ├─ detect_subrequests_tool  → list of subrequests
  ├─ validation_tool          → human confirms each subrequest (HITL)
  └─ persist_tool             → write confirmed subrequests
```

### Orchestrator Loop (pseudo-code)

```python
while True:
    context = gather_context()
    plan = model("What should I do next?")

    if plan == "split_pdf":
        pages = split_pdf(file)
    elif plan == "extract_pages":
        summaries = parallel_map(extract_page, pages)
    elif plan == "detect_requests":
        requests = detect_subrequests(summaries, rules)
    elif plan == "validate":
        for r in requests:
            if validate_request(r):
                persist(r)
    elif plan == "done":
        break
```

---

## Tools

### `split_pdf_tool`

```python
def split_pdf(file_path: str) -> List[Page]:
```

**Output:** list of pages

---

### `extract_page_tool`

```python
def extract_page(page: str) -> dict:
```

**Output:**
```json
{
  "header": "string",
  "entities": ["list", "of", "strings"],
  "summary": "string"
}
```

---

### `detect_subrequests_tool`

```python
def detect_subrequests(page_summaries: list, rules: str) -> list:
```

**Output:**
```json
[
  {
    "request_id": "R1",
    "pages": [1, 2],
    "description": "...",
    "data": {}
  }
]
```

---

### `validation_tool`

```python
def validate_request(request: dict) -> bool:
```

Human-in-the-loop gate. Returns `True` only on explicit human confirmation.

---

### `persist_tool`

```python
def persist(request: dict):
```

Writes a confirmed subrequest to the data store. Called only after `validation_tool` returns `True`.

---

## Subagents (optional)

Specialists that can replace direct tool calls for more complex logic:

| Subagent | Replaces |
|---|---|
| Page Extraction Agent | `extract_page_tool` calls |
| Subrequest Detection Agent | `detect_subrequests_tool` call |
| Validation Agent | `validation_tool` interaction |

Each is implemented as a separate prompt or callable agent. Task subagents do not inherit orchestrator context — pass all needed context explicitly.

---

## Parallel Processing

```python
summaries = await asyncio.gather(*[
    extract_page(page) for page in pages
])
```

Use for `extract_page` across all pages simultaneously. Do not parallelize `detect_subrequests` or `persist` — they depend on prior results.

---

## State Management

Choose one approach per deployment context:

| Option | When to use |
|---|---|
| In-memory state | Short-lived sessions, prototypes |
| JSON intermediate files | Restartable pipelines, audit trail needed |
| Database | Production, multi-user, persistence required |

---

## Error Handling

```python
try:
    result = tool()
except ToolError:
    retry()
```

Tools should return structured errors (`is_error: True` with a reason code) rather than raising exceptions. The orchestrator uses the error code to decide whether to retry, escalate, or abort.

---

## Validation Flow

```
Agent proposes subrequest → human reviews → human confirms → persist
                                          ↘ human rejects → discard / flag
```

Never skip validation. Never persist without explicit human confirmation.

---

## Orchestrator System Prompt

```
You are an autonomous agent that processes ticket PDFs.

Objectives:
1. Extract structured information
2. Identify subrequests
3. Validate with human
4. Persist results

Rules:
- Always process page-by-page
- Always summarize before grouping
- Never skip validation
- Use tools instead of guessing
```

---

## Project Structure

```
/agents
    orchestrator.py
    extraction_agent.py
    detection_agent.py

/tools
    split_pdf.py
    extract_page.py
    detect_subrequests.py
    persist.py

/config
    CLAUDE.md

/data
    sample.pdf
    output.csv
```

---

## Best Practices

- Keep tools small and composable — one responsibility each
- Use JSON outputs at every tool boundary
- Minimize context passed between stages — pass only what the next step needs
- Maintain explicit control of the loop — the orchestrator decides, tools execute
- Use subagents for complex sub-tasks that would otherwise bloat the orchestrator context

---

## Future Improvements

- OCR support for scanned / image-based PDFs
- Multi-document handling (batch ingestion)
- Advanced clustering for subrequest grouping
- Integration with enterprise ticketing systems

---

## Summary

An agentic workflow combining orchestration, parallel tool execution, and human validation to transform unstructured ticket PDFs into structured, actionable subrequests. The orchestrator loop drives all decisions; tools handle execution; humans gate every write.
