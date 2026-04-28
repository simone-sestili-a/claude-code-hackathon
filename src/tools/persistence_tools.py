"""Persistence utility for IntakeAI.

Writes validated structured requests to disk as UTF-8 JSON.
Does not validate business logic, detect subrequests, extract page data, or render PDFs.
"""

import json
from pathlib import Path


def _ensure_dir(output_path: str) -> None:
    """Create the parent directory of output_path if it does not exist."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)


def persist_request(request: dict, output_path: str) -> None:
    """Persist a single validated structured request to disk as JSON.

    The caller is responsible for serializing Pydantic models before calling
    (e.g. ``NormalizedRequest.model_dump()`` or ``TriageResult.model_dump()``).
    No fields are dropped or transformed.

    Args:
        request: Validated structured request as a plain dict.
        output_path: File path for the JSON output (parent dirs are created).

    Raises:
        ValueError: If ``request`` is not a dict, or contains non-serializable values.
        OSError: If the output path cannot be written.
    """
    if not isinstance(request, dict):
        raise ValueError(f"request must be a dict, got {type(request).__name__}")

    _ensure_dir(output_path)

    try:
        payload = json.dumps(request, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"request is not JSON-serializable: {exc}") from exc

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(payload)
    except OSError as exc:
        raise OSError(f"Failed to write to {output_path!r}: {exc}") from exc


def persist_requests(requests: list[dict], output_path: str) -> None:
    """Persist an ordered list of validated structured requests to disk as JSON.

    List order is preserved. No fields are dropped or transformed.
    An empty list writes an empty JSON array.

    Args:
        requests: Ordered list of validated structured requests as plain dicts.
        output_path: File path for the JSON output (parent dirs are created).

    Raises:
        ValueError: If ``requests`` is not a list of dicts, or contains
            non-serializable values.
        OSError: If the output path cannot be written.
    """
    if not isinstance(requests, list):
        raise ValueError(f"requests must be a list, got {type(requests).__name__}")

    for i, item in enumerate(requests):
        if not isinstance(item, dict):
            raise ValueError(f"requests[{i}] must be a dict, got {type(item).__name__}")

    _ensure_dir(output_path)

    try:
        payload = json.dumps(requests, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"requests are not JSON-serializable: {exc}") from exc

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(payload)
    except OSError as exc:
        raise OSError(f"Failed to write to {output_path!r}: {exc}") from exc
