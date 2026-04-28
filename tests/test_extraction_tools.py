"""Tests for src/tools/extraction_tools.py — no API key required."""

from pathlib import Path

import fitz
import pytest

from src.tools.extraction_tools import extract_page, extract_pages_from_pdf


# -- Helpers -------------------------------------------------------------------

def _make_pdf_with_text(pages: list[str], tmp_dir: str) -> str:
    """Create a PDF where each page contains the given text."""
    path = str(Path(tmp_dir) / "sample.pdf")
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


# -- extract_page --------------------------------------------------------------

class TestExtractPage:
    def test_returns_all_required_keys(self) -> None:
        result = extract_page("IT Help Desk\nNome: Mario Rossi", 1)
        assert set(result.keys()) == {"page_number", "header", "summary", "entities", "filled_fields"}

    def test_page_number_preserved(self) -> None:
        result = extract_page("Some text", 7)
        assert result["page_number"] == 7

    def test_header_is_first_line(self) -> None:
        result = extract_page("Reset Password Request\nNome: Mario Rossi", 1)
        assert result["header"] == "Reset Password Request"

    def test_header_empty_on_blank_page(self) -> None:
        result = extract_page("", 1)
        assert result["header"] == ""

    def test_summary_excludes_header(self) -> None:
        result = extract_page("HEADER LINE\nBody content here", 1)
        assert "HEADER LINE" not in result["summary"]
        assert "Body content here" in result["summary"]

    def test_summary_truncated_at_300(self) -> None:
        long_body = "A" * 500
        result = extract_page(f"Header\n{long_body}", 1)
        assert len(result["summary"]) <= 300
        assert result["summary"].endswith("...")

    def test_empty_page_returns_valid_structure(self) -> None:
        result = extract_page("", 3)
        assert result["page_number"] == 3
        assert result["header"] == ""
        assert result["summary"] == ""
        assert result["entities"] == []
        assert result["filled_fields"] == []

    def test_entities_detects_date(self) -> None:
        result = extract_page("Richiesta del 15/04/2024", 1)
        assert any("15/04/2024" in e for e in result["entities"])

    def test_entities_detects_italian_fiscal_code(self) -> None:
        result = extract_page("Codice Fiscale: RSSMRA80A01H501Z", 1)
        assert "RSSMRA80A01H501Z" in result["entities"]

    def test_entities_detects_email(self) -> None:
        result = extract_page("Email: mario.rossi@example.com", 1)
        assert "mario.rossi@example.com" in result["entities"]

    def test_entities_detects_ticket_id(self) -> None:
        result = extract_page("Riferimento: INC-20241031", 1)
        assert any("INC" in e for e in result["entities"])

    def test_entities_no_hallucination_on_empty(self) -> None:
        result = extract_page("No codes here just plain prose text.", 1)
        assert result["entities"] == []

    def test_entities_deduplicated(self) -> None:
        result = extract_page("Data: 01/01/2024\nScadenza: 01/01/2024", 1)
        assert result["entities"].count("01/01/2024") == 1

    def test_filled_fields_known_label(self) -> None:
        result = extract_page("Nome: Mario\nCognome: Rossi", 1)
        keys = [f["field_name"] for f in result["filled_fields"]]
        assert "Nome" in keys
        assert "Cognome" in keys

    def test_filled_fields_values_correct(self) -> None:
        result = extract_page("Email: mario@example.com\nTelefono: 333-1234567", 1)
        by_key = {f["field_name"]: f["field_value"] for f in result["filled_fields"]}
        assert by_key.get("Email") == "mario@example.com"
        assert by_key.get("Telefono") == "333-1234567"

    def test_filled_fields_skips_empty_values(self) -> None:
        result = extract_page("Nome:\nCognome: Rossi", 1)
        keys = [f["field_name"] for f in result["filled_fields"]]
        assert "Nome" not in keys
        assert "Cognome" in keys

    def test_filled_fields_no_duplicates(self) -> None:
        result = extract_page("Nome: Mario\nNome: Luigi", 1)
        keys = [f["field_name"].lower() for f in result["filled_fields"]]
        assert keys.count("nome") == 1

    def test_filled_fields_short_unlisted_label_accepted(self) -> None:
        # "Data richiesta" is ≤3 words — accepted even if not in known labels
        result = extract_page("Data richiesta: 2024-01-10", 1)
        keys = [f["field_name"] for f in result["filled_fields"]]
        assert "Data richiesta" in keys

    def test_filled_fields_long_value_skipped(self) -> None:
        long_val = "X" * 201
        result = extract_page(f"Nome: {long_val}", 1)
        assert result["filled_fields"] == []

    def test_output_is_json_serializable(self) -> None:
        import json
        result = extract_page("Nome: Mario\nEmail: m@x.com\nData: 01/01/2024", 1)
        # Should not raise
        serialized = json.dumps(result)
        assert '"page_number"' in serialized

    def test_company_and_person_fields_coexist(self) -> None:
        text = "Ragione sociale: Acme S.r.l.\nRappresentante legale: Mario Bianchi"
        result = extract_page(text, 1)
        keys = [f["field_name"] for f in result["filled_fields"]]
        assert "Ragione sociale" in keys
        assert "Rappresentante legale" in keys


# -- extract_pages_from_pdf ----------------------------------------------------

class TestExtractPagesFromPdf:
    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            extract_pages_from_pdf("/nonexistent/file.pdf")

    def test_invalid_file_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        with pytest.raises(ValueError):
            extract_pages_from_pdf(str(bad))

    def test_multipage_keys_match_page_numbers(self, tmp_path: Path) -> None:
        pdf = _make_pdf_with_text(["Page one text", "Page two text", "Page three"], str(tmp_path))
        result = extract_pages_from_pdf(pdf)
        assert set(result.keys()) == {1, 2, 3}

    def test_each_page_has_correct_page_number(self, tmp_path: Path) -> None:
        pdf = _make_pdf_with_text(["First", "Second"], str(tmp_path))
        result = extract_pages_from_pdf(pdf)
        assert result[1]["page_number"] == 1
        assert result[2]["page_number"] == 2

    def test_single_page_pdf(self, tmp_path: Path) -> None:
        pdf = _make_pdf_with_text(["Only page"], str(tmp_path))
        result = extract_pages_from_pdf(pdf)
        assert len(result) == 1
        assert result[1]["page_number"] == 1

    def test_pages_are_independent(self, tmp_path: Path) -> None:
        # Entities on page 1 must not bleed into page 2
        pdf = _make_pdf_with_text(
            ["Email: a@b.com", "No entities here plain text"],
            str(tmp_path),
        )
        result = extract_pages_from_pdf(pdf)
        assert any("a@b.com" in e for e in result[1]["entities"])
        assert result[2]["entities"] == []
