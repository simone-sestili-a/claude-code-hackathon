"""Structural validation for detected subrequests.

Validates completeness and basic consistency only.
Does not detect subrequests, render PDFs, extract data, or persist anything.
"""

import json
from typing import Any

from src.schemas.validation_result import ValidationResult


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_request_id(request: dict[str, Any], issues: list[str]) -> None:
    """Validate that request_id is a non-empty string."""
    value = request.get("request_id")
    if value is None:
        issues.append("request_id is missing")
    elif not isinstance(value, str):
        issues.append(f"request_id must be a string, got {type(value).__name__}")
    elif not value.strip():
        issues.append("request_id is empty")


def _check_description(
    request: dict[str, Any], issues: list[str], warnings: list[str]
) -> None:
    """Validate that description is a non-empty string."""
    value = request.get("description")
    if value is None:
        issues.append("description is missing")
    elif not isinstance(value, str):
        issues.append(f"description must be a string, got {type(value).__name__}")
    elif not value.strip():
        issues.append("description is empty")
    elif len(value.strip()) < 10:
        warnings.append("description is very short (< 10 chars); may need human review")


def _check_data(
    request: dict[str, Any], issues: list[str], warnings: list[str]
) -> None:
    """Validate that data key exists and is JSON-serializable."""
    if "data" not in request:
        issues.append("data is missing")
        return

    value = request["data"]

    if value is None:
        warnings.append("data is null; content may be incomplete")
        return

    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        issues.append(f"data is not JSON-serializable: {exc}")
        return

    if isinstance(value, (dict, list)) and len(value) == 0:
        warnings.append("data is present but empty")


def _check_pages(
    request: dict[str, Any], issues: list[str], warnings: list[str]
) -> list[int] | None:
    """Validate pages field; return the valid page list or None on hard failure."""
    value = request.get("pages")

    if value is None:
        issues.append("pages is missing")
        return None

    if not isinstance(value, list):
        issues.append(f"pages must be a list, got {type(value).__name__}")
        return None

    if len(value) == 0:
        issues.append("pages is empty")
        return None

    non_ints = [p for p in value if not isinstance(p, int) or isinstance(p, bool)]
    if non_ints:
        # Truncate report to avoid very long messages
        sample = non_ints[:5]
        issues.append(f"pages contains non-integer values: {sample}")
        return None

    if len(value) != len(set(value)):
        warnings.append("pages contains duplicate entries")

    if value != sorted(value):
        warnings.append("pages are not sorted in ascending order")

    return value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_request(request: dict[str, Any]) -> ValidationResult:
    """Validate the structure and completeness of a single detected subrequest.

    Args:
        request: A subrequest dict produced by the detection/extraction step.
                 Expected keys: request_id, pages, description, data.

    Returns:
        A ValidationResult dict with is_valid, issues, human_review_required,
        and optionally warnings and normalized_request.
    """
    issues: list[str] = []
    warnings: list[str] = []

    _check_request_id(request, issues)
    _check_description(request, issues, warnings)
    _check_data(request, issues, warnings)
    pages = _check_pages(request, issues, warnings)

    is_valid = len(issues) == 0
    human_review_required = bool(warnings) or not is_valid

    result: ValidationResult = {
        "is_valid": is_valid,
        "issues": issues,
        "human_review_required": human_review_required,
    }

    if warnings:
        result["warnings"] = warnings

    if is_valid and pages is not None:
        normalized_pages = sorted(set(pages))
        result["normalized_request"] = {**request, "pages": normalized_pages}

    return result


def validate_requests(requests: list[dict[str, Any]]) -> list[ValidationResult]:
    """Validate a list of detected subrequests.

    Args:
        requests: List of subrequest dicts.

    Returns:
        A list of ValidationResult dicts, one per input request, in the same order.
    """
    return [validate_request(r) for r in requests]
