"""Specialist definitions and user-message builders for the Ercole document flow.

Each specialist is backed by a .j2 prompt file in prompts/.
The file is split at {# === USER INPUT BELOW === #} into:
  - system prompt (static, loaded once at import time)
  - user message template (rendered per-call via Jinja2 with {{ variable }} placeholders)
"""

from __future__ import annotations

from src.flows.ercole.prompts import PromptTemplate
from src.utils import SpecialistDef

_SONNET = "claude-sonnet-4-6"
_HAIKU = "claude-haiku-4-5-20251001"

_doc_reader = PromptTemplate.load("document_reader.j2")
_task_recognizer = PromptTemplate.load("task_recognizer.j2")
_worker = PromptTemplate.load("worker.j2")
_summarizer = PromptTemplate.load("summarizer.j2")
_follow_up_agent = PromptTemplate.load("follow_up_agent.j2")

DOCUMENT_READER = SpecialistDef(
    description="Extracts structured metadata (header, summary, entities, fields) from a single document page",
    prompt=_doc_reader.system,
    model=_HAIKU,
)

TASK_RECOGNIZER = SpecialistDef(
    description="Identifies Ercole pension fund module requests from aggregated page metadata",
    prompt=_task_recognizer.system,
    model=_SONNET,
)

WORKER = SpecialistDef(
    description="Assigns document pages to identified requests (page allocator)",
    prompt=_worker.system,
    model=_SONNET,
)

SUMMARIZER = SpecialistDef(
    description="Generates a structured markdown report from extracted requests and page assignments",
    prompt=_summarizer.system,
    model=_SONNET,
)

FOLLOW_UP_AGENT = SpecialistDef(
    description="Answers follow-up questions about a previously processed Ercole document",
    prompt=_follow_up_agent.system,
    model=_SONNET,
)


def build_doc_reader_message(page_number: int, page_text: str) -> str:
    return _doc_reader.render_user(page_number=page_number, page_text=page_text)


def build_task_recognizer_message(pages_information: str) -> str:
    return _task_recognizer.render_user(pages_information=pages_information)


def build_worker_message(llm_instructions: str, attachment_metadata: str) -> str:
    return _worker.render_user(
        llm_instructions=llm_instructions,
        attachment_metadata=attachment_metadata,
    )


def build_summarizer_message(summary_context: str) -> str:
    return _summarizer.render_user(summary_context=summary_context)


def build_follow_up_message(analysis_context: str, question: str) -> str:
    return _follow_up_agent.render_user(
        analysis_context=analysis_context,
        question=question,
    )
