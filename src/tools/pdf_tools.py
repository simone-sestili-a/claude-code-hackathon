"""PDF-to-images utility for IntakeAI.

Converts a PDF into one PNG image per page. Used as a preprocessing step when
inbound requests carry PDF attachments (InboundRequest.attachments).
No OCR, no agent logic — pure rendering.
"""

import tempfile
from pathlib import Path

import fitz  # PyMuPDF


def render_page(doc: fitz.Document, page_index: int, output_dir: str) -> str:
    """Render a single PDF page to a PNG file.

    Args:
        doc: Open PyMuPDF document.
        page_index: Zero-based page index.
        output_dir: Directory where the image will be saved.

    Returns:
        Absolute path of the saved PNG file.
    """
    page = doc.load_page(page_index)
    pixmap = page.get_pixmap(dpi=150)
    filename = f"page_{page_index + 1}.png"
    output_path = str(Path(output_dir) / filename)
    pixmap.save(output_path)
    return output_path


def pdf_to_page_images(pdf_path: str, output_dir: str | None = None) -> list[str]:
    """Convert a PDF into one PNG image per page.

    Args:
        pdf_path: Path to the source PDF file.
        output_dir: Directory for output images. Created if absent.
                    Defaults to a temporary directory when None.

    Returns:
        Ordered list of absolute image paths, one per page (page 1 first).

    Raises:
        FileNotFoundError: pdf_path does not exist.
        ValueError: File is not a valid PDF or contains no pages.
    """
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(source))
    except fitz.FileDataError as exc:
        raise ValueError(f"Cannot open as PDF: {pdf_path}") from exc

    if doc.page_count == 0:
        doc.close()
        return []

    target_dir = output_dir if output_dir is not None else tempfile.mkdtemp()
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    paths: list[str] = []
    try:
        for i in range(doc.page_count):
            paths.append(render_page(doc, i, target_dir))
    finally:
        doc.close()

    return paths
