"""Document processing coordinator — classifies user intent and routes to the correct flow.

Entry point for all chat messages. The coordinator:
  1. Classifies the message (new_document | follow_up | off_topic)
  2. Routes to the matched flow, or returns a fallback if off_topic

Session state is owned here so that follow-up routing has access to prior results.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from src.flows import get_flow, get_flow_routing_info
from src.utils import PromptTemplate, SpecialistDef, parse_json_result, run_specialist

logger = logging.getLogger(__name__)

_CLASSIFIER_PROMPT = PromptTemplate.from_path(
    Path(__file__).parent / "prompts" / "classifier.j2"
)

_CLASSIFIER = SpecialistDef(
    description="Intent classifier — routes user messages to the correct flow",
    prompt=_CLASSIFIER_PROMPT.system,
    model="claude-haiku-4-5-20251001",
)

_FALLBACK_MESSAGE = (
    "Mi dispiace, non riesco ad aiutarti con questa richiesta. "
    "Sono specializzato nell'elaborazione di documenti del fondo pensione Ercole: "
    "posso analizzare moduli, identificare richieste, estrarre i dati dei contatti "
    "e rispondere a domande su documenti già analizzati.\n\n"
    "Prova a inviarmi il testo OCR di un documento Ercole, "
    "oppure fai una domanda su un'analisi precedente fornendo il session_id."
)

_SESSION_STORE: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ClassificationResult(BaseModel):
    flow_type: str | None = None
    intent: Literal["new_document", "follow_up", "off_topic"] = "off_topic"
    confidence: int = 0


class CoordinatorResponse(BaseModel):
    session_id: str | None = None
    flow_type: str | None = None
    intent: str
    response: str
    document_result: dict | None = None


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


async def _classify(
    user_message: str,
    has_pages: bool,
    has_session: bool,
) -> ClassificationResult:
    available_flows = get_flow_routing_info()
    user_msg = _CLASSIFIER_PROMPT.render_user(
        user_message=user_message,
        has_pages=has_pages,
        has_session=has_session,
        available_flows=available_flows,
    )
    raw = await run_specialist(_CLASSIFIER, user_msg, timeout_seconds=30)
    data = parse_json_result(raw)
    try:
        return ClassificationResult(**data)
    except Exception:
        logger.warning("Classification parse failed for raw=%r, defaulting to off_topic", raw)
        return ClassificationResult(flow_type=None, intent="off_topic", confidence=0)


# ---------------------------------------------------------------------------
# Main coordinator entry point
# ---------------------------------------------------------------------------


async def handle_message(
    user_message: str,
    pages: list[dict] | None = None,
    session_id: str | None = None,
) -> CoordinatorResponse:
    has_pages = bool(pages)
    has_session = session_id is not None and session_id in _SESSION_STORE

    classification = await _classify(user_message, has_pages, has_session)
    logger.info(
        "Classified: intent=%s flow=%s confidence=%d",
        classification.intent,
        classification.flow_type,
        classification.confidence,
    )

    # --- Off-topic ---
    if classification.intent == "off_topic" or classification.flow_type is None:
        return CoordinatorResponse(
            flow_type=None,
            intent="off_topic",
            response=_FALLBACK_MESSAGE,
        )

    flow = get_flow(classification.flow_type)

    # --- Follow-up question on a previous session ---
    if classification.intent == "follow_up":
        session = _SESSION_STORE.get(session_id or "")
        if session:
            answer = await flow.handle_followup(
                session_id=session_id or "",
                question=user_message,
                context=session["result"],
            )
            return CoordinatorResponse(
                session_id=session_id,
                flow_type=classification.flow_type,
                intent="follow_up",
                response=answer,
            )
        # No session found — treat as new_document if pages present, else ambiguous
        if not has_pages:
            return CoordinatorResponse(
                flow_type=classification.flow_type,
                intent="follow_up",
                response=(
                    "Non ho trovato il documento precedente associato a questa sessione. "
                    "Per favore, invia di nuovo il documento da analizzare oppure "
                    "verifica il session_id fornito."
                ),
            )

    # --- New document processing ---
    if not pages:
        return CoordinatorResponse(
            flow_type=classification.flow_type,
            intent="new_document",
            response=(
                "Ho riconosciuto la richiesta come pertinente al flusso "
                f"'{classification.flow_type}', ma non ho ricevuto il contenuto del "
                "documento da analizzare. Per favore, invia anche il testo delle pagine."
            ),
        )

    result = await flow.run(pages)
    _SESSION_STORE[result.session_id] = {
        "flow_type": classification.flow_type,
        "result": result.model_dump(),
    }
    return CoordinatorResponse(
        session_id=result.session_id,
        flow_type=classification.flow_type,
        intent="new_document",
        document_result=result.model_dump(),
        response=result.summary,
    )
