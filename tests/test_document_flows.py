"""Tests for the document-processing pipeline schemas, utilities, and flow registry."""

from __future__ import annotations

import pytest

from src.schemas.document import (
    Contact,
    DocumentProcessingResponse,
    ExternalModule,
    FilledField,
    PageExtraction,
    ErcoleRequest,
    RequestPageAssignment,
)
from src.flows import get_flow, list_flows
from src.flows.base import BaseFlow
from src.utils import parse_json_result, parse_yaml_result


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_filled_field():
    f = FilledField(field_name="Nome", field_value="Mario")
    assert f.field_name == "Nome"
    assert f.field_value == "Mario"


def test_page_extraction_defaults():
    p = PageExtraction(page_number=1)
    assert p.header == ""
    assert p.entities == []
    assert p.filled_fields == []


def test_page_extraction_full():
    p = PageExtraction(
        page_number=2,
        header="MODULO DI ADESIONE A ERCOLE",
        summary="Form page for adhesion.",
        entities=["Mario Rossi"],
        filled_fields=[FilledField(field_name="Cognome", field_value="Rossi")],
    )
    assert p.page_number == 2
    assert len(p.filled_fields) == 1


def test_contact_persona_fisica():
    c = Contact(name="Mario", surname="Rossi", fiscal_code="RSSMRA80A01H501U")
    assert c.name == "Mario"
    assert c.ragione_sociale is None
    assert c.piva is None


def test_contact_entita_giuridica():
    c = Contact(ragione_sociale="Acme S.p.A.", piva="12345678901")
    assert c.ragione_sociale == "Acme S.p.A."
    assert c.name is None


def test_contact_all_none():
    c = Contact()
    assert c.name is None
    assert c.ragione_sociale is None


def test_external_module_defaults():
    m = ExternalModule(module_name="Some doc")
    assert m.page_section is None
    assert m.ercole_related is False


def test_ercole_request_defaults():
    req = ErcoleRequest(
        request_id="REQ_ERCOLE_1_1",
        page_number=1,
        header="MODULO DI ADESIONE A ERCOLE",
        confidence_score=0.92,
    )
    assert req.contacts == []
    assert req.notes is None
    assert req.external_modules == []


def test_ercole_request_full():
    req = ErcoleRequest(
        request_id="REQ_ERCOLE_1_1",
        page_number=1,
        header="MODULO DI ADESIONE A ERCOLE",
        contacts=[Contact(name="Mario", surname="Rossi")],
        notes="Mario Rossi",
        confidence_score=0.9,
    )
    assert len(req.contacts) == 1
    assert req.notes == "Mario Rossi"


def test_request_page_assignment():
    a = RequestPageAssignment(pages=[1, 2, 3], reasoning="sequential", confidence_score=90)
    assert a.pages == [1, 2, 3]
    assert a.confidence_score == 90


def test_request_page_assignment_defaults():
    a = RequestPageAssignment()
    assert a.pages == []
    assert a.reasoning == ""
    assert a.confidence_score == 0


def test_document_processing_response_defaults():
    resp = DocumentProcessingResponse(session_id="sess-001", total_pages=5)
    assert resp.requests == []
    assert resp.page_assignments == {}
    assert resp.external_modules == []
    assert resp.summary == ""


def test_document_processing_response_full():
    resp = DocumentProcessingResponse(
        session_id="sess-001",
        total_pages=3,
        requests=[
            ErcoleRequest(
                request_id="REQ_ERCOLE_1_1",
                page_number=1,
                header="MODULO DI ADESIONE A ERCOLE",
            )
        ],
        page_assignments={
            "REQ_ERCOLE_1_1": RequestPageAssignment(pages=[1, 2], confidence_score=95)
        },
        summary="Document processed successfully.",
    )
    assert len(resp.requests) == 1
    assert "REQ_ERCOLE_1_1" in resp.page_assignments


# ---------------------------------------------------------------------------
# Flow registry tests
# ---------------------------------------------------------------------------


def test_flow_registry_ercole():
    flow = get_flow("ercole")
    assert isinstance(flow, BaseFlow)
    assert flow.flow_type == "ercole"


def test_flow_registry_case_insensitive():
    flow = get_flow("ERCOLE")
    assert flow.flow_type == "ercole"


def test_flow_registry_unknown():
    with pytest.raises(ValueError, match="Unknown flow type"):
        get_flow("unknown_flow")


def test_list_flows():
    flows = list_flows()
    assert isinstance(flows, list)
    assert "ercole" in flows


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------


def test_parse_json_none():
    assert parse_json_result(None) == {}


def test_parse_json_empty():
    assert parse_json_result("") == {}


def test_parse_json_valid():
    result = parse_json_result('{"page_number": 1, "header": "Test"}')
    assert result["page_number"] == 1
    assert result["header"] == "Test"


def test_parse_json_code_fences():
    text = '```json\n{"key": "value"}\n```'
    assert parse_json_result(text) == {"key": "value"}


def test_parse_json_code_fences_no_lang():
    text = '```\n{"key": 42}\n```'
    assert parse_json_result(text) == {"key": 42}


def test_parse_json_invalid():
    assert parse_json_result("not json at all") == {}


def test_parse_yaml_none():
    assert parse_yaml_result(None) == {}


def test_parse_yaml_empty():
    assert parse_yaml_result("") == {}


def test_parse_yaml_valid():
    result = parse_yaml_result("requests:\n  - request_id: REQ_1\n")
    assert "requests" in result
    assert result["requests"][0]["request_id"] == "REQ_1"


def test_parse_yaml_code_fences():
    text = "```yaml\nkey: value\n```"
    result = parse_yaml_result(text)
    assert result == {"key": "value"}


def test_parse_yaml_invalid():
    assert parse_yaml_result("}{invalid yaml") == {}


# ---------------------------------------------------------------------------
# Specialist prompt loading
# ---------------------------------------------------------------------------


def test_prompt_template_split():
    """PromptTemplate correctly splits system and user sections."""
    from src.flows.ercole.prompts import PromptTemplate
    from pathlib import Path
    import tempfile, os

    content = "System instructions here.\n{# === USER INPUT BELOW === #}\nHello {{ name }}!"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
        f.write(content)
        path = Path(f.name)
    try:
        t = PromptTemplate(path)
        assert t.system == "System instructions here."
        assert t.render_user(name="World") == "Hello World!"
    finally:
        os.unlink(path)


def test_prompt_template_no_split():
    """PromptTemplate with no marker treats entire file as system prompt."""
    from src.flows.ercole.prompts import PromptTemplate
    from pathlib import Path
    import tempfile, os

    content = "Just a system prompt, no split."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
        f.write(content)
        path = Path(f.name)
    try:
        t = PromptTemplate(path)
        assert t.system == content
        assert t.render_user() == ""
    finally:
        os.unlink(path)


def test_specialist_prompts_load():
    """Verify that .j2 files load and split correctly into system / user parts."""
    from src.flows.ercole.specialists import DOCUMENT_READER, TASK_RECOGNIZER, WORKER

    assert len(DOCUMENT_READER.prompt) > 100
    assert "{{ page_text }}" not in DOCUMENT_READER.prompt   # user var not in system
    assert "{{ page_number }}" not in DOCUMENT_READER.prompt
    assert len(TASK_RECOGNIZER.prompt) > 100
    assert "{{ pages_information }}" not in TASK_RECOGNIZER.prompt
    assert WORKER.prompt.startswith("You are an AI assistant")
    assert "{{ llm_instructions }}" not in WORKER.prompt


def test_build_doc_reader_message():
    from src.flows.ercole.specialists import build_doc_reader_message

    msg = build_doc_reader_message(page_number=3, page_text="Some OCR text here.")
    assert "3" in msg
    assert "Some OCR text here." in msg
    assert "{{ page_number }}" not in msg
    assert "{{ page_text }}" not in msg


def test_build_task_recognizer_message():
    from src.flows.ercole.specialists import build_task_recognizer_message

    pages_yaml = "pages_information:\n  total_pages: 1\n"
    msg = build_task_recognizer_message(pages_yaml)
    assert "total_pages: 1" in msg
    assert "{{ pages_information }}" not in msg


def test_build_worker_message():
    from src.flows.ercole.specialists import build_worker_message

    msg = build_worker_message(
        llm_instructions="requests:\n  - request_id: REQ_1\n",
        attachment_metadata="pages:\n  - page_number: 1\n",
    )
    assert "REQ_1" in msg
    assert "page_number: 1" in msg
    assert "{{ llm_instructions }}" not in msg
    assert "{{ attachment_metadata }}" not in msg


def test_build_summarizer_message():
    from src.flows.ercole.specialists import build_summarizer_message

    msg = build_summarizer_message(summary_context='{"total_pages": 2}')
    assert '"total_pages": 2' in msg
    assert "{{ summary_context }}" not in msg


def test_build_follow_up_message():
    from src.flows.ercole.specialists import build_follow_up_message

    msg = build_follow_up_message(
        analysis_context='{"requests": []}',
        question="Quante richieste ci sono?",
    )
    assert '"requests": []' in msg
    assert "Quante richieste ci sono?" in msg
    assert "{{ analysis_context }}" not in msg
    assert "{{ question }}" not in msg


# ---------------------------------------------------------------------------
# Coordinator tests
# ---------------------------------------------------------------------------


def test_coordinator_classifier_prompt_loads():
    """Classifier prompt must have a system part and a user template."""
    from src.coordinator.document_coordinator import _CLASSIFIER_PROMPT

    assert len(_CLASSIFIER_PROMPT.system) > 100
    assert "{{ user_message }}" not in _CLASSIFIER_PROMPT.system  # var in user template
    user_msg = _CLASSIFIER_PROMPT.render_user(
        user_message="test",
        has_pages=False,
        has_session=False,
        available_flows=[],
    )
    assert "test" in user_msg
    assert "{{ user_message }}" not in user_msg


def test_coordinator_classifier_prompt_renders_flows():
    """Available flows must appear in the rendered user message."""
    from src.coordinator.document_coordinator import _CLASSIFIER_PROMPT

    flows = [{"flow_type": "ercole", "description": "Test desc", "hints": ["hint1", "hint2"]}]
    user_msg = _CLASSIFIER_PROMPT.render_user(
        user_message="Voglio elaborare un modulo",
        has_pages=True,
        has_session=False,
        available_flows=flows,
    )
    assert "ercole" in user_msg
    assert "hint1" in user_msg


def test_classification_result_defaults():
    """ClassificationResult must default to off_topic."""
    from src.coordinator.document_coordinator import ClassificationResult

    r = ClassificationResult()
    assert r.intent == "off_topic"
    assert r.flow_type is None
    assert r.confidence == 0


def test_coordinator_response_model():
    """CoordinatorResponse must round-trip correctly."""
    from src.coordinator.document_coordinator import CoordinatorResponse

    r = CoordinatorResponse(intent="off_topic", response="Mi dispiace...")
    assert r.session_id is None
    assert r.flow_type is None
    assert r.document_result is None


def test_coordinator_fallback_message_is_italian():
    """Fallback message must be in Italian and mention Ercole."""
    from src.coordinator.document_coordinator import _FALLBACK_MESSAGE

    assert "Ercole" in _FALLBACK_MESSAGE or "ercole" in _FALLBACK_MESSAGE.lower()
    assert len(_FALLBACK_MESSAGE) > 50


def test_classifier_specialist_uses_haiku():
    """Classifier must use the lightweight Haiku model, not Sonnet or Opus."""
    from src.coordinator.document_coordinator import _CLASSIFIER

    assert "haiku" in _CLASSIFIER.model.lower()


def test_flow_routing_info_for_coordinator():
    """get_flow_routing_info() must return data the coordinator classifier can use."""
    from src.flows import get_flow_routing_info

    info = get_flow_routing_info()
    assert isinstance(info, list)
    assert len(info) >= 1
    first = info[0]
    assert "flow_type" in first
    assert "description" in first
    assert "hints" in first
    assert isinstance(first["hints"], list)
