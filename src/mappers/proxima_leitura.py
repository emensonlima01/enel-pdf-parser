# -*- coding: ascii -*-
from __future__ import annotations

from ._utils import format_date
from .primeiro_item import map as mapear_primeiro_item


def map(texts: list, boxes=None) -> str:
    del boxes
    value = mapear_primeiro_item(texts)
    if not value:
        return ""
    return format_date(value.strip())
