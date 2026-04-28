from typing import TypedDict


class FilledField(TypedDict):
    field_name: str
    field_value: str


class PageExtraction(TypedDict):
    page_number: int
    header: str
    summary: str
    entities: list[str]
    filled_fields: list[FilledField]
