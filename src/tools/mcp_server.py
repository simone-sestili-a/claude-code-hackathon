"""In-process MCP server exposing document processing tools to specialist agents.

Tools wrapped here are all deterministic (no LLM). Specialists can call them to
get a pre-extraction baseline, group pages into subrequests, validate outputs,
or persist final results to disk.

Usage:
    from src.tools.mcp_server import build_document_tools_server, DOCUMENT_TOOL_NAMES

    server = build_document_tools_server()
    # Then pass: ClaudeCodeOptions(mcp_servers={"document_tools": server}, allowed_tools=[...])
"""

from __future__ import annotations

import json
from typing import Any

from claude_code_sdk import create_sdk_mcp_server, tool

from src.tools.extraction_tools import extract_page as _extract_page
from src.tools.persistence_tools import persist_request as _persist_request
from src.tools.persistence_tools import persist_requests as _persist_requests
from src.tools.subrequest_tools import detect_subrequests as _detect_subrequests
from src.tools.validation_tools import validate_request as _validate_request
from src.tools.validation_tools import validate_requests as _validate_requests


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


@tool(
    "extract_page",
    (
        "Deterministically extract structured information (header, summary, entities, "
        "filled fields) from a single page's plain text. No LLM involved. "
        "Returns a JSON object with keys: page_number, header, summary, entities, filled_fields."
    ),
    {"page_text": str, "page_number": int},
)
async def mcp_extract_page(args: dict[str, Any]) -> dict[str, Any]:
    result = _extract_page(str(args["page_text"]), int(args["page_number"]))
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


@tool(
    "detect_subrequests",
    (
        "Group page extraction results into subrequests based on shared entities and "
        "field values. Accepts a JSON array of PageExtraction dicts "
        "(each with page_number, header, summary, entities, filled_fields). "
        "Returns a JSON array of subrequest dicts with request_id, pages, description, data."
    ),
    {"page_summaries_json": str},
)
async def mcp_detect_subrequests(args: dict[str, Any]) -> dict[str, Any]:
    pages = json.loads(args["page_summaries_json"])
    result = _detect_subrequests(pages)
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


@tool(
    "validate_request",
    (
        "Validate the structure and completeness of a single subrequest dict. "
        "Expects a JSON object with keys: request_id, pages, description, data. "
        "Returns a ValidationResult JSON with is_valid, issues, warnings, "
        "human_review_required, and optionally normalized_request."
    ),
    {"request_json": str},
)
async def mcp_validate_request(args: dict[str, Any]) -> dict[str, Any]:
    request = json.loads(args["request_json"])
    result = _validate_request(request)
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


@tool(
    "validate_requests",
    (
        "Validate a list of subrequest dicts. "
        "Accepts a JSON array of request dicts (same schema as validate_request). "
        "Returns a JSON array of ValidationResult objects, one per input request."
    ),
    {"requests_json": str},
)
async def mcp_validate_requests(args: dict[str, Any]) -> dict[str, Any]:
    requests = json.loads(args["requests_json"])
    results = _validate_requests(requests)
    return {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False)}]}


@tool(
    "persist_result",
    (
        "Write a validated structured result to disk as UTF-8 JSON. "
        "Use for saving the final structured output of a processing step. "
        "Accepts result_json (a JSON object string) and output_path (destination file path). "
        "Parent directories are created automatically."
    ),
    {"result_json": str, "output_path": str},
)
async def mcp_persist_result(args: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(args["result_json"])
    _persist_request(result, str(args["output_path"]))
    return {"content": [{"type": "text", "text": f"Saved to {args['output_path']}"}]}


@tool(
    "persist_results",
    (
        "Write an ordered list of validated structured results to disk as a JSON array. "
        "Accepts results_json (a JSON array string) and output_path (destination file path). "
        "Parent directories are created automatically."
    ),
    {"results_json": str, "output_path": str},
)
async def mcp_persist_results(args: dict[str, Any]) -> dict[str, Any]:
    results = json.loads(args["results_json"])
    _persist_requests(results, str(args["output_path"]))
    return {"content": [{"type": "text", "text": f"Saved {len(results)} result(s) to {args['output_path']}"}]}


# ---------------------------------------------------------------------------
# Tool name constants — used by specialists to declare their allowed_tools
# ---------------------------------------------------------------------------

TOOL_EXTRACT_PAGE = "extract_page"
TOOL_DETECT_SUBREQUESTS = "detect_subrequests"
TOOL_VALIDATE_REQUEST = "validate_request"
TOOL_VALIDATE_REQUESTS = "validate_requests"
TOOL_PERSIST_RESULT = "persist_result"
TOOL_PERSIST_RESULTS = "persist_results"

ALL_TOOL_NAMES: list[str] = [
    TOOL_EXTRACT_PAGE,
    TOOL_DETECT_SUBREQUESTS,
    TOOL_VALIDATE_REQUEST,
    TOOL_VALIDATE_REQUESTS,
    TOOL_PERSIST_RESULT,
    TOOL_PERSIST_RESULTS,
]

_ALL_TOOLS = [
    mcp_extract_page,
    mcp_detect_subrequests,
    mcp_validate_request,
    mcp_validate_requests,
    mcp_persist_result,
    mcp_persist_results,
]

MCP_SERVER_NAME = "document_tools"


def build_document_tools_server():
    """Create an in-process MCP server with all document processing tools."""
    return create_sdk_mcp_server(MCP_SERVER_NAME, tools=_ALL_TOOLS)
