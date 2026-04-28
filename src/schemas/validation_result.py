"""TypedDict schema for subrequest validation results."""

from typing import TypedDict


class ValidationResult(TypedDict, total=False):
    """Structured output of validate_request / validate_requests.

    Required fields (total=False allows optional extras):
        is_valid               -- True only when no hard issues are found.
        issues                 -- List of blocking problem descriptions (empty when valid).
        human_review_required  -- True when the request is structurally weak or ambiguous.

    Optional fields (present only when relevant):
        warnings               -- Non-blocking observations (unsorted pages, short description…).
        normalized_request     -- Copy of the input with pages sorted and deduplicated.
                                  Included only when is_valid is True.
    """

    is_valid: bool
    issues: list[str]
    human_review_required: bool
    warnings: list[str]
    normalized_request: dict
