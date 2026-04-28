"""Tests for validate_request and validate_requests."""

import pytest

from src.tools.validation_tools import validate_request, validate_requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_valid() -> dict:
    """Return the smallest possible fully-valid subrequest."""
    return {
        "request_id": "REQ-001",
        "pages": [1, 2, 3],
        "description": "Replace laptop hard drive",
        "data": {"user": "alice", "asset_id": "LT-4242"},
    }


# ---------------------------------------------------------------------------
# Valid input
# ---------------------------------------------------------------------------


class TestValidInput:
    def test_fully_valid_request(self):
        result = validate_request(_minimal_valid())
        assert result["is_valid"] is True
        assert result["issues"] == []
        assert result["human_review_required"] is False

    def test_valid_includes_normalized_request(self):
        result = validate_request(_minimal_valid())
        assert "normalized_request" in result

    def test_normalized_pages_sorted_and_deduped(self):
        req = {**_minimal_valid(), "pages": [3, 1, 2, 2]}
        result = validate_request(req)
        # Unsorted/dup pages → warnings → human_review_required
        assert result["is_valid"] is True
        assert result["normalized_request"]["pages"] == [1, 2, 3]

    def test_data_can_be_a_list(self):
        req = {**_minimal_valid(), "data": [1, 2, 3]}
        result = validate_request(req)
        assert result["is_valid"] is True

    def test_single_page_is_valid(self):
        req = {**_minimal_valid(), "pages": [5]}
        result = validate_request(req)
        assert result["is_valid"] is True

    def test_no_warnings_on_clean_input(self):
        result = validate_request(_minimal_valid())
        assert "warnings" not in result


# ---------------------------------------------------------------------------
# Hard failures (is_valid = False)
# ---------------------------------------------------------------------------


class TestHardFailures:
    def test_missing_request_id(self):
        req = _minimal_valid()
        del req["request_id"]
        result = validate_request(req)
        assert result["is_valid"] is False
        assert any("request_id" in i for i in result["issues"])

    def test_empty_request_id(self):
        req = {**_minimal_valid(), "request_id": "   "}
        result = validate_request(req)
        assert result["is_valid"] is False
        assert any("empty" in i for i in result["issues"])

    def test_non_string_request_id(self):
        req = {**_minimal_valid(), "request_id": 123}
        result = validate_request(req)
        assert result["is_valid"] is False

    def test_missing_pages(self):
        req = _minimal_valid()
        del req["pages"]
        result = validate_request(req)
        assert result["is_valid"] is False
        assert any("pages" in i for i in result["issues"])

    def test_empty_pages_list(self):
        req = {**_minimal_valid(), "pages": []}
        result = validate_request(req)
        assert result["is_valid"] is False

    def test_pages_not_a_list(self):
        req = {**_minimal_valid(), "pages": "1,2,3"}
        result = validate_request(req)
        assert result["is_valid"] is False

    def test_pages_contains_non_integers(self):
        req = {**_minimal_valid(), "pages": [1, "two", 3]}
        result = validate_request(req)
        assert result["is_valid"] is False
        assert any("non-integer" in i for i in result["issues"])

    def test_pages_rejects_booleans(self):
        # bool is a subclass of int in Python; we treat it as invalid
        req = {**_minimal_valid(), "pages": [1, True, 3]}
        result = validate_request(req)
        assert result["is_valid"] is False

    def test_missing_description(self):
        req = _minimal_valid()
        del req["description"]
        result = validate_request(req)
        assert result["is_valid"] is False

    def test_empty_description(self):
        req = {**_minimal_valid(), "description": "   "}
        result = validate_request(req)
        assert result["is_valid"] is False

    def test_missing_data(self):
        req = _minimal_valid()
        del req["data"]
        result = validate_request(req)
        assert result["is_valid"] is False

    def test_non_serializable_data(self):
        req = {**_minimal_valid(), "data": {"fn": lambda: None}}
        result = validate_request(req)
        assert result["is_valid"] is False
        assert any("JSON-serializable" in i for i in result["issues"])

    def test_multiple_issues_reported(self):
        result = validate_request({})
        assert len(result["issues"]) >= 3  # request_id, pages, description, data all missing

    def test_invalid_has_no_normalized_request(self):
        req = _minimal_valid()
        del req["request_id"]
        result = validate_request(req)
        assert "normalized_request" not in result


# ---------------------------------------------------------------------------
# Warnings / human_review_required
# ---------------------------------------------------------------------------


class TestWarningsAndHumanReview:
    def test_null_data_triggers_warning(self):
        req = {**_minimal_valid(), "data": None}
        result = validate_request(req)
        assert result["is_valid"] is True
        assert result["human_review_required"] is True
        assert any("null" in w for w in result["warnings"])

    def test_empty_dict_data_triggers_warning(self):
        req = {**_minimal_valid(), "data": {}}
        result = validate_request(req)
        assert result["is_valid"] is True
        assert result["human_review_required"] is True

    def test_empty_list_data_triggers_warning(self):
        req = {**_minimal_valid(), "data": []}
        result = validate_request(req)
        assert result["is_valid"] is True
        assert result["human_review_required"] is True

    def test_short_description_triggers_warning(self):
        req = {**_minimal_valid(), "description": "Fix it"}
        result = validate_request(req)
        assert result["is_valid"] is True
        assert result["human_review_required"] is True
        assert any("short" in w for w in result["warnings"])

    def test_duplicate_pages_trigger_warning(self):
        req = {**_minimal_valid(), "pages": [1, 2, 2, 3]}
        result = validate_request(req)
        assert result["is_valid"] is True
        assert result["human_review_required"] is True
        assert any("duplicate" in w for w in result["warnings"])

    def test_unsorted_pages_trigger_warning(self):
        req = {**_minimal_valid(), "pages": [3, 1, 2]}
        result = validate_request(req)
        assert result["is_valid"] is True
        assert result["human_review_required"] is True
        assert any("sorted" in w for w in result["warnings"])

    def test_human_review_false_on_clean_valid_request(self):
        result = validate_request(_minimal_valid())
        assert result["human_review_required"] is False


# ---------------------------------------------------------------------------
# validate_requests (batch)
# ---------------------------------------------------------------------------


class TestValidateRequests:
    def test_empty_list_returns_empty(self):
        assert validate_requests([]) == []

    def test_returns_one_result_per_input(self):
        reqs = [_minimal_valid(), _minimal_valid(), {}]
        results = validate_requests(reqs)
        assert len(results) == 3

    def test_order_preserved(self):
        req_good = _minimal_valid()
        req_bad = {}
        results = validate_requests([req_good, req_bad])
        assert results[0]["is_valid"] is True
        assert results[1]["is_valid"] is False

    def test_each_result_is_json_serializable(self):
        import json
        results = validate_requests([_minimal_valid(), {}])
        # Should not raise
        json.dumps(results)


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------


class TestOutputContract:
    def test_result_always_has_required_keys(self):
        for req in [_minimal_valid(), {}]:
            result = validate_request(req)
            assert "is_valid" in result
            assert "issues" in result
            assert "human_review_required" in result

    def test_issues_is_always_a_list(self):
        for req in [_minimal_valid(), {}]:
            assert isinstance(validate_request(req)["issues"], list)

    def test_result_is_json_serializable(self):
        import json
        for req in [_minimal_valid(), {}, {**_minimal_valid(), "data": {}}]:
            json.dumps(validate_request(req))  # must not raise
