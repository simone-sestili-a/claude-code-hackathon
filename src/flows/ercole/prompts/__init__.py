"""Prompt loader for Ercole specialists — thin wrapper around src.utils.PromptTemplate."""

from __future__ import annotations

from pathlib import Path

from src.utils import PromptTemplate

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> PromptTemplate:
    """Load a .j2 prompt file from the Ercole prompts directory."""
    return PromptTemplate.from_path(_PROMPTS_DIR / name)
