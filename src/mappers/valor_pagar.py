# -*- coding: ascii -*-
from __future__ import annotations

from ._utils import normalize_text, parse_decimal
from .primeiro_item import map as mapear_primeiro_item
from ._utils import parse_decimal


def map(texts: list, boxes=None) -> Decimal:
    del boxes
    value = mapear_primeiro_item(texts)
    if value:
        normalized = normalize_text(value)
        if any(keyword in normalized for keyword in ("pagar", "paga", "pagamento")):
            for text in texts[1:]:
                if not text:
                    continue
                candidate = str(text).strip()
                if candidate:
                    value = candidate
                    break
    return parse_decimal(value)
