"""Runtime configuration resolved from environment variables.

LiteLLM proxy support
---------------------
Set these env vars to route calls through a LiteLLM proxy:
  ANTHROPIC_BASE_URL          — proxy base URL
  ANTHROPIC_AUTH_TOKEN        — proxy auth token (mapped to ANTHROPIC_API_KEY)
  ANTHROPIC_DEFAULT_HAIKU_MODEL  — model alias the proxy uses for haiku (default: claude-haiku-4-5-20251001)
  ANTHROPIC_DEFAULT_SONNET_MODEL — model alias for sonnet (default: claude-sonnet-4-6)
  ANTHROPIC_DEFAULT_OPUS_MODEL   — model alias for opus (default: claude-opus-4-7)

If ANTHROPIC_AUTH_TOKEN is set and ANTHROPIC_API_KEY is not, the token is
copied into ANTHROPIC_API_KEY so that the claude CLI subprocess picks it up.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# LiteLLM proxy: map ANTHROPIC_AUTH_TOKEN → ANTHROPIC_API_KEY for the CLI
# ---------------------------------------------------------------------------

_auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
if _auth_token and not os.environ.get("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = _auth_token


def _env(key: str, default: str) -> str:
    return os.environ.get(key) or default


# ---------------------------------------------------------------------------
# Model aliases — override via env for LiteLLM proxy routing
# ---------------------------------------------------------------------------

HAIKU_MODEL: str = _env("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-haiku-4-5-20251001")
SONNET_MODEL: str = _env("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-6")
OPUS_MODEL: str = _env("ANTHROPIC_DEFAULT_OPUS_MODEL", "claude-opus-4-7")

# Default model used when no per-specialist override is set
DEFAULT_MODEL: str = HAIKU_MODEL
