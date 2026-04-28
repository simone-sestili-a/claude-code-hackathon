"""Jinja2 prompt template loader for Ercole specialists.

Each .j2 file contains two sections separated by a marker comment:
  - Everything before {# === USER INPUT BELOW === #} → system prompt (static)
  - Everything after → user message template (rendered per-call with {{ variable }} placeholders)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

_SPLIT_MARKER = "{# === USER INPUT BELOW === #}"
_ENV = jinja2.Environment(undefined=jinja2.StrictUndefined, keep_trailing_newline=True)


class PromptTemplate:
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
        return _ENV.from_string(self._user_template).render(**kwargs)

    @classmethod
    def load(cls, name: str) -> "PromptTemplate":
        path = Path(__file__).parent / name
        return cls(path)
