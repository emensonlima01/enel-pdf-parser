# -*- coding: ascii -*-
from __future__ import annotations

import re
from ..models import InformacoesCredito
from ._utils import normalize_text, parse_decimal


def _extract_kwh(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    raw = match.group(1)
    cleaned = "".join(ch for ch in raw if ch.isdigit() or ch in ".,-")
    if cleaned.count(".") > 1 and "," not in cleaned:
        parts = cleaned.split(".")
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    if cleaned.count(",") > 1 and "." not in cleaned:
        parts = cleaned.split(",")
        cleaned = "".join(parts[:-1]) + "," + parts[-1]
    parsed = parse_decimal(cleaned)
    try:
        return float(parsed)
    except ValueError:
        return None


def map(message: str) -> InformacoesCredito:
    if not message:
        return InformacoesCredito(
            energia_injetada_hfp_kwh=0.0,
            saldo_utilizado_kwh=0.0,
            saldo_atualizado_kwh=0.0,
            creditos_expirar_proximo_mes_kwh=0.0,
        )
    normalized = normalize_text(message, case="upper")
    injected = _extract_kwh(
        normalized, r"ENERGIA INJETADA HFP NO M.S:\s*([0-9.,]+)\s*KWH"
    )
    used = _extract_kwh(
        normalized, r"SALDO UTILIZADO NO M.S:\s*([0-9.,]+)\s*KWH"
    )
    updated = _extract_kwh(normalized, r"SALDO ATUALIZADO:\s*([0-9.,]+)\s*KWH")
    expiring = _extract_kwh(
        normalized,
        r"CREDITOS A EXPIRAR NO PROXIMO M.S:\s*([0-9.,]+)\s*KWH",
    )

    return InformacoesCredito(
        energia_injetada_hfp_kwh=injected or 0.0,
        saldo_utilizado_kwh=used or 0.0,
        saldo_atualizado_kwh=updated or 0.0,
        creditos_expirar_proximo_mes_kwh=expiring or 0.0,
    )
