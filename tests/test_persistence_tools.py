"""Tests for src/tools/persistence_tools."""

import json
import os
from pathlib import Path

import pytest

from src.tools.persistence_tools import persist_request, persist_requests


# -- Fixtures ------------------------------------------------------------------

_NORMALIZED_REQUEST: dict = {
    "request_id": "abc-0001",
    "channel": "email",
    "subject": "VPN access issue",
    "body": "My laptop won't connect to VPN since this morning.",
    "user_id": "jdoe",
    "account_status": "ACTIVE",
    "is_duplicate": False,
    "duplicate_of": None,
}

_TRIAGE_RESULT: dict = {
    "request_id": "abc-0001",
    "category": "INFRA",
    "priority": "P3",
    "confidence": 0.92,
    "impact_bucket": "LOW",
    "target_queue": "infra-ops",
    "escalate": False,
    "escalation_reason": None,
    "auto_resolved": False,
    "auto_resolve_action": None,
    "reasoning_summary": "VPN connectivity issue, standard routing.",
    "draft_response": "We have received your request and are investigating.",
    "retry_count": 0,
    "audit_log_ref": "",
}

# A request that carries page-level traceability (page_number must survive round-trip).
_REQUEST_WITH_PAGES: dict = {
    **_NORMALIZED_REQUEST,
    "pages": [
        {"page_number": 1, "header": "Richiesta Accesso VPN", "entities": ["TKT-0001"]},
        {"page_number": 2, "header": "Allegati", "entities": []},
    ],
}


# -- persist_request -----------------------------------------------------------

class TestPersistRequest:
    def test_creates_file(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_request(_NORMALIZED_REQUEST, out)
        assert os.path.exists(out)

    def test_round_trip(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_request(_NORMALIZED_REQUEST, out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded == _NORMALIZED_REQUEST

    def test_creates_nested_parent_directories(self, tmp_path):
        out = str(tmp_path / "a" / "b" / "c" / "out.json")
        persist_request(_NORMALIZED_REQUEST, out)
        assert os.path.exists(out)

    def test_preserves_request_id(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_request(_NORMALIZED_REQUEST, out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded["request_id"] == "abc-0001"

    def test_preserves_all_fields(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_request(_TRIAGE_RESULT, out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert set(loaded.keys()) == set(_TRIAGE_RESULT.keys())

    def test_utf8_non_ascii_characters(self, tmp_path):
        req = {**_NORMALIZED_REQUEST, "body": "Accesso non funziona — café résumé"}
        out = str(tmp_path / "out.json")
        persist_request(req, out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded["body"] == req["body"]

    def test_non_ascii_not_escaped(self, tmp_path):
        req = {**_NORMALIZED_REQUEST, "body": "Accèss"}
        out = str(tmp_path / "out.json")
        persist_request(req, out)
        raw = Path(out).read_text(encoding="utf-8")
        # ensure_ascii=False: characters appear literally, not as \uXXXX
        assert "Accèss" in raw

    def test_raises_on_non_dict(self, tmp_path):
        out = str(tmp_path / "out.json")
        with pytest.raises(ValueError, match="must be a dict"):
            persist_request(["not", "a", "dict"], out)  # type: ignore[arg-type]

    def test_raises_on_non_serializable(self, tmp_path):
        out = str(tmp_path / "out.json")
        with pytest.raises(ValueError, match="not JSON-serializable"):
            persist_request({"bad": object()}, out)


# -- persist_requests ----------------------------------------------------------

class TestPersistRequests:
    def test_creates_file(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_requests([_NORMALIZED_REQUEST], out)
        assert os.path.exists(out)

    def test_output_is_json_array(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_requests([_NORMALIZED_REQUEST], out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert isinstance(loaded, list)

    def test_round_trip_single(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_requests([_NORMALIZED_REQUEST], out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded == [_NORMALIZED_REQUEST]

    def test_round_trip_multiple(self, tmp_path):
        reqs = [_NORMALIZED_REQUEST, _TRIAGE_RESULT]
        out = str(tmp_path / "out.json")
        persist_requests(reqs, out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded == reqs

    def test_preserves_list_order(self, tmp_path):
        reqs = [{**_NORMALIZED_REQUEST, "request_id": f"req-{i}"} for i in range(5)]
        out = str(tmp_path / "out.json")
        persist_requests(reqs, out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert [r["request_id"] for r in loaded] == [f"req-{i}" for i in range(5)]

    def test_empty_list_writes_empty_array(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_requests([], out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded == []

    def test_creates_nested_parent_directories(self, tmp_path):
        out = str(tmp_path / "x" / "y" / "out.json")
        persist_requests([_NORMALIZED_REQUEST], out)
        assert os.path.exists(out)

    def test_preserves_page_traceability(self, tmp_path):
        out = str(tmp_path / "out.json")
        persist_requests([_REQUEST_WITH_PAGES], out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        pages = loaded[0]["pages"]
        assert pages[0]["page_number"] == 1
        assert pages[1]["page_number"] == 2

    def test_preserves_request_id_across_all_items(self, tmp_path):
        reqs = [{**_NORMALIZED_REQUEST, "request_id": f"id-{i}"} for i in range(3)]
        out = str(tmp_path / "out.json")
        persist_requests(reqs, out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        for i, item in enumerate(loaded):
            assert item["request_id"] == f"id-{i}"

    def test_raises_on_non_list(self, tmp_path):
        out = str(tmp_path / "out.json")
        with pytest.raises(ValueError, match="must be a list"):
            persist_requests(_NORMALIZED_REQUEST, out)  # type: ignore[arg-type]

    def test_raises_on_non_dict_element(self, tmp_path):
        out = str(tmp_path / "out.json")
        with pytest.raises(ValueError, match=r"requests\[1\] must be a dict"):
            persist_requests([_NORMALIZED_REQUEST, "not-a-dict"], out)  # type: ignore[arg-type]

    def test_raises_on_non_serializable_element(self, tmp_path):
        out = str(tmp_path / "out.json")
        with pytest.raises(ValueError, match="not JSON-serializable"):
            persist_requests([{"bad": object()}], out)

