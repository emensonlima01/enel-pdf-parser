# -*- coding: ascii -*-
from __future__ import annotations

import re

from ..models import InformacoesTributarias
from ._utils import build_items, format_date, group_items_by_row, normalize_text


def _extract_after_label(text: str, labels: list[str]) -> str:
    normalized = normalize_text(text)
    for label in labels:
        label_norm = normalize_text(label)
        index = normalized.find(label_norm)
        if index == -1:
            continue
        after = text[index + len(label_norm) :].strip(" :.-")
        if after:
            return after
    return ""


def _first_date(text: str) -> str:
    match = re.search(r"(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{4}(?!\d)", text)
    if not match:
        return ""
    return format_date(match.group(0))


def _first_digits(text: str, min_len: int) -> str:
    for match in re.findall(r"\d+", text):
        if len(match) >= min_len:
            return match
    return ""

def _extract_invoice_number(text: str) -> str:
    normalized = normalize_text(text)
    if "nota fiscal" not in normalized:
        return ""
    match = re.search(r"nota fiscal[^0-9]*(\d{6,})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return _first_digits(text, 6)


def _extract_access_key(text: str) -> str:
    normalized = normalize_text(text)
    label_index = normalized.find("chave de acesso")
    if label_index != -1:
        raw_after = text[label_index + len("chave de acesso") :]
        compact = "".join(re.findall(r"\d+", raw_after))
        if len(compact) >= 44:
            return compact
    compact_all = "".join(re.findall(r"\d+", text))
    if len(compact_all) >= 44:
        return compact_all[:44]
    return ""


def _extract_cfop(text: str) -> str:
    match = re.search(r"\bcfop\D*(\d{4})\b", text, re.IGNORECASE)
    return match.group(1) if match else ""


def _extract_date_after_label(text: str, labels: list[str]) -> str:
    normalized = normalize_text(text)
    for label in labels:
        label_norm = normalize_text(label)
        index = normalized.find(label_norm)
        if index == -1:
            continue
        after = text[index + len(label_norm) :]
        date = _first_date(after)
        if date:
            return date
    return ""

def map(texts: list, boxes: list | None = None) -> InformacoesTributarias:
    if boxes:
        items = build_items(texts, boxes)
        rows = group_items_by_row(items)
        lines = [" ".join(item["text"] for item in row).strip() for row in rows]
    else:
        lines = [str(text).strip() for text in texts if text and str(text).strip()]
    lines = [line for line in lines if line]
    full_text = " ".join(lines)
    numero_nota_fiscal = ""
    data_emissao_nota_fiscal = ""
    chave_acesso = ""
    cfop = ""
    data_apresentacao = ""

    for line in lines:
        normalized = normalize_text(line)
        if not numero_nota_fiscal and "nota fiscal" in normalized:
            numero_nota_fiscal = _extract_invoice_number(line)
            data_emissao_nota_fiscal = (
                data_emissao_nota_fiscal
                or _extract_date_after_label(line, ["data de emissao", "emissao"])
            )
        if not data_emissao_nota_fiscal and "emissao" in normalized:
            data_emissao_nota_fiscal = _extract_date_after_label(
                line, ["data de emissao", "emissao"]
            )
        if not chave_acesso and "chave de acesso" in normalized:
            chave_acesso = _extract_access_key(line)
        if not cfop and "cfop" in normalized:
            cfop = _extract_cfop(line)
        if not data_apresentacao and "apresentacao" in normalized:
            data_apresentacao = _extract_date_after_label(
                line, ["data de apresentacao", "apresentacao"]
            )

    if not numero_nota_fiscal:
        numero_nota_fiscal = _extract_invoice_number(full_text)
    if not data_emissao_nota_fiscal:
        data_emissao_nota_fiscal = _extract_date_after_label(
            full_text, ["data de emissao", "emissao"]
        )
    if not chave_acesso:
        chave_acesso = _extract_access_key(full_text)
    if not cfop:
        cfop = _extract_cfop(full_text)
    if not data_apresentacao:
        data_apresentacao = _extract_date_after_label(
            full_text, ["data de apresentacao", "apresentacao"]
        )

    return InformacoesTributarias(
        numero_nota_fiscal=numero_nota_fiscal.upper(),
        data_emissao_nota_fiscal=data_emissao_nota_fiscal.upper(),
        chave_acesso=chave_acesso.upper(),
        cfop=cfop.upper(),
        data_apresentacao=data_apresentacao.upper(),
        tributos=[],
    )
