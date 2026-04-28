# DocumentAI — Ercole Document Processor Architecture

## Mission

Automated pipeline for processing Italian pension fund (Ercole) documents. The system receives raw OCR text per page, runs a multi-agent pipeline to identify pension-fund module requests, assigns pages to each request, and returns a structured markdown report. Follow-up questions are handled via a separate path (Scenario B) using stored session artifacts.

---

## System Architecture

```mermaid
flowchart TD
    User([User / API Client])
    API[FastAPI\n/process-document\n/followup\n/flows]

    User -->|POST pages + flow_type| API

    subgraph Scenario A — Document Processing
        direction TB
        DR["Document Reader\n(Haiku · 1 per page · parallel)\ndocs/tmp/document-reader-prompt.txt"]
        TR["Task Recognizer\n(Sonnet · 1 call)\ndocs/tmp/task-recognizer-prompt.txt"]
        WK["Worker — Page Allocator\n(Sonnet · 1 call)\ndocs/tmp/worker-prompt.txt"]
        SUM["Summarizer\n(Sonnet · 1 call)"]

        DR -->|"JSON per page\n(header, summary, entities, filled_fields)"| TR
        TR -->|"YAML requests list\n(request_id, header, contacts, confidence)"| WK
        DR -->|"page metadata YAML\n(attachment_metadata)"| WK
        WK -->|"YAML page assignments\n(pages[], reasoning, confidence)"| SUM
        TR -->|requests| SUM
        SUM -->|markdown report| API
    end

    subgraph Scenario B — Follow-up
        direction TB
        FU["Follow-up Agent\n(Sonnet · 1 call)"]
        SS[(Session Store\nin-memory / Redis)]
    end

    API -->|pages| DR
    SUM -->|DocumentProcessingResponse| API
    API -->|session_id + result| SS
    User -->|POST session_id + question| API
    SS -->|stored artifacts| FU
    FU -->|answer| API
    API -->|FollowUpResponse| User
```

---

## Component Details

### Document Reader
- **File**: `docs/tmp/document-reader-prompt.txt`
- **Model**: `claude-haiku-4-5-20251001` (fast, cost-efficient for per-page extraction)
- **Pattern**: one-shot `query()`, called once per page in parallel via `asyncio.gather()`
- **Input**: raw OCR text for a single page
- **Output**: JSON with `page_number`, `header`, `summary`, `entities[]`, `filled_fields[]`
- **Rule**: processes exactly one page; never infers from other pages

### Task Recognizer
- **File**: `docs/tmp/task-recognizer-prompt.txt`
- **Model**: `claude-sonnet-4-6`
- **Pattern**: one-shot `query()`, single call on aggregated page metadata
- **Input**: YAML `pages_information` built from all Document Reader outputs
- **Output**: YAML `requests[]` list — each item has `request_id`, `page_number`, `header`, `contacts`, `notes`, `confidence_score`, `external_modules`
- **Key feature**: 40+ Ercole module header lookup table; distinguishes PERSONA FISICA from ENTITA GIURIDICA contacts
- **Template var**: `{{pages_information}}` in the `## INPUT FILE` section

### Worker (Page Allocator)
- **File**: `docs/tmp/worker-prompt.txt`
- **Model**: `claude-sonnet-4-6`
- **Pattern**: one-shot `query()`, single call
- **Input**:
  - `{{ llm_instructions }}` = Task Recognizer YAML output (requests with request IDs)
  - `{{ attachment_metadata }}` = compact page summaries from Document Reader
- **Output**: YAML keyed by `request_id` — each with `pages[]`, `reasoning`, `confidence_score`
- **Rule**: assigns pages to requests; excludes blank pages; respects PAGINA SECONDARIA continuity

### Summarizer
- **Model**: `claude-sonnet-4-6`
- **Pattern**: one-shot `query()`, single call
- **Input**: JSON summary context (requests + page_assignments + external_modules)
- **Output**: markdown report with summary table, per-request details, anomalies section

### Follow-up Agent (Scenario B)
- **Model**: `claude-sonnet-4-6`
- **Pattern**: one-shot `query()`, single call
- **Input**: stored `DocumentProcessingResponse` JSON + user question
- **Output**: natural language answer grounded in the stored analysis

---

## Data Flow Schemas

### Document Reader Output (per page)
```json
{
  "page_number": 1,
  "header": "MODULO DI ADESIONE A ERCOLE",
  "summary": "Adhesion form for Mario Rossi.",
  "entities": ["Mario Rossi", "RSSMRA80A01H501U"],
  "filled_fields": [
    {"field_name": "Nome", "field_value": "Mario"},
    {"field_name": "Cognome", "field_value": "Rossi"}
  ]
}
```

### Task Recognizer Output
```yaml
requests:
  - request_id: REQ_ERCOLE_1_1
    page_number: 1
    header: "MODULO DI ADESIONE A ERCOLE"
    contacts:
      - name: "Mario"
        surname: "Rossi"
        fiscal_code: "RSSMRA80A01H501U"
    notes: "Mario Rossi"
    confidence_score: 0.92
    external_modules: []
external_modules: []
```

### Worker Output
```yaml
REQ_ERCOLE_1_1:
  pages: [1, 2, 3]
  reasoning: "Pages 1-3 share the adhesion module header and show pagination continuity."
  confidence_score: 95
excluded_pages:
  pages: [4]
  reasoning: "Page 4 is blank."
  confidence_score: 100
```

---

## File Structure

```
src/
├── agent.py                          # process_document() / handle_followup() / session store
├── api.py                            # FastAPI: /process-document, /followup, /flows
├── utils.py                          # SpecialistDef, run_specialist, parse_json_result, parse_yaml_result
├── schemas/
│   └── document.py                   # Pydantic v2: FilledField, PageExtraction, ErcoleRequest,
│                                     #   Contact, RequestPageAssignment, DocumentProcessingResponse
└── flows/
    ├── __init__.py                   # FLOW_REGISTRY + get_flow() + list_flows()
    ├── base.py                       # BaseFlow ABC (run, handle_followup)
    └── ercole/
        ├── __init__.py
        ├── specialists.py            # DOCUMENT_READER, TASK_RECOGNIZER, WORKER, SUMMARIZER,
        │                             #   FOLLOW_UP_AGENT (SpecialistDef instances + build_worker_message)
        └── flow.py                   # ErcoleFlow — orchestrates the full 4-step pipeline

docs/tmp/                             # Authoritative prompt files (source of truth)
    ├── document-reader-prompt.txt
    ├── task-recognizer-prompt.txt
    └── worker-prompt.txt
```

---

## Extensibility — Adding a New Flow

1. Create `src/flows/<new_flow>/` with `__init__.py`, `specialists.py`, `flow.py`
2. Subclass `BaseFlow`, implement `run()` and `handle_followup()`
3. Register in `src/flows/__init__.py`: `FLOW_REGISTRY["<new_flow>"] = NewFlow`
4. The coordinator, API, and session store require zero changes

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/flows` | List available flow types |
| `POST` | `/process-document` | Run the full pipeline; returns `DocumentProcessingResponse` |
| `POST` | `/followup` | Answer a question about a previous session |

### POST /process-document
```json
{
  "pages": [
    {"page_number": 1, "text": "raw OCR text of page 1"},
    {"page_number": 2, "text": "raw OCR text of page 2"}
  ],
  "flow_type": "ercole",
  "session_id": "optional-custom-id"
}
```

### POST /followup
```json
{
  "session_id": "sess-uuid-from-previous-response",
  "question": "Qual è il codice fiscale dell'aderente nella prima richiesta?"
}
```

---

## SDK Patterns

All specialists use the one-shot `query()` pattern from `claude-code-sdk`:

```python
async for msg in query(prompt=prompt, options=options):
    if isinstance(msg, ResultMessage):
        result = msg.result if msg.subtype == "success" else None
# Do NOT break early — let the generator exhaust naturally
```

The generator is always fully consumed to avoid event loop poisoning (SDK anti-pattern #454). `asyncio.timeout(90)` prevents disconnect hangs (SDK anti-pattern #378).

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Haiku for Document Reader | Fast and cheap for per-page extraction; runs N in parallel |
| YAML for Task Recognizer / Worker output | Prompts specify YAML; more readable for structured lists |
| Worker is a page allocator, not a data extractor | Contact/field data is already extracted by Task Recognizer; Worker only groups pages to requests |
| SpecialistDef over AgentDefinition | `AgentDefinition` not available in `claude-code-sdk` 0.0.25 |
| `disallowed_tools` not `tools=` | SDK uses blacklist model; whitelist (`tools=`) is not a valid option |
| In-memory session store | Sufficient for MVP; swap for Redis with no API changes |
| Prompts loaded from txt files at import time | Prompts in `docs/tmp/` are the single source of truth; no duplication in code |
