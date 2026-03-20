# -*- coding: ascii -*-
from __future__ import annotations

from ._utils import format_year_month, normalize_text
from .primeiro_item import map as mapear_primeiro_item


def map(texts: list, boxes=None) -> str:
    del boxes
    value = mapear_primeiro_item(texts)
    if value:
        normalized = normalize_text(value)
        if normalized in ("mes/ano", "mes ano"):
            for text in texts[1:]:
                if not text:
                    continue
                candidate = str(text).strip()
                if candidate:
                    value = candidate
                    break
    if not value:
        return ""
    return format_year_month(value.strip())
