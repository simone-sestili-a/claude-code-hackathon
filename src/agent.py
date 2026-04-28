"""Document processing agent — public API for the pipeline."""

from __future__ import annotations

import logging
from typing import Any

from src.flows import get_flow, list_flows
from src.schemas.document import DocumentProcessingResponse

logger = logging.getLogger(__name__)

# In-memory session store. Replace with Redis for production.
_SESSION_STORE: dict[str, dict[str, Any]] = {}


async def process_document(
    pages: list[dict],
    flow_type: str = "ercole",
    session_id: str | None = None,
) -> DocumentProcessingResponse:
    """Run the full pipeline and persist results to the session store."""
    flow = get_flow(flow_type)
    result = await flow.run(pages)

    if session_id:
        result = result.model_copy(update={"session_id": session_id})

    _SESSION_STORE[result.session_id] = {
        "flow_type": flow_type,
        "result": result.model_dump(),
    }
    logger.info("Session %s stored (%d requests)", result.session_id, len(result.requests))
    return result


async def handle_followup(session_id: str, question: str) -> str:
    """Answer a follow-up question using a stored session's artifacts."""
    session = _SESSION_STORE.get(session_id)
    if not session:
        return (
            f"Session {session_id!r} not found. "
            "Please process a document first via POST /process-document."
        )
    flow = get_flow(session["flow_type"])
    return await flow.handle_followup(session_id, question, session["result"])


def get_available_flows() -> list[str]:
    return list_flows()
