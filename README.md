# DocumentAI — Pension Fund Document Processor

Multi-agent pipeline for automated processing of Italian pension fund documents. Classifies incoming requests, routes them through a specialist pipeline (Document Reader → Task Recognizer → Worker → Summarizer), and exposes the result via a REST API with PDF upload support.

A full-featured **web frontend** is included in [`frontend/`](./frontend/) — built with Next.js 14, Tailwind CSS, and shadcn/ui.

Built with **Claude Agent SDK** · **FastAPI** · **Python 3.12** · **uv**

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for the frontend)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 1. Install backend dependencies

```bash
uv sync
```

For dev tools (pytest, mypy, ruff):

```bash
uv sync --all-extras
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your LiteLLM proxy credentials:

```env
ANTHROPIC_BASE_URL=https://your-proxy-host/proxylab
ANTHROPIC_AUTH_TOKEN=sk-your-token-here

ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-haiku
ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet
ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus
```

### 3. Start the API

```bash
uv run uvicorn src.api:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### 4. Start the frontend (optional)

```bash
cd frontend
npm install
cp .env.example .env.local   # sets NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

See [`frontend/README.md`](./frontend/README.md) for full frontend documentation.

---

## API Endpoints

All page-accepting endpoints use `multipart/form-data` to support PDF file uploads alongside text.

### `POST /chat` — Main chat interface

Send a message and optionally attach a document. The coordinator classifies intent and routes to the correct flow.

```bash
# With PDF upload
curl -X POST http://localhost:8000/chat \
  -F "message=Analizza questo documento" \
  -F "pdf=@modulo_ercole.pdf"

# With pre-extracted text
curl -X POST http://localhost:8000/chat \
  -F "message=Analizza questo documento" \
  -F 'pages_json=[{"page_number":1,"text":"MODULO DI ADESIONE Ercole..."}]'

# Follow-up question on a previous session
curl -X POST http://localhost:8000/chat \
  -F "message=Quali dati anagrafici hai estratto?" \
  -F "session_id=<session_id_from_previous_response>"
```

**Form fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | yes | Chat message |
| `pdf` | file | no | PDF to process |
| `pages_json` | string (JSON) | no | Pre-extracted pages: `[{"page_number": 1, "text": "..."}]` |
| `session_id` | string | no | Resume a previous session for follow-up questions |

**Response:**

```json
{
  "session_id": "uuid",
  "flow_type": "ercole",
  "intent": "new_document",
  "response": "Ho analizzato il documento...",
  "document_result": { ... }
}
```

---

### `POST /process-document` — Direct pipeline call

Skips the classifier — runs the full pipeline directly. Requires at least one page source.

```bash
# With PDF upload
curl -X POST http://localhost:8000/process-document \
  -F "flow_type=ercole" \
  -F "pdf=@modulo_ercole.pdf"

# With text pages
curl -X POST http://localhost:8000/process-document \
  -F 'pages_json=[{"page_number":1,"text":"..."},{"page_number":2,"text":"..."}]'
```

---

### `POST /extract-pdf` — PDF text extraction

Extracts raw page text from an uploaded PDF. Useful for inspecting content before processing.

```bash
curl -X POST http://localhost:8000/extract-pdf \
  -F "pdf=@modulo_ercole.pdf"
```

**Response:**

```json
{
  "total_pages": 3,
  "pages": [
    {"page_number": 1, "text": "MODULO DI ADESIONE..."},
    {"page_number": 2, "text": "..."}
  ]
}
```

---

### `POST /followup` — Follow-up question (JSON)

Ask a question about a previously processed document.

```bash
curl -X POST http://localhost:8000/followup \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "question": "Qual è il codice fiscale del richiedente?"}'
```

---

### `GET /flows` — List available flows

```bash
curl http://localhost:8000/flows
# {"flows": ["ercole"]}
```

---

## Processing Pipeline

```
User message + optional PDF
        │
        ▼
  Coordinator (Haiku)
  └─ classifies intent: new_document | follow_up | off_topic
        │
        ▼ (new_document)
  Document Reader × N pages   ←── parallel, one call per page
  └─ extracts: header, summary, entities, filled fields
  └─ tool: extract_page (deterministic pre-extraction baseline)
        │
        ▼
  Task Recognizer
  └─ identifies Ercole module requests from aggregated page metadata
  └─ tools: detect_subrequests, validate_request
        │
        ▼
  Worker (page allocator)
  └─ assigns pages to each identified request
  └─ tools: validate_request, validate_requests
        │
        ▼
  Summarizer
  └─ produces structured markdown report
  └─ tools: validate_requests, persist_result, persist_results
        │
        ▼
  CoordinatorResponse (session stored for follow-ups)
```

Each specialist can call deterministic MCP tools for pre-extraction, grouping, and validation — reducing LLM hallucination and enabling self-correction before output.

---

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Type check
uv run mypy src/ --ignore-missing-imports

# Lint
uv run ruff check src/ tests/
```

### Adding a new flow

1. Create `src/flows/<name>/` with `flow.py`, `specialists.py`, `prompts/`
2. Subclass `BaseFlow` and set `flow_type`, `description`, `routing_hints`
3. Register it in `src/flows/__init__.py` inside `_build_registry()`

The coordinator, API, and session store require no other changes.

### Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_BASE_URL` | LiteLLM proxy base URL |
| `ANTHROPIC_AUTH_TOKEN` | Proxy auth token (mapped to `ANTHROPIC_API_KEY` automatically) |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Model alias for haiku (default: `claude-haiku-4-5-20251001`) |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Model alias for sonnet (default: `claude-sonnet-4-6`) |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Model alias for opus (default: `claude-opus-4-7`) |
| `ANTHROPIC_API_KEY` | Direct Anthropic API key (alternative to proxy) |
