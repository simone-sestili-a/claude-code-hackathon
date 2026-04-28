"""Pydantic v2 schemas for the document-processing pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FilledField(BaseModel):
    field_name: str
    field_value: str


class PageExtraction(BaseModel):
    """Output of the Document Reader specialist for a single page."""

    page_number: int
    header: str = ""
    summary: str = ""
    entities: list[str] = Field(default_factory=list)
    filled_fields: list[FilledField] = Field(default_factory=list)


class ExternalModule(BaseModel):
    module_name: str
    page_section: str | None = None
    ercole_related: bool = False


class Contact(BaseModel):
    """Unified contact: either PERSONA FISICA or ENTITA GIURIDICA fields."""

    # PERSONA FISICA
    name: str | None = None
    surname: str | None = None
    fiscal_code: str | None = None
    data_nascita: str | None = None
    luogo_nascita: str | None = None
    provincia_nascita: str | None = None
    genere: str | None = None
    # ENTITA GIURIDICA
    ragione_sociale: str | None = None
    piva: str | None = None


class ErcoleRequest(BaseModel):
    """Output of the Task Recognizer for one identified Ercole module."""

    request_id: str
    page_number: int
    header: str
    contacts: list[Contact] = Field(default_factory=list)
    notes: str | None = None
    confidence_score: float = 0.0
    external_modules: list[ExternalModule] = Field(default_factory=list)


class RequestPageAssignment(BaseModel):
    """Output of the Worker (page allocator) for one request."""

    pages: list[int] = Field(default_factory=list)
    reasoning: str = ""
    confidence_score: int = 0


class DocumentProcessingResponse(BaseModel):
    """Final response returned by the pipeline."""

    session_id: str
    total_pages: int
    page_extractions: list[PageExtraction] = Field(default_factory=list)
    requests: list[ErcoleRequest] = Field(default_factory=list)
    page_assignments: dict[str, RequestPageAssignment] = Field(default_factory=dict)
    external_modules: list[str] = Field(default_factory=list)
    summary: str = ""
