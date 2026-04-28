# Agentic Ticket Processing System - Implementation Guide

## 1. Overview

This document describes the design and implementation of an agentic system built using the Claude Agent SDK. The system processes ticket PDFs, extracts structured information, identifies subrequests, validates them with a human, and persists the results.

---

## 2. Core Principles

- Agent = iterative loop (observe → plan → act → evaluate)
- Tool-first architecture
- Stateless, parallelizable sub-tasks
- Human-in-the-loop validation
- Structured outputs (JSON)

---

## 3. System Architecture

### High-Level Flow

Orchestrator Agent
→ split_pdf_tool
→ extract_page_tool (parallel)
→ detect_subrequests_tool
→ validation_tool (HITL)
→ persist_tool

---

## 4. Components

### 4.1 Orchestrator Agent

Responsibilities:
- Controls execution loop
- Decides next actions
- Calls tools and subagents
- Maintains state

Pseudo-code:

```
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

### 4.2 Tool Layer

#### split_pdf_tool

```
def split_pdf(file_path: str) -> List[Page]:
```

Output: list of pages

---

#### extract_page_tool

```
def extract_page(page: str) -> dict:
```

Output:
```
{
  "header": str,
  "entities": list[str],
  "summary": str
}
```

---

#### detect_subrequests_tool

```
def detect_subrequests(page_summaries: list, rules: str) -> list:
```

Output:
```
[
  {
    "request_id": "R1",
    "pages": [1,2],
    "description": "...",
    "data": {}
  }
]
```

---

#### validation_tool

```
def validate_request(request: dict) -> bool:
```

---

#### persist_tool

```
def persist(request: dict):
```

---

## 5. Subagents

Optional specialized agents:

- Page Extraction Agent
- Subrequest Detection Agent
- Validation Agent

Each can be implemented as a separate prompt or callable agent.

---

## 6. Prompt Design

### Orchestrator Prompt

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

---

## 7. CLAUDE.md

```
# TicketMind Agent System

## Goal
Process ticket PDFs into structured subrequests

## Workflow
1. Split PDF
2. Extract page info
3. Detect subrequests
4. Validate
5. Persist

## Rules
- Always use tools
- Never hallucinate data
- Require human validation
```

---

## 8. Parallel Processing

```
summaries = await asyncio.gather(*[
    extract_page(page) for page in pages
])
```

---

## 9. State Management

Options:
- In-memory state
- JSON intermediate files
- Database (optional)

---

## 10. Error Handling

```
try:
    result = tool()
except:
    retry()
```

---

## 11. Validation Flow

Agent → propose → human confirm → persist

---

## 12. Project Structure

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

## 13. Best Practices

- Keep tools small and composable
- Use JSON outputs
- Minimize context
- Explicit control of loop
- Use subagents for complex tasks

---

## 14. Future Improvements

- OCR support
- Multi-document handling
- Advanced clustering
- Integration with enterprise systems

---

## 15. Summary

The system implements an agentic workflow using Claude Agent SDK principles, combining orchestration, tool usage, parallel processing, and human validation to transform unstructured ticket PDFs into structured actionable data.

