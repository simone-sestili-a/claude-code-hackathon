"""FastAPI application — REST interface for the document-processing pipeline.

Request formats
---------------
Endpoints that accept document pages use multipart/form-data so that an
optional PDF file can be uploaded alongside other fields.

  pdf (File, optional)
      Raw PDF file. Pages are extracted as plain text via PyMuPDF.

  pages_json (Form, optional)
      JSON-encoded array of {"page_number": int, "text": str} objects.
      Explicit pages override PDF-extracted pages with the same page number.

If both pdf and pages_json are supplied, pages are merged: PDF provides the
baseline and pages_json overrides individual pages by page_number.
"""

from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Any

from src import agent
from src.logging_config import configure_logging, set_request_id
from src.schemas.document import DocumentProcessingResponse
from src.tools.pdf_tools import pdf_bytes_to_pages

configure_logging()
logger = logging.getLogger(__name__)


app = FastAPI(
    title="DocumentAI — Ercole Document Processor",
    description="Automated processing of Italian pension fund (Ercole) documents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class _RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns a short request ID to every request and logs timing."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        rid = uuid.uuid4().hex[:8]
        set_request_id(rid)
        start = time.monotonic()
        logger.info("→ %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.info(
                "← %s %s %d (%.0f ms)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
            return response
        except Exception:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.exception(
                "← %s %s ERROR (%.0f ms)", request.method, request.url.path, elapsed_ms
            )
            raise


app.add_middleware(_RequestLoggingMiddleware)


# ---------------------------------------------------------------------------
# Response models (remain JSON regardless of request format)
# ---------------------------------------------------------------------------


class FollowUpRequest(BaseModel):
    session_id: str
    question: str


class FollowUpResponse(BaseModel):
    session_id: str
    answer: str


class ChatResponse(BaseModel):
    session_id: str | None = None
    flow_type: str | None = None
    intent: str
    response: str
    document_result: dict | None = None


class ExtractPdfResponse(BaseModel):
    total_pages: int
    pages: list[dict]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _build_pages(
    pdf: UploadFile | None,
    pages_json: str | None,
) -> list[dict] | None:
    """Merge PDF-extracted pages with explicitly provided pages.

    PDF pages are extracted first; pages_json entries override by page_number.
    Returns None when neither source provides any pages.
    """
    pages: dict[int, dict] = {}

    if pdf is not None:
        pdf_bytes = await pdf.read()
        size_kb = len(pdf_bytes) / 1024
        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="Uploaded PDF file is empty")
        logger.info("PDF upload: filename=%s size=%.1f KB", pdf.filename, size_kb)
        try:
            extracted = pdf_bytes_to_pages(pdf_bytes)
            logger.info("PDF extracted: %d pages from %s", len(extracted), pdf.filename)
            for p in extracted:
                pages[p["page_number"]] = p
        except ValueError as exc:
            logger.error("PDF extraction failed: filename=%s error=%s", pdf.filename, exc)
            raise HTTPException(status_code=400, detail=f"Invalid PDF: {exc}")

    if pages_json is not None:
        try:
            parsed: list[dict] = json.loads(pages_json)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid pages_json: %s", exc)
            raise HTTPException(status_code=400, detail=f"pages_json is not valid JSON: {exc}")
        logger.debug("pages_json override: %d page(s)", len(parsed))
        for p in parsed:
            pages[p["page_number"]] = p

    if not pages:
        return None
    return sorted(pages.values(), key=lambda p: p["page_number"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "document-ai"}


@app.get("/flows")
async def list_flows() -> dict[str, list[str]]:
    return {"flows": agent.get_available_flows()}


@app.post("/extract-pdf", response_model=ExtractPdfResponse)
async def extract_pdf(pdf: UploadFile = File(...)) -> ExtractPdfResponse:
    """Extract plain text from each page of an uploaded PDF.

    Useful for inspecting OCR output before sending to the processing pipeline.
    """
    pdf_bytes = await pdf.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF file is empty")
    try:
        pages = pdf_bytes_to_pages(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid PDF: {exc}")
    return ExtractPdfResponse(total_pages=len(pages), pages=pages)


@app.post("/process-document", response_model=DocumentProcessingResponse)
async def process_document(
    flow_type: str = Form("ercole"),
    session_id: str | None = Form(None),
    pdf: UploadFile | None = File(None),
    pages_json: str | None = Form(None),
) -> DocumentProcessingResponse:
    """Run the full document processing pipeline.

    Requires at least one page source: pdf (file upload) or pages_json (text).
    """
    pages = await _build_pages(pdf, pages_json)
    if not pages:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one page: upload a pdf file or pass pages_json.",
        )
    logger.info("process-document: flow=%s pages=%d", flow_type, len(pages))
    try:
        result = await agent.process_document(
            pages=pages,
            flow_type=flow_type,
            session_id=session_id,
        )
        logger.info(
            "process-document done: session=%s requests=%d",
            result.session_id,
            len(result.requests),
        )
        return result
    except ValueError as exc:
        logger.warning("process-document invalid input: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("process-document failed: flow=%s pages=%d", flow_type, len(pages))
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")


@app.post("/followup", response_model=FollowUpResponse)
async def follow_up(request: FollowUpRequest) -> FollowUpResponse:
    answer = await agent.handle_followup(request.session_id, request.question)
    return FollowUpResponse(session_id=request.session_id, answer=answer)


@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    session_id: str | None = Form(None),
    pdf: UploadFile | None = File(None),
    pages_json: str | None = Form(None),
) -> ChatResponse:
    """Main chat endpoint.

    Send a message and optionally attach document pages via pdf upload and/or
    pages_json. The coordinator classifies intent and routes to the correct flow.
    """
    pages = await _build_pages(pdf, pages_json)
    logger.info(
        "chat: session=%s has_pages=%s msg_len=%d",
        session_id or "new",
        pages is not None,
        len(message),
    )
    try:
        result = await agent.handle_chat_message(
            message=message,
            pages=pages,
            session_id=session_id,
        )
        logger.info(
            "chat done: intent=%s flow=%s session=%s",
            result.intent,
            result.flow_type,
            result.session_id,
        )
        return ChatResponse(
            session_id=result.session_id,
            flow_type=result.flow_type,
            intent=result.intent,
            response=result.response,
            document_result=result.document_result,
        )
    except Exception as exc:
        logger.exception("chat failed: session=%s", session_id)
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}")
