"""Subrequest detection from structured page extraction outputs.

Groups related pages into subrequests. Purely deterministic — no LLM, no OCR,
no PDF rendering, no persistence, no validation.
"""

from __future__ import annotations

from typing import Any

from src.schemas.page_extraction import PageExtraction


# -- Public API ----------------------------------------------------------------


def detect_subrequests(
    page_summaries: list[dict] | dict[int, dict],
    rules: str | dict | None = None,
) -> list[dict]:
    """Detect and group subrequests from structured page extraction outputs.

    Grouping is conservative: a page joins the current group only when it
    shares at least one entity string or field name with any page already in
    that group. When uncertain, pages are split into separate subrequests
    rather than merged.

    Args:
        page_summaries: Either a list of PageExtraction-shaped dicts (any
            order) or a dict[int, dict] keyed by 1-based page number.
        rules: Optional grouping hints. Recognised keys when dict:
            - "max_pages_per_group" (int): hard cap on group size.
            Unrecognised keys and string values are silently ignored.

    Returns:
        List of subrequest dicts, each with:
            request_id, pages, description, data.
        Returns [] for empty input.
    """
    pages = _normalize_input(page_summaries)
    if not pages:
        return []

    max_group = _parse_max_group(rules)
    groups = _group_pages(pages, max_group)
    return [_build_subrequest(idx + 1, group) for idx, group in enumerate(groups)]


# -- Input normalisation -------------------------------------------------------


def _normalize_input(raw: list[dict] | dict[int, dict]) -> list[dict]:
    """Return a list of page dicts sorted by page_number (ascending)."""
    if isinstance(raw, dict):
        items: list[dict] = list(raw.values())
    else:
        items = list(raw)
    return sorted(items, key=lambda p: p.get("page_number", 0))


def _parse_max_group(rules: str | dict | None) -> int | None:
    if not isinstance(rules, dict):
        return None
    value = rules.get("max_pages_per_group")
    if isinstance(value, int) and value > 0:
        return value
    return None


# -- Grouping ------------------------------------------------------------------


def _group_pages(pages: list[dict], max_group: int | None) -> list[list[dict]]:
    """Sequentially group pages by shared entity strings or field (name, value) pairs.

    Entity overlap: same entity string appears on both pages (e.g. same person name).
    Field-value overlap: same field_name AND same field_value on both pages.
    Pure field-name overlap (e.g. both pages have a "nome" field) is NOT a
    grouping signal — it triggers too many false positives across unrelated forms.

    A page is added to the current group when it overlaps with the accumulated
    entity set or field-value set of that group. Otherwise a new group starts.
    max_group caps the group size; a full group is closed and a new one starts.
    """
    groups: list[list[dict]] = []
    current: list[dict] = [pages[0]]
    group_entities: set[str] = set(_entities(pages[0]))
    group_field_pairs: set[tuple[str, str]] = set(_field_pairs(pages[0]))

    for page in pages[1:]:
        page_entities = set(_entities(page))
        page_field_pairs = set(_field_pairs(page))

        at_cap = max_group is not None and len(current) >= max_group
        shares_entity = bool(group_entities & page_entities)
        shares_field_pair = bool(group_field_pairs & page_field_pairs)

        if not at_cap and (shares_entity or shares_field_pair):
            current.append(page)
            group_entities |= page_entities
            group_field_pairs |= page_field_pairs
        else:
            groups.append(current)
            current = [page]
            group_entities = page_entities
            group_field_pairs = page_field_pairs

    groups.append(current)
    return groups


# -- Subrequest assembly -------------------------------------------------------


def _build_subrequest(index: int, pages: list[dict]) -> dict[str, Any]:
    """Assemble a single subrequest dict from a group of pages."""
    page_numbers = sorted(
        p.get("page_number", i + 1) for i, p in enumerate(pages)
    )

    header = next((p.get("header", "") for p in pages if p.get("header")), "")
    first_summary = pages[0].get("summary", "")
    if header and first_summary:
        description = f"{header} — {first_summary}"
    elif header:
        description = header
    elif first_summary:
        description = first_summary
    else:
        description = f"Subrequest {index}"

    all_entities = _merge_entities(pages)
    all_fields = _merge_fields(pages)

    if len(pages) == 1:
        grouping_note = "Single-page subrequest."
    else:
        overlap_types: list[str] = []
        if _has_shared_entities(pages):
            overlap_types.append("shared entities")
        if _has_shared_fields(pages):
            overlap_types.append("shared field names")
        reason = " and ".join(overlap_types) if overlap_types else "adjacency"
        grouping_note = (
            f"{len(pages)} pages grouped by {reason}."
        )

    return {
        "request_id": f"R{index}",
        "pages": page_numbers,
        "description": description,
        "data": {
            "entities": all_entities,
            "filled_fields": all_fields,
            "grouping_note": grouping_note,
        },
    }


# -- Helpers -------------------------------------------------------------------


def _entities(page: dict) -> list[str]:
    return [e for e in page.get("entities", []) if isinstance(e, str) and e.strip()]


def _field_names(page: dict) -> list[str]:
    return [
        f["field_name"]
        for f in page.get("filled_fields", [])
        if isinstance(f, dict) and f.get("field_name")
    ]


def _field_pairs(page: dict) -> list[tuple[str, str]]:
    """Return (field_name, field_value) pairs — used for grouping signal."""
    return [
        (f["field_name"], f["field_value"])
        for f in page.get("filled_fields", [])
        if isinstance(f, dict) and f.get("field_name") and f.get("field_value")
    ]


def _merge_entities(pages: list[dict]) -> list[str]:
    """Deduplicated entity list preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for page in pages:
        for e in _entities(page):
            if e not in seen:
                seen.add(e)
                result.append(e)
    return result


def _merge_fields(pages: list[dict]) -> list[dict[str, str]]:
    """Merge filled_fields across pages; last value wins on duplicate field names."""
    fields_map: dict[str, str] = {}
    for page in pages:
        for f in page.get("filled_fields", []):
            if isinstance(f, dict) and f.get("field_name") and f.get("field_value"):
                fields_map[f["field_name"]] = f["field_value"]
    return [{"field_name": k, "field_value": v} for k, v in fields_map.items()]


def _has_shared_entities(pages: list[dict]) -> bool:
    if len(pages) < 2:
        return False
    first = set(_entities(pages[0]))
    return any(first & set(_entities(p)) for p in pages[1:])


def _has_shared_fields(pages: list[dict]) -> bool:
    if len(pages) < 2:
        return False
    first = set(_field_pairs(pages[0]))
    return any(first & set(_field_pairs(p)) for p in pages[1:])
