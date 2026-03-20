# -*- coding: ascii -*-
from __future__ import annotations

import re

from ..models import TributoFatura
from ._utils import build_items, group_items_by_row, normalize_text, parse_decimal

COLUMN_ORDER = [
    "tax_name",
    "base_calc",
    "rate",
    "amount",
]
HEADER_KEYWORDS = {
    "tributos",
    "base",
    "calc",
    "aliquota",
    "valor",
}

SIGLAS_TRIBUTOS_PATTERNS = [
    (re.compile(r"\bI\s+CMS\b", re.IGNORECASE), "ICMS"),
    (re.compile(r"\bP\s+IS\b", re.IGNORECASE), "PIS"),
    (re.compile(r"\bCO\s+FINS\b", re.IGNORECASE), "COFINS"),
]


def _row_like_header(row: list[dict]) -> bool:
    row_text = " ".join(item["text"] for item in row)
    normalized = normalize_text(row_text)
    matches = [key for key in HEADER_KEYWORDS if key in normalized]
    has_tributos = "tributos" in normalized
    return has_tributos and (len(matches) >= 2 or len(row) <= 2)


def _row_extends_header(row: list[dict]) -> bool:
    row_text = " ".join(item["text"] for item in row)
    normalized = normalize_text(row_text)
    if any(char.isdigit() for char in normalized):
        return False
    return any(key in normalized for key in HEADER_KEYWORDS)


def _find_header_index(rows: list[list[dict]]) -> int | None:
    for index, row in enumerate(rows):
        if _row_like_header(row):
            return index
    return None


def _infer_column_positions(header_items: list[dict]) -> dict[str, float]:
    positions: dict[str, float] = {}
    ordered_mapping = [
        ("tax_name", ["tributos"]),
        ("base_calc", ["base", "calc"]),
        ("rate", ["aliquota"]),
        ("amount", ["valor"]),
    ]
    used = set()
    for column, keywords in ordered_mapping:
        for item in header_items:
            if item["index"] in used:
                continue
            text = normalize_text(item["text"])
            if any(keyword in text for keyword in keywords):
                positions[column] = item.get("x_center", item["x"])
                used.add(item["index"])
                break
    return positions


def _assign_row_items(
    items: list[dict],
    column_positions: dict[str, float],
) -> dict[str, str]:
    row = {column: "" for column in COLUMN_ORDER}
    if not column_positions:
        return row
    sorted_positions = sorted(column_positions.items(), key=lambda item: item[1])
    boundaries = []
    for index in range(len(sorted_positions) - 1):
        boundaries.append(
            (sorted_positions[index][1] + sorted_positions[index + 1][1]) / 2
        )
    for item in items:
        x_value = item["x_center"]
        column_index = 0
        for boundary in boundaries:
            if x_value < boundary:
                break
            column_index += 1
        column_name = sorted_positions[
            min(column_index, len(sorted_positions) - 1)
        ][0]
        if row[column_name]:
            row[column_name] = f"{row[column_name]} {item['text']}".strip()
        else:
            row[column_name] = item["text"]
    return row


def _normalize_nome_tributo(value: str) -> str:
    normalized_value = value.strip()
    for pattern, replacement in SIGLAS_TRIBUTOS_PATTERNS:
        normalized_value = pattern.sub(replacement, normalized_value)
    return normalized_value.upper()


def _row_has_tax_values(row_data: dict[str, str]) -> bool:
    numeric_text = " ".join(
        row_data.get(column, "") for column in ("base_calc", "rate", "amount")
    )
    return any(char.isdigit() for char in numeric_text)


def map(texts: list, boxes: list) -> list[TributoFatura]:
    items = build_items(texts, boxes)
    rows = group_items_by_row(items)
    header_index = _find_header_index(rows)
    if header_index is None:
        return []
    header_items = list(rows[header_index])
    for row in rows[header_index + 1 : header_index + 3]:
        if _row_extends_header(row):
            header_items.extend(row)
        else:
            break
    column_positions = _infer_column_positions(header_items)
    if "tax_name" not in column_positions:
        return []
    result_rows = []
    for row in rows[header_index + 1 :]:
        if _row_extends_header(row):
            continue
        row_data = _assign_row_items(row, column_positions)
        normalized_name = normalize_text(row_data.get("tax_name", ""))
        if not normalized_name and not any(row_data.values()):
            continue
        if normalized_name in HEADER_KEYWORDS:
            continue
        if not _row_has_tax_values(row_data):
            continue
        result_rows.append(row_data)
    if not result_rows:
        return []
    return [
        TributoFatura(
            nome_tributo=_normalize_nome_tributo(row.get("tax_name", "")),
            base_calculo=parse_decimal(row.get("base_calc", "")),
            aliquota=parse_decimal(row.get("rate", "")),
            valor=parse_decimal(row.get("amount", "")),
        )
        for row in result_rows
    ]
