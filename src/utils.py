"""Shared utilities for the document-processing specialist pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jinja2
import yaml
from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query

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


@dataclass
class SpecialistDef:
    description: str
    prompt: str
    model: str
    disallowed_tools: list[str] = field(default_factory=list)


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


async def run_specialist(
    spec: SpecialistDef, prompt: str, timeout_seconds: int = 90
) -> str | None:
    options = ClaudeCodeOptions(
        model=spec.model,
        system_prompt=spec.prompt,
        permission_mode="bypassPermissions",
        max_turns=5,
    )
    result: str | None = None
    async with asyncio.timeout(timeout_seconds):
        async for msg in query(prompt=prompt, options=options):
            if isinstance(msg, ResultMessage):
                result = msg.result if msg.subtype == "success" else None
    return result
