"""Abstract base class for document processing flows."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.schemas.document import DocumentProcessingResponse


class BaseFlow(ABC):
    flow_type: str = ""

    @abstractmethod
    async def run(self, pages: list[dict]) -> DocumentProcessingResponse:
        """Run the full pipeline for this flow type."""
        ...

    @abstractmethod
    async def handle_followup(self, session_id: str, question: str, context: dict) -> str:
        """Answer a follow-up question using the stored flow artifacts."""
        ...
