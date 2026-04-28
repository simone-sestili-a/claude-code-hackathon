"""Tests for src/tools/pdf_tools.py — no fixtures, PDFs created in-process."""

import os
import tempfile
from pathlib import Path

import fitz
import pytest

from src.tools.pdf_tools import pdf_to_page_images, render_page


def _make_pdf(num_pages: int, tmp_dir: str) -> str:
    """Create a minimal PDF with num_pages pages and return its path."""
    path = str(Path(tmp_dir) / "sample.pdf")
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1}")
    doc.save(path)
    doc.close()
    return path


class TestPdfToPageImages:
    def test_missing_file_raises_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError, match="PDF not found"):
            pdf_to_page_images("/nonexistent/path/file.pdf")

    def test_invalid_pdf_raises_value_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"this is not a pdf")
        with pytest.raises(ValueError, match="Cannot open as PDF"):
            pdf_to_page_images(str(bad))

    def test_single_page_returns_one_image(self, tmp_path: Path) -> None:
        pdf = _make_pdf(1, str(tmp_path))
        images = pdf_to_page_images(pdf, str(tmp_path / "out"))
        assert len(images) == 1
        assert images[0].endswith("page_1.png")
        assert os.path.isfile(images[0])

    def test_multipage_returns_ordered_images(self, tmp_path: Path) -> None:
        pdf = _make_pdf(3, str(tmp_path))
        out = str(tmp_path / "out")
        images = pdf_to_page_images(pdf, out)
        assert len(images) == 3
        assert images[0].endswith("page_1.png")
        assert images[1].endswith("page_2.png")
        assert images[2].endswith("page_3.png")
        for p in images:
            assert os.path.isfile(p)

    def test_page_order_matches_index(self, tmp_path: Path) -> None:
        pdf = _make_pdf(5, str(tmp_path))
        images = pdf_to_page_images(pdf, str(tmp_path / "out"))
        for i, path in enumerate(images, start=1):
            assert Path(path).name == f"page_{i}.png"

    def test_output_dir_created_automatically(self, tmp_path: Path) -> None:
        pdf = _make_pdf(2, str(tmp_path))
        new_dir = str(tmp_path / "deep" / "nested" / "out")
        images = pdf_to_page_images(pdf, new_dir)
        assert len(images) == 2
        assert os.path.isdir(new_dir)

    def test_no_output_dir_uses_tempdir(self, tmp_path: Path) -> None:
        pdf = _make_pdf(2, str(tmp_path))
        images = pdf_to_page_images(pdf)
        assert len(images) == 2
        for p in images:
            assert os.path.isfile(p)

    def test_empty_pdf_returns_empty_list(self, tmp_path: Path) -> None:
        # PyMuPDF refuses to save a zero-page PDF (format requires ≥1 page),
        # so we test the guard via monkeypatching rather than a real file.
        pdf = _make_pdf(1, str(tmp_path))

        original_open = fitz.open

        class _ZeroPageDoc:
            page_count = 0

            def close(self) -> None:
                pass

        import unittest.mock as mock

        with mock.patch("src.tools.pdf_tools.fitz.open", return_value=_ZeroPageDoc()):
            result = pdf_to_page_images(pdf)

        assert result == []


class TestRenderPage:
    def test_render_page_returns_existing_png(self, tmp_path: Path) -> None:
        pdf = _make_pdf(1, str(tmp_path))
        doc = fitz.open(pdf)
        try:
            out = render_page(doc, 0, str(tmp_path))
        finally:
            doc.close()
        assert out.endswith("page_1.png")
        assert os.path.isfile(out)
