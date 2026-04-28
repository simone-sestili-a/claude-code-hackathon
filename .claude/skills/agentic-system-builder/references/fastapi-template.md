# FastAPI Template for Claude Agent SDK

Full template for `src/api.py`. Adapt models and endpoints to the project.

```python
"""FastAPI REST layer — wraps src/agent.py for frontend/service consumption."""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agent import send_query, send_query_simple

app = FastAPI(
    title="{ProjectName} Agent API",
    description="REST API for the {ProjectName} Claude agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response models -----------------------------------------------

class QueryRequest(BaseModel):
    prompt: str
    output_style: Optional[str] = None
    continue_conversation: bool = False
    dry_run: bool = False


class QueryResponse(BaseModel):
    result: str
    num_messages: int


class HealthResponse(BaseModel):
    status: str
    version: str


# --- Endpoints ----------------------------------------------------------------

@app.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest) -> QueryResponse:
    """
    Send a prompt to the agent and get a full response.

    - **prompt**: The request text
    - **output_style**: Optional style override (concise, detailed)
    - **continue_conversation**: Continue the previous conversation turn
    - **dry_run**: Return immediately without calling the LLM (for testing)
    """
    if request.dry_run:
        return QueryResponse(result="[dry-run] ok", num_messages=0)

    try:
        result, messages = await send_query(
            prompt=request.prompt,
            output_style=request.output_style,
            continue_conversation=request.continue_conversation,
        )
        if result is None:
            raise HTTPException(status_code=500, detail="Agent returned no result")
        return QueryResponse(result=result, num_messages=len(messages))
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/simple")
async def query_simple(request: QueryRequest) -> dict[str, str]:
    """Simplified endpoint — returns only the text result."""
    try:
        result = await send_query_simple(
            prompt=request.prompt,
            continue_conversation=request.continue_conversation,
        )
        if result is None:
            raise HTTPException(status_code=500, detail="Agent returned no result")
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/styles")
async def list_output_styles() -> dict:
    """List available output styles."""
    return {
        "styles": [
            {"name": "default", "description": "Standard agent output"},
            {"name": "concise", "description": "Brief, bullet-point style"},
            {"name": "detailed", "description": "Comprehensive, in-depth output"},
        ]
    }


# --- Entry point -------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Running the API

```bash
# Development (hot reload)
uvicorn src.api:app --reload --port 8000

# Production
uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4

# Via Makefile
make run
```

## Example Requests

```bash
# Health check
curl http://localhost:8000/

# Full query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "VPN is down for user u001"}'

# Simple query
curl -X POST http://localhost:8000/query/simple \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the status of ticket TKT-001?"}'

# Dry run (no LLM call — good for CI smoke test)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "dry_run": true}'
```
