# -*- coding: ascii -*-
from __future__ import annotations

import re

from ..models import ItemFatura
from ._utils import build_items, format_year_month, group_items_by_row, normalize_text, parse_decimal

COLUMN_ORDER = [
    "description",
    "unit",
    "quantity",
    "unit_price_with_taxes",
    "amount",
    "pis_cofins",
    "icms_tax_base",
    "icms_rate",
    "icms_amount",
    "unit_rate",
]
HEADER_COLUMNS = [
    ("description", ["descricao", "itens", "fatura"]),
    ("unit", ["unid"]),
    ("quantity", ["quant"]),
    ("unit_price_with_taxes", ["preco"]),
    ("amount", ["valor"]),
    ("pis_cofins", ["pis", "cofins"]),
    ("icms_tax_base", ["base"]),
    ("icms_rate", ["aliquota"]),
    ("icms_amount", ["icms"]),
    ("unit_rate", ["tarifa"]),
]

HEADER_KEYWORDS = {
    "descricao",
    "itens",
    "fatura",
    "unid",
    "quant",
    "preco",
    "valor",
    "pis",
    "cofins",
    "base",
    "aliquota",
    "icms",
    "tarifa",
}

COMPETENCIA_PATTERNS = [
    re.compile(
        r"(?<!\d)(?P<day>0?[1-9]|[12]\d|3[01])\s*[/\-.]\s*(?P<month>0?[1-9]|1[0-2])\s*[/\-.]\s*(?P<year>\d{4})(?!\d)"
    ),
    re.compile(
        r"(?<!\d)(?P<year>\d{4})\s*[/\-.]\s*(?P<month>0?[1-9]|1[0-2])\s*[/\-.]\s*(?P<day>0?[1-9]|[12]\d|3[01])(?!\d)"
    ),
    re.compile(
        r"(?<!\d)(?P<month>0?[1-9]|1[0-2])\s*[/\-.]\s*(?P<year>\d{4})(?!\d)"
    ),
    re.compile(
        r"(?<!\d)(?P<year>\d{4})\s*[/\-.]\s*(?P<month>0?[1-9]|1[0-2])(?!\d)"
    ),
    re.compile(
        r"(?<!\w)(?P<month_name>jan(?:eiro)?|fev(?:ereiro)?|mar(?:co)?|abr(?:il)?|mai(?:o)?|jun(?:ho)?|jul(?:ho)?|ago(?:sto)?|set(?:embro)?|out(?:ubro)?|nov(?:embro)?|dez(?:embro)?)\s*[/\-. ]\s*(?P<year>\d{4})(?!\d)"
    ),
]

MONTH_NAME_TO_NUMBER = {
    "jan": 1,
    "janeiro": 1,
    "fev": 2,
    "fevereiro": 2,
    "mar": 3,
    "marco": 3,
    "abr": 4,
    "abril": 4,
    "mai": 5,
    "maio": 5,
    "jun": 6,
    "junho": 6,
    "jul": 7,
    "julho": 7,
    "ago": 8,
    "agosto": 8,
    "set": 9,
    "setembro": 9,
    "out": 10,
    "outubro": 10,
    "nov": 11,
    "novembro": 11,
    "dez": 12,
    "dezembro": 12,
}

DECIMAL_TOKEN_PATTERN = re.compile(r"-?\d[\d.,]*-?")


def _row_like_header(row: list[dict]) -> bool:
    row_text = " ".join(item["text"] for item in row)
    normalized = normalize_text(row_text)
    matches = [key for key in HEADER_KEYWORDS if key in normalized]
    has_description = any(
        key in normalized for key in ("descricao", "itens", "fatura")
    )
    return len(matches) >= 3 and has_description


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
    used = set()
    for column, keywords in HEADER_COLUMNS:
        for item in header_items:
            if item["index"] in used:
                continue
            text = normalize_text(item["text"])
            if any(keyword in text for keyword in keywords):
                if column == "description":
                    matched = [
                        candidate
                        for candidate in header_items
                        if any(
                            keyword in normalize_text(candidate["text"])
                            for keyword in keywords
                        )
                    ]
                    positions[column] = max(
                        candidate.get("x_center", candidate["x"])
                        for candidate in matched
                    )
                else:
                    positions[column] = item.get("x_center", item["x"])
                used.add(item["index"])
                break
    if "amount" not in positions:
        unit_price = positions.get("unit_price_with_taxes")
        pis = positions.get("pis_cofins")
        if unit_price is not None and pis is not None:
            positions["amount"] = (unit_price + pis) / 2
    return positions


def _assign_line_items(
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


def _is_numeric_text(value: str) -> bool:
    if not value:
        return False
    allowed = set("0123456789.,-%")
    return all(char in allowed for char in value.strip())


def _is_numeric_row(items: list[dict]) -> bool:
    if not items:
        return False
    return all(_is_numeric_text(item["text"]) for item in items)


def _description_limit(column_positions: dict[str, float]) -> float | None:
    sorted_positions = sorted(column_positions.items(), key=lambda item: item[1])
    for index, (column_name, position) in enumerate(sorted_positions):
        if column_name == "description" and index + 1 < len(sorted_positions):
            next_position = sorted_positions[index + 1][1]
            return position + ((next_position - position) * 0.75)
    return None


def _is_description_code_row(items: list[dict], limit: float | None) -> bool:
    if limit is None or not items:
        return False
    if not all(item["x"] < limit for item in items):
        return False
    combined = "".join(item["text"].strip() for item in items)
    if not combined:
        return False
    return combined.isdigit() and len(combined) <= 6


def _extract_competencia(description: str) -> str:
    normalized_description = normalize_text(description)

    for pattern in COMPETENCIA_PATTERNS:
        match = pattern.search(normalized_description)
        if match is None:
            continue

        year = match.group("year")
        month_name = match.groupdict().get("month_name")
        if month_name:
            month = MONTH_NAME_TO_NUMBER.get(month_name)
            if month is None:
                continue
            return format_year_month(f"{month:02d}/{year}")

        month_value = match.groupdict().get("month")
        if not month_value:
            continue

        month = int(month_value)
        return format_year_month(f"{month:02d}/{year}")

    return ""


def _extract_decimal_tokens(value: str) -> list[str]:
    if not value:
        return []
    return [match.group(0) for match in DECIMAL_TOKEN_PATTERN.finditer(value)]


def _normalize_fused_value_columns(row: dict[str, str]) -> dict[str, str]:
    normalized_row = dict(row)
    if normalized_row.get("unit_price_with_taxes", "").strip():
        return normalized_row

    amount = normalized_row.get("amount", "").strip()
    quantity = normalized_row.get("quantity", "").strip()
    if not amount or not quantity:
        return normalized_row

    decimal_tokens = _extract_decimal_tokens(amount)
    if len(decimal_tokens) < 2:
        return normalized_row

    normalized_row["unit_price_with_taxes"] = decimal_tokens[0]
    normalized_row["amount"] = decimal_tokens[-1]
    return normalized_row


def map(texts: list, boxes: list) -> list[ItemFatura]:
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
    if "description" not in column_positions:
        return []
    description_limit = _description_limit(column_positions)
    result_rows = []
    pending_numeric_items = None
    for row in rows[header_index + 1 :]:
        if _is_description_code_row(row, description_limit) and result_rows:
            continue
        if _is_numeric_row(row):
            pending_numeric_items = row
            continue
        row_data = _assign_line_items(row, column_positions)
        if row_data.get("unit"):
            allowed_units = {"kwh", "kw", "mwh", "m3", "wh", "unid"}
            unit_tokens = row_data["unit"].split()
            kept_units = []
            for token in unit_tokens:
                normalized_token = normalize_text(token)
                if normalized_token in allowed_units:
                    kept_units.append(token)
            row_data["unit"] = " ".join(kept_units)

        normalized_description = normalize_text(row_data["description"])
        if not normalized_description:
            continue
        if normalized_description == "total" and pending_numeric_items:
            numeric_row = _assign_line_items(pending_numeric_items, column_positions)
            for column, value in numeric_row.items():
                if not row_data.get(column):
                    row_data[column] = value
            pending_numeric_items = None
        raw_row_data = dict(row_data)
        normalized_row_data = _normalize_fused_value_columns(raw_row_data)
        result_rows.append({"raw": raw_row_data, "mapped": normalized_row_data})
        if normalized_description == "total":
            break
    if not result_rows:
        return []
    mapped_items = []
    for row_entry in result_rows:
        raw_row = row_entry["raw"]
        mapped_row = row_entry["mapped"]
        mapped_items.append(
            ItemFatura(
                descricao=mapped_row.get("description", ""),
                competencia=_extract_competencia(mapped_row.get("description", "")),
                unidade=mapped_row.get("unit", "").upper(),
                quantidade=parse_decimal(mapped_row.get("quantity", "")),
                preco_unitario_com_tributos=parse_decimal(
                    mapped_row.get("unit_price_with_taxes", "")
                ),
                preco_unitario_com_tributos_original=raw_row.get(
                    "unit_price_with_taxes", ""
                ),
                valor=parse_decimal(mapped_row.get("amount", "")),
                pis_cofins=parse_decimal(mapped_row.get("pis_cofins", "")),
                base_calculo_icms=parse_decimal(mapped_row.get("icms_tax_base", "")),
                aliquota_icms=parse_decimal(mapped_row.get("icms_rate", "")),
                valor_icms=parse_decimal(mapped_row.get("icms_amount", "")),
                tarifa_unitaria=parse_decimal(mapped_row.get("unit_rate", "")),
                colunas_ocr={
                    "descricao": raw_row.get("description", ""),
                    "unidade": raw_row.get("unit", ""),
                    "quantidade": raw_row.get("quantity", ""),
                    "preco_unitario_com_tributos": raw_row.get(
                        "unit_price_with_taxes", ""
                    ),
                    "valor": raw_row.get("amount", ""),
                    "pis_cofins": raw_row.get("pis_cofins", ""),
                    "base_calculo_icms": raw_row.get("icms_tax_base", ""),
                    "aliquota_icms": raw_row.get("icms_rate", ""),
                    "valor_icms": raw_row.get("icms_amount", ""),
                    "tarifa_unitaria": raw_row.get("unit_rate", ""),
                },
            )
        )
    return mapped_items
