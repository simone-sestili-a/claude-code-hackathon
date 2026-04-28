"""FastAPI application — REST interface for the document-processing pipeline."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src import agent
from src.schemas.document import DocumentProcessingResponse

logging.basicConfig(level=logging.INFO)


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


class PageInput(BaseModel):
    page_number: int
    text: str


class ProcessDocumentRequest(BaseModel):
    pages: list[PageInput] = Field(..., min_length=1)
    flow_type: str = "ercole"
    session_id: str | None = None


class FollowUpRequest(BaseModel):
    session_id: str
    question: str


class FollowUpResponse(BaseModel):
    session_id: str
    answer: str


class ChatRequest(BaseModel):
    message: str
    pages: list[PageInput] | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str | None = None
    flow_type: str | None = None
    intent: str
    response: str
    document_result: dict | None = None


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "document-ai"}


@app.get("/flows")
async def list_flows() -> dict[str, list[str]]:
    return {"flows": agent.get_available_flows()}


@app.post("/process-document", response_model=DocumentProcessingResponse)
async def process_document(request: ProcessDocumentRequest) -> DocumentProcessingResponse:
    pages = [{"page_number": p.page_number, "text": p.text} for p in request.pages]
    try:
        return await agent.process_document(
            pages=pages,
            flow_type=request.flow_type,
            session_id=request.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Document processing failed")
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")


@app.post("/followup", response_model=FollowUpResponse)
async def follow_up(request: FollowUpRequest) -> FollowUpResponse:
    answer = await agent.handle_followup(request.session_id, request.question)
    return FollowUpResponse(session_id=request.session_id, answer=answer)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    pages = (
        [{"page_number": p.page_number, "text": p.text} for p in request.pages]
        if request.pages
        else None
    )
    try:
        result = await agent.handle_chat_message(
            message=request.message,
            pages=pages,
            session_id=request.session_id,
        )
        return ChatResponse(
            session_id=result.session_id,
            flow_type=result.flow_type,
            intent=result.intent,
            response=result.response,
            document_result=result.document_result,
        )
    except Exception as exc:
        logger.exception("Chat message handling failed")
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}")
