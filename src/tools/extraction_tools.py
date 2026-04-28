"""Page extraction utility for IntakeAI.

Deterministic, LLM-free extraction of structured information from page text.
Does not detect subrequests, validate, group pages, or persist anything.
"""

import re
from pathlib import Path

import fitz  # PyMuPDF

from src.schemas.page_extraction import FilledField, PageExtraction


# -- Entity patterns -----------------------------------------------------------
# Applied in order; first match wins for deduplication by matched string.
_ENTITY_PATTERNS: list[str] = [
    r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b",              # date DD/MM/YYYY
    r"\b\d{4}[/\-.]\d{2}[/\-.]\d{2}\b",                      # date YYYY-MM-DD
    r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b",          # Italian codice fiscale
    r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b",  # email
    r"\bPROT(?:OCOLLO)?\.?\s*(?:N\.?\s*)?\d+[/\-]\d+\b",    # protocol number
    r"\b(?:TKT|TICK|REQ|INC|CHG|TASK|CRQ)[-#]?\s*\d+\b",    # ticket / request ID
    r"(?<!\w)[A-Z][a-zA-Z]{1,25}\s+S\.(?:r\.l\.|p\.A\.|n\.c\.|a\.s\.)",  # company
]

# -- Known field labels (case-insensitive exact match on normalised key) -------
_KNOWN_LABELS: frozenset[str] = frozenset({
    "nome", "cognome", "name", "surname", "full name", "nome e cognome",
    "ragione sociale", "denominazione", "company name", "business name",
    "codice fiscale", "fiscal code", "tax code", "cf",
    "partita iva", "p.iva", "p. iva", "vat", "vat number",
    "data di nascita", "date of birth", "dob",
    "indirizzo", "address", "sede legale", "registered office",
    "email", "e-mail", "pec",
    "telefono", "phone", "tel", "mobile", "cellulare",
    "iban",
    "tipo richiesta", "request type", "oggetto", "subject",
    "protocollo", "protocol", "protocol number", "numero protocollo",
    "ticket", "ticket number", "ticket id", "numero ticket",
    "importo", "amount",
    "data", "date",
    "riferimento", "reference", "ref",
    "sistema", "applicazione", "application", "system",
    "rappresentante legale", "legal representative",
    "username", "user id", "utente",
    "reparto", "department", "sede", "location",
    "priorità", "priority",
    "descrizione", "description",
    "categoria", "category",
    "stato", "status",
    "azione richiesta", "requested action",
})

# Matches "Label: Value" — label up to 60 chars, value up to 200 chars.
_LABEL_VALUE_RE = re.compile(
    r"^([A-Za-zÀ-ÿ0-9\s\.#_\-\/]{1,60}):\s*(.{1,200})$"
)


def _extract_header(lines: list[str]) -> str:
    """Return the first non-empty line under 120 chars, or empty string."""
    for line in lines:
        if len(line) <= 120:
            return line
    return ""


def _extract_summary(lines: list[str], header: str) -> str:
    """Concatenate non-header lines; truncate at 300 chars."""
    body = " ".join(l for l in lines if l != header)
    if len(body) <= 300:
        return body
    return body[:297] + "..."


def _extract_entities(text: str) -> list[str]:
    """Return unique regex matches from known entity patterns, in order of appearance."""
    found: list[str] = []
    seen: set[str] = set()
    for pattern in _ENTITY_PATTERNS:
        for match in re.finditer(pattern, text):
            value = match.group().strip()
            if value not in seen:
                seen.add(value)
                found.append(value)
    return found


def _extract_filled_fields(lines: list[str]) -> list[FilledField]:
    """Return label-value pairs from lines matching 'Label: Value'.

    Accepts a label if it is in the known-label list (exact, case-insensitive)
    or if it has at most 3 words (catches unlisted but obvious labels).
    Long values (>200 chars) and duplicates are skipped.
    """
    fields: list[FilledField] = []
    seen_keys: set[str] = set()
    for line in lines:
        m = _LABEL_VALUE_RE.match(line)
        if not m:
            continue
        key, value = m.group(1).strip(), m.group(2).strip()
        if not key or not value:
            continue
        norm = key.lower()
        is_known = norm in _KNOWN_LABELS
        is_short_label = len(key.split()) <= 3
        if not is_known and not is_short_label:
            continue
        if norm in seen_keys:
            continue
        seen_keys.add(norm)
        fields.append(FilledField(field_name=key, field_value=value))
    return fields


def extract_page(page_text: str, page_number: int) -> PageExtraction:
    """Extract structured information from a single page's plain text.

    Purely deterministic — no LLM, no subrequest detection, no persistence.

    Args:
        page_text: Raw text of the page (may be empty).
        page_number: 1-based page number.

    Returns:
        PageExtraction dict with page_number, header, summary, entities, filled_fields.
    """
    lines = [l.strip() for l in page_text.splitlines()]
    non_empty = [l for l in lines if l]

    header = _extract_header(non_empty)
    summary = _extract_summary(non_empty, header)
    entities = _extract_entities(page_text)
    filled_fields = _extract_filled_fields(non_empty)

    return PageExtraction(
        page_number=page_number,
        header=header,
        summary=summary,
        entities=entities,
        filled_fields=filled_fields,
    )


def extract_pages_from_pdf(pdf_path: str) -> dict[int, PageExtraction]:
    """Extract structured information from every page of a PDF.

    Uses PyMuPDF for text extraction, then calls extract_page per page.
    Returns a mapping keyed by 1-based page number.

    Args:
        pdf_path: Path to the source PDF file.

    Returns:
        {page_number: PageExtraction} for each page.

    Raises:
        FileNotFoundError: pdf_path does not exist.
        ValueError: File is not a valid PDF.
    """
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(source))
    except fitz.FileDataError as exc:
        raise ValueError(f"Cannot open as PDF: {pdf_path}") from exc

    result: dict[int, PageExtraction] = {}
    try:
        for i in range(doc.page_count):
            page_text = doc.load_page(i).get_text()
            result[i + 1] = extract_page(page_text, i + 1)
    finally:
        doc.close()

    return result
