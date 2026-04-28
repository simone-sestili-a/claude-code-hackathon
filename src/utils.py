"""Shared utilities for the document-processing specialist pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import yaml
from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query

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
