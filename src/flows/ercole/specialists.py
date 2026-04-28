"""Specialist definitions and user-message builders for the Ercole document flow.

Each specialist is backed by a .j2 prompt file in prompts/.
The file is split at {# === USER INPUT BELOW === #} into:
  - system prompt (static, loaded once at import time)
  - user message template (rendered per-call via Jinja2 with {{ variable }} placeholders)
"""

from __future__ import annotations

import src.config as config
from src.flows.ercole.prompts import load_prompt
from src.tools.mcp_server import (
    MCP_SERVER_NAME,
    TOOL_DETECT_SUBREQUESTS,
    TOOL_EXTRACT_PAGE,
    TOOL_PERSIST_RESULT,
    TOOL_PERSIST_RESULTS,
    TOOL_VALIDATE_REQUEST,
    TOOL_VALIDATE_REQUESTS,
    build_document_tools_server,
)
from src.utils import SpecialistDef

# Shared in-process MCP server — built once, reused by all specialists that need tools
_DOCUMENT_TOOLS = build_document_tools_server()


def _mcp(tools: list[str]) -> dict:
    return {MCP_SERVER_NAME: _DOCUMENT_TOOLS}

_HAIKU = config.HAIKU_MODEL
_SONNET = config.SONNET_MODEL

_doc_reader = load_prompt("document_reader.j2")
_task_recognizer = load_prompt("task_recognizer.j2")
_worker = load_prompt("worker.j2")
_summarizer = load_prompt("summarizer.j2")
_follow_up_agent = load_prompt("follow_up_agent.j2")

_DOC_READER_TOOLS = [TOOL_EXTRACT_PAGE]
DOCUMENT_READER = SpecialistDef(
    description="Extracts structured metadata (header, summary, entities, fields) from a single document page",
    prompt=_doc_reader.system,
    model=_HAIKU,
    mcp_servers=_mcp(_DOC_READER_TOOLS),
    allowed_tools=_DOC_READER_TOOLS,
)

_TASK_RECOGNIZER_TOOLS = [TOOL_DETECT_SUBREQUESTS, TOOL_VALIDATE_REQUEST]
TASK_RECOGNIZER = SpecialistDef(
    description="Identifies Ercole pension fund module requests from aggregated page metadata",
    prompt=_task_recognizer.system,
    model=_HAIKU,
    mcp_servers=_mcp(_TASK_RECOGNIZER_TOOLS),
    allowed_tools=_TASK_RECOGNIZER_TOOLS,
)

_WORKER_TOOLS = [TOOL_VALIDATE_REQUEST, TOOL_VALIDATE_REQUESTS]
WORKER = SpecialistDef(
    description="Assigns document pages to identified requests (page allocator)",
    prompt=_worker.system,
    model=_HAIKU,
    mcp_servers=_mcp(_WORKER_TOOLS),
    allowed_tools=_WORKER_TOOLS,
)

_SUMMARIZER_TOOLS = [TOOL_VALIDATE_REQUESTS, TOOL_PERSIST_RESULT, TOOL_PERSIST_RESULTS]
SUMMARIZER = SpecialistDef(
    description="Generates a structured markdown report from extracted requests and page assignments",
    prompt=_summarizer.system,
    model=_HAIKU,
    mcp_servers=_mcp(_SUMMARIZER_TOOLS),
    allowed_tools=_SUMMARIZER_TOOLS,
)

FOLLOW_UP_AGENT = SpecialistDef(
    description="Answers follow-up questions about a previously processed Ercole document",
    prompt=_follow_up_agent.system,
    model=_HAIKU,
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
