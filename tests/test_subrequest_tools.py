"""Tests for detect_subrequests — grouping/detection only, no LLM, no I/O."""

import json

import pytest

from src.tools.subrequest_tools import detect_subrequests

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PAGE_VPN_1 = {
    "page_number": 1,
    "header": "IT Access Request",
    "summary": "New employee Mario Rossi needs VPN access.",
    "entities": ["Mario Rossi", "VPN-001"],
    "filled_fields": [
        {"field_name": "nome", "field_value": "Mario Rossi"},
        {"field_name": "reparto", "field_value": "IT"},
    ],
}

PAGE_VPN_2 = {
    "page_number": 2,
    "header": "IT Access Request (continued)",
    "summary": "Additional details and approval signatures.",
    "entities": ["Mario Rossi", "IT-2024-001"],
    "filled_fields": [
        {"field_name": "responsabile", "field_value": "Luca Verdi"},
    ],
}

PAGE_HARDWARE = {
    "page_number": 3,
    "header": "Hardware Request",
    "summary": "Giulia Bianchi requests a new laptop.",
    "entities": ["Giulia Bianchi", "ASSET-9987"],
    "filled_fields": [
        {"field_name": "nome", "field_value": "Giulia Bianchi"},
        {"field_name": "modello", "field_value": "MacBook Pro 14"},
    ],
}

PAGE_NO_OVERLAP = {
    "page_number": 4,
    "header": "Password Reset",
    "summary": "Unrelated standalone request.",
    "entities": [],
    "filled_fields": [],
}


# ---------------------------------------------------------------------------
# Basic grouping
# ---------------------------------------------------------------------------


def test_single_page_returns_one_subrequest():
    result = detect_subrequests([PAGE_VPN_1])
    assert len(result) == 1
    assert result[0]["request_id"] == "R1"
    assert result[0]["pages"] == [1]


def test_two_pages_sharing_entity_grouped_together():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2])
    assert len(result) == 1
    assert result[0]["pages"] == [1, 2]


def test_unrelated_page_starts_new_group():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2, PAGE_HARDWARE])
    assert len(result) == 2
    assert result[0]["pages"] == [1, 2]
    assert result[1]["pages"] == [3]


def test_page_with_no_overlap_is_isolated():
    result = detect_subrequests([PAGE_VPN_1, PAGE_NO_OVERLAP])
    assert len(result) == 2
    assert result[1]["pages"] == [4]


def test_shared_field_value_triggers_grouping():
    # Two pages with no entity overlap but sharing the same (field_name, field_value)
    # pair should be grouped — this indicates they reference the same data record.
    a = {
        "page_number": 1,
        "header": "Form A",
        "summary": "Alpha.",
        "entities": [],
        "filled_fields": [{"field_name": "codice", "field_value": "X1"}],
    }
    b = {
        "page_number": 2,
        "header": "Form A continued",
        "summary": "Alpha continued.",
        "entities": [],
        "filled_fields": [{"field_name": "codice", "field_value": "X1"}],
    }
    result = detect_subrequests([a, b])
    assert len(result) == 1
    assert result[0]["pages"] == [1, 2]


def test_shared_field_name_only_does_not_group():
    # Two pages sharing only a field NAME (e.g. both have "nome") but with
    # different values and no entity overlap must NOT be merged — field names
    # like "nome" are schema-structural and appear in every form.
    a = {
        "page_number": 1,
        "header": "VPN Request",
        "summary": "",
        "entities": [],
        "filled_fields": [{"field_name": "nome", "field_value": "Mario Rossi"}],
    }
    b = {
        "page_number": 2,
        "header": "Hardware Request",
        "summary": "",
        "entities": [],
        "filled_fields": [{"field_name": "nome", "field_value": "Giulia Bianchi"}],
    }
    result = detect_subrequests([a, b])
    assert len(result) == 2


# ---------------------------------------------------------------------------
# request_id stability and order
# ---------------------------------------------------------------------------


def test_request_ids_are_r1_r2():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2, PAGE_HARDWARE])
    assert [r["request_id"] for r in result] == ["R1", "R2"]


def test_pages_always_sorted_within_subrequest():
    reversed_input = [PAGE_HARDWARE, PAGE_VPN_2, PAGE_VPN_1]
    result = detect_subrequests(reversed_input)
    for sr in result:
        assert sr["pages"] == sorted(sr["pages"])


# ---------------------------------------------------------------------------
# Input formats
# ---------------------------------------------------------------------------


def test_dict_int_input_accepted():
    dict_input: dict[int, dict] = {1: PAGE_VPN_1, 3: PAGE_HARDWARE}
    result = detect_subrequests(dict_input)
    assert len(result) == 2


def test_empty_list_returns_empty():
    assert detect_subrequests([]) == []


def test_empty_dict_returns_empty():
    assert detect_subrequests({}) == []


# ---------------------------------------------------------------------------
# Output shape and JSON-serializability
# ---------------------------------------------------------------------------


def test_output_is_json_serializable():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2, PAGE_HARDWARE])
    json.dumps(result)  # must not raise


def test_required_fields_present():
    result = detect_subrequests([PAGE_VPN_1])
    sr = result[0]
    assert "request_id" in sr
    assert "pages" in sr
    assert "description" in sr
    assert "data" in sr


def test_data_subfields_present():
    result = detect_subrequests([PAGE_VPN_1])
    data = result[0]["data"]
    assert "entities" in data
    assert "filled_fields" in data
    assert "grouping_note" in data


def test_pages_non_empty():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2, PAGE_HARDWARE])
    for sr in result:
        assert len(sr["pages"]) >= 1


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------


def test_entities_deduplicated_across_pages():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2])
    entities = result[0]["data"]["entities"]
    assert entities.count("Mario Rossi") == 1


def test_all_entities_from_group_included():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2])
    entities = result[0]["data"]["entities"]
    assert "VPN-001" in entities
    assert "IT-2024-001" in entities


def test_filled_fields_merged_last_value_wins():
    a = {
        "page_number": 1,
        "header": "Form",
        "summary": "",
        "entities": ["shared-entity"],
        "filled_fields": [{"field_name": "stato", "field_value": "bozza"}],
    }
    b = {
        "page_number": 2,
        "header": "Form",
        "summary": "",
        "entities": ["shared-entity"],
        "filled_fields": [{"field_name": "stato", "field_value": "approvato"}],
    }
    result = detect_subrequests([a, b])
    fields = {f["field_name"]: f["field_value"] for f in result[0]["data"]["filled_fields"]}
    assert fields["stato"] == "approvato"


def test_description_contains_header():
    result = detect_subrequests([PAGE_VPN_1])
    assert "IT Access Request" in result[0]["description"]


def test_single_page_grouping_note():
    result = detect_subrequests([PAGE_VPN_1])
    assert "Single-page" in result[0]["data"]["grouping_note"]


def test_multi_page_grouping_note_mentions_count():
    result = detect_subrequests([PAGE_VPN_1, PAGE_VPN_2])
    note = result[0]["data"]["grouping_note"]
    assert "2 pages" in note


# ---------------------------------------------------------------------------
# rules parameter
# ---------------------------------------------------------------------------


def test_rules_none_accepted():
    result = detect_subrequests([PAGE_VPN_1], rules=None)
    assert len(result) == 1


def test_rules_string_accepted_and_ignored():
    result = detect_subrequests([PAGE_VPN_1], rules="group by subject")
    assert len(result) == 1


def test_rules_max_pages_per_group_caps_group_size():
    # VPN_1 and VPN_2 share "Mario Rossi" — would normally be one group.
    # With max_pages_per_group=1, each page must be its own subrequest.
    result = detect_subrequests(
        [PAGE_VPN_1, PAGE_VPN_2, PAGE_HARDWARE],
        rules={"max_pages_per_group": 1},
    )
    assert len(result) == 3
    for sr in result:
        assert len(sr["pages"]) == 1


def test_rules_unknown_keys_ignored():
    result = detect_subrequests([PAGE_VPN_1], rules={"unknown_key": 99})
    assert len(result) == 1
