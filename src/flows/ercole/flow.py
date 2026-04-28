"""Ercole pension fund document processing flow.

Pipeline:
  1. Document Reader  — one specialist per page, run in parallel
  2. Task Recognizer  — single call on aggregated page metadata → YAML requests
  3. Worker           — page allocator: assigns pages to each request → YAML assignments
  4. Summarizer       — produces markdown report
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

import yaml

from src.flows.base import BaseFlow
from src.flows.ercole.specialists import (
    DOCUMENT_READER,
    FOLLOW_UP_AGENT,
    SUMMARIZER,
    TASK_RECOGNIZER,
    WORKER,
    build_doc_reader_message,
    build_follow_up_message,
    build_summarizer_message,
    build_task_recognizer_message,
    build_worker_message,
)
from src.schemas.document import (
    Contact,
    DocumentProcessingResponse,
    ExternalModule,
    FilledField,
    PageExtraction,
    ErcoleRequest,
    RequestPageAssignment,
)
from src.utils import parse_json_result, parse_yaml_result, run_specialist

logger = logging.getLogger(__name__)

_CONTACT_FIELDS = set(Contact.model_fields)


# ---------------------------------------------------------------------------
# Input formatters
# ---------------------------------------------------------------------------


def _pages_information_yaml(pages: list[PageExtraction]) -> str:
    """Convert Document Reader output to Task Recognizer input format."""
    page_dicts = []
    for p in pages:
        field_names = [f.field_name for f in p.filled_fields]
        extracted = {f.field_name: f.field_value for f in p.filled_fields}
        page_dicts.append(
            {
                "page_number": p.page_number,
                "page_content": p.summary,
                "visual_indicators": {
                    "header_text": p.header,
                    "document_type": "MODULO_ERCOLE" if p.header else "OTHER",
                    "has_fields": field_names,
                },
                "extracted_text_by_section": extracted,
                "entities": p.entities,
            }
        )
    data = {"pages_information": {"total_pages": len(page_dicts), "pages": page_dicts}}
    return yaml.dump(data, allow_unicode=True, default_flow_style=False)


def _attachment_metadata_yaml(pages: list[PageExtraction]) -> str:
    """Compact page summary for the Worker prompt."""
    page_dicts = [
        {
            "page_number": p.page_number,
            "header": p.header,
            "summary": p.summary,
            "entities": p.entities,
            "fields": [f.field_name for f in p.filled_fields],
        }
        for p in pages
    ]
    return yaml.dump({"pages": page_dicts}, allow_unicode=True, default_flow_style=False)


# ---------------------------------------------------------------------------
# Output parsers
# ---------------------------------------------------------------------------


def _parse_page_extraction(raw: dict[str, Any], fallback_number: int) -> PageExtraction:
    return PageExtraction(
        page_number=raw.get("page_number", fallback_number),
        header=raw.get("header", ""),
        summary=raw.get("summary", ""),
        entities=raw.get("entities", []),
        filled_fields=[
            FilledField(field_name=f["field_name"], field_value=f["field_value"])
            for f in raw.get("filled_fields", [])
            if isinstance(f, dict) and "field_name" in f and "field_value" in f
        ],
    )


def _parse_contact(raw: dict[str, Any]) -> Contact:
    return Contact(**{k: v for k, v in raw.items() if k in _CONTACT_FIELDS})


def _parse_external_module(raw: Any) -> ExternalModule | None:
    if isinstance(raw, dict):
        return ExternalModule(
            module_name=raw.get("module_name", ""),
            page_section=raw.get("page_section"),
            ercole_related=bool(raw.get("ercole_related", False)),
        )
    return None


def _parse_ercole_request(raw: dict[str, Any]) -> ErcoleRequest:
    contacts = [
        _parse_contact(c) for c in raw.get("contacts", []) if isinstance(c, dict)
    ]
    ext_mods = [
        m
        for m in (_parse_external_module(e) for e in raw.get("external_modules", []))
        if m is not None
    ]
    return ErcoleRequest(
        request_id=raw.get("request_id", ""),
        page_number=raw.get("page_number", 0),
        header=raw.get("header", ""),
        contacts=contacts,
        notes=raw.get("notes"),
        confidence_score=float(raw.get("confidence_score", 0.0)),
        external_modules=ext_mods,
    )


def _parse_worker_output(
    raw: dict[str, Any],
) -> tuple[dict[str, RequestPageAssignment], RequestPageAssignment | None]:
    assignments: dict[str, RequestPageAssignment] = {}
    excluded: RequestPageAssignment | None = None
    for key, val in raw.items():
        if not isinstance(val, dict):
            continue
        assignment = RequestPageAssignment(
            pages=sorted(set(int(p) for p in val.get("pages", []) if isinstance(p, int))),
            reasoning=val.get("reasoning", ""),
            confidence_score=int(val.get("confidence_score", 0)),
        )
        if key == "excluded_pages":
            excluded = assignment
        else:
            assignments[key] = assignment
    return assignments, excluded


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


class ErcoleFlow(BaseFlow):
    flow_type = "ercole"
    description = (
        "Processa documenti del fondo pensione Ercole: identifica moduli e richieste, "
        "estrae dati anagrafici dei contatti, assegna le pagine a ciascuna richiesta "
        "e produce un report strutturato."
    )
    routing_hints = [
        "fondo pensione", "ercole", "modulo", "adesione", "anticipazione",
        "riscatto", "trasferimento posizione", "contribuzione", "nota informativa",
        "pegaso", "tfr", "premorienza", "pensionistico", "comparto",
    ]

    async def run(self, pages: list[dict]) -> DocumentProcessingResponse:
        session_id = str(uuid.uuid4())

        # Step 1: Document Reader — one specialist per page, in parallel
        logger.info("Step 1: Document Reader (%d pages)", len(pages))
        dr_results = await asyncio.gather(
            *[
                run_specialist(
                    DOCUMENT_READER,
                    build_doc_reader_message(p["page_number"], p["text"]),
                )
                for p in pages
            ]
        )
        page_extractions = [
            _parse_page_extraction(parse_json_result(raw), p["page_number"])
            for p, raw in zip(pages, dr_results)
        ]

        # Step 2: Task Recognizer — single call on aggregated page info
        logger.info("Step 2: Task Recognizer")
        pages_yaml = _pages_information_yaml(page_extractions)
        tr_raw = await run_specialist(TASK_RECOGNIZER, build_task_recognizer_message(pages_yaml))
        tr_data = parse_yaml_result(tr_raw)

        ercole_requests: list[ErcoleRequest] = []
        top_level_external: list[str] = []
        if isinstance(tr_data, dict):
            for req_raw in tr_data.get("requests", []):
                if isinstance(req_raw, dict):
                    ercole_requests.append(_parse_ercole_request(req_raw))
            ext = tr_data.get("external_modules", [])
            if isinstance(ext, list):
                top_level_external = [str(e) for e in ext]

        # Step 3: Worker — assign pages to each identified request
        logger.info("Step 3: Worker (page allocator)")
        worker_msg = build_worker_message(
            llm_instructions=tr_raw or "",
            attachment_metadata=_attachment_metadata_yaml(page_extractions),
        )
        w_raw = await run_specialist(WORKER, worker_msg)
        w_data = parse_yaml_result(w_raw)
        page_assignments, _ = _parse_worker_output(
            w_data if isinstance(w_data, dict) else {}
        )

        # Step 4: Summarizer — produce markdown report
        logger.info("Step 4: Summarizer")
        summary_ctx = {
            "total_pages": len(pages),
            "requests": [r.model_dump() for r in ercole_requests],
            "page_assignments": {k: v.model_dump() for k, v in page_assignments.items()},
            "external_modules": top_level_external,
        }
        summary_text = await run_specialist(
            SUMMARIZER,
            build_summarizer_message(json.dumps(summary_ctx, indent=2, ensure_ascii=False)),
        ) or ""

        return DocumentProcessingResponse(
            session_id=session_id,
            total_pages=len(pages),
            page_extractions=page_extractions,
            requests=ercole_requests,
            page_assignments=page_assignments,
            external_modules=top_level_external,
            summary=summary_text,
        )

    async def handle_followup(
        self, session_id: str, question: str, context: dict
    ) -> str:
        result = await run_specialist(
            FOLLOW_UP_AGENT,
            build_follow_up_message(
                analysis_context=json.dumps(context, indent=2, ensure_ascii=False),
                question=question,
            ),
        )
        return result or "Unable to answer the question based on the available context."
