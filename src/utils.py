"""Shared utilities for the document-processing specialist pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic
import jinja2
import yaml

import src.config as config  # ensures ANTHROPIC_API_KEY mapping runs at import time

_JINJA_ENV = jinja2.Environment(
    undefined=jinja2.StrictUndefined,
    keep_trailing_newline=True,
)

_SPLIT_MARKER = "{# === USER INPUT BELOW === #}"


class PromptTemplate:
    """Loads a .j2 file and exposes system prompt + per-call user-message rendering.

    The file is split at {# === USER INPUT BELOW === #} (a Jinja2 comment that
    renders to nothing, so it acts as a pure marker before rendering):
      - Everything before the marker → system prompt (static, loaded at import time)
      - Everything after → user message template (rendered per-call via Jinja2)
    """

    def __init__(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        if _SPLIT_MARKER in text:
            system_part, user_part = text.split(_SPLIT_MARKER, 1)
            self.system = system_part.strip()
            self._user_template = user_part.strip()
        else:
            self.system = text.strip()
            self._user_template = ""

    def render_user(self, **kwargs: Any) -> str:
        if not self._user_template:
            return ""
        return _JINJA_ENV.from_string(self._user_template).render(**kwargs)

    @classmethod
    def from_path(cls, path: Path) -> "PromptTemplate":
        return cls(path)

logger = logging.getLogger(__name__)


def _default_model() -> str:
    return config.DEFAULT_MODEL


@dataclass
class SpecialistDef:
    description: str
    prompt: str
    model: str = field(default_factory=_default_model)
    disallowed_tools: list[str] = field(default_factory=list)
    # MCP server config — {server_name: McpSdkServerConfig} returned by build_document_tools_server()
    mcp_servers: dict = field(default_factory=dict)
    # Explicit list of MCP tool names this specialist may call (empty = no restriction)
    allowed_tools: list[str] = field(default_factory=list)


def parse_json_result(text: str | None) -> dict[str, Any]:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        inner = lines[1:] if len(lines) > 1 else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed: %s", exc)
        return {}


def parse_yaml_result(text: str | None) -> dict[str, Any]:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        inner = lines[1:] if len(lines) > 1 else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()
    try:
        result = yaml.safe_load(text)
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError as exc:
        logger.warning("YAML parse failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Anthropic client (lazy singleton)
# ---------------------------------------------------------------------------

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        import os
        _client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL") or None,
        )
    return _client


# ---------------------------------------------------------------------------
# Local tool registry — maps tool names to the underlying Python functions
# ---------------------------------------------------------------------------

_TOOL_REGISTRY: dict[str, Any] = {}

_TOOL_DEFINITIONS: dict[str, dict] = {
    "extract_page": {
        "name": "extract_page",
        "description": (
            "Deterministically extract structured information (header, summary, entities, "
            "filled fields) from a single page's plain text. No LLM involved. "
            "Returns a JSON object with keys: page_number, header, summary, entities, filled_fields."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page_text": {"type": "string"},
                "page_number": {"type": "integer"},
            },
            "required": ["page_text", "page_number"],
        },
    },
    "detect_subrequests": {
        "name": "detect_subrequests",
        "description": (
            "Group page extraction results into subrequests based on shared entities and "
            "field values. Accepts a JSON array of PageExtraction dicts. "
            "Returns a JSON array of subrequest dicts with request_id, pages, description, data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page_summaries_json": {"type": "string"},
            },
            "required": ["page_summaries_json"],
        },
    },
    "validate_request": {
        "name": "validate_request",
        "description": (
            "Validate the structure and completeness of a single subrequest dict. "
            "Expects a JSON object with keys: request_id, pages, description, data. "
            "Returns a ValidationResult JSON with is_valid, issues, warnings, "
            "human_review_required, and optionally normalized_request."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "request_json": {"type": "string"},
            },
            "required": ["request_json"],
        },
    },
    "validate_requests": {
        "name": "validate_requests",
        "description": (
            "Validate a list of subrequest dicts. "
            "Accepts a JSON array of request dicts. "
            "Returns a JSON array of ValidationResult objects, one per input request."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "requests_json": {"type": "string"},
            },
            "required": ["requests_json"],
        },
    },
    "persist_result": {
        "name": "persist_result",
        "description": (
            "Write a validated structured result to disk as UTF-8 JSON. "
            "Accepts result_json (a JSON object string) and output_path (destination file path)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "result_json": {"type": "string"},
                "output_path": {"type": "string"},
            },
            "required": ["result_json", "output_path"],
        },
    },
    "persist_results": {
        "name": "persist_results",
        "description": (
            "Write an ordered list of validated structured results to disk as a JSON array. "
            "Accepts results_json (a JSON array string) and output_path (destination file path)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "results_json": {"type": "string"},
                "output_path": {"type": "string"},
            },
            "required": ["results_json", "output_path"],
        },
    },
}


def _ensure_tool_registry() -> None:
    """Lazily populate the tool registry from local tool implementations."""
    if _TOOL_REGISTRY:
        return
    from src.tools.extraction_tools import extract_page
    from src.tools.subrequest_tools import detect_subrequests
    from src.tools.validation_tools import validate_request, validate_requests
    from src.tools.persistence_tools import persist_request, persist_requests

    def _wrap_extract_page(args: dict) -> str:
        result = extract_page(str(args["page_text"]), int(args["page_number"]))
        return json.dumps(result, ensure_ascii=False)

    def _wrap_detect_subrequests(args: dict) -> str:
        pages = json.loads(args["page_summaries_json"])
        return json.dumps(detect_subrequests(pages), ensure_ascii=False)

    def _wrap_validate_request(args: dict) -> str:
        request = json.loads(args["request_json"])
        return json.dumps(validate_request(request), ensure_ascii=False)

    def _wrap_validate_requests(args: dict) -> str:
        reqs = json.loads(args["requests_json"])
        return json.dumps(validate_requests(reqs), ensure_ascii=False)

    def _wrap_persist_result(args: dict) -> str:
        result = json.loads(args["result_json"])
        persist_request(result, str(args["output_path"]))
        return f"Saved to {args['output_path']}"

    def _wrap_persist_results(args: dict) -> str:
        results = json.loads(args["results_json"])
        persist_requests(results, str(args["output_path"]))
        return f"Saved {len(results)} result(s) to {args['output_path']}"

    _TOOL_REGISTRY["extract_page"] = _wrap_extract_page
    _TOOL_REGISTRY["detect_subrequests"] = _wrap_detect_subrequests
    _TOOL_REGISTRY["validate_request"] = _wrap_validate_request
    _TOOL_REGISTRY["validate_requests"] = _wrap_validate_requests
    _TOOL_REGISTRY["persist_result"] = _wrap_persist_result
    _TOOL_REGISTRY["persist_results"] = _wrap_persist_results


def _execute_tool(name: str, input_args: dict) -> str:
    """Execute a local tool by name and return the result as a string."""
    _ensure_tool_registry()
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return json.dumps({"isError": True, "error": f"Unknown tool: {name}"})
    try:
        return fn(input_args)
    except Exception as exc:
        logger.warning("Tool %s failed: %s", name, exc)
        return json.dumps({"isError": True, "error": str(exc)})


async def run_specialist(
    spec: SpecialistDef, prompt: str, timeout_seconds: int = 90
) -> str | None:
    client = _get_client()
    max_turns = 5

    # Build the tool definitions for this specialist
    tools = []
    if spec.allowed_tools:
        _ensure_tool_registry()
        for tool_name in spec.allowed_tools:
            if tool_name in _TOOL_DEFINITIONS:
                tools.append(_TOOL_DEFINITIONS[tool_name])

    messages: list[dict] = [{"role": "user", "content": prompt}]

    async with asyncio.timeout(timeout_seconds):
        for _ in range(max_turns):
            kwargs: dict[str, Any] = {
                "model": spec.model,
                "max_tokens": 4096,
                "system": spec.prompt,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools

            response = await client.messages.create(**kwargs)

            # Extract text from the response
            if response.stop_reason == "tool_use":
                # Process tool calls
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result_text = _execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        })
                messages.append({"role": "user", "content": tool_results})
                continue

            # End turn — extract final text
            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
            return "\n".join(text_parts) if text_parts else None

    return None
