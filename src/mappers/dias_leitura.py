# -*- coding: ascii -*-
from __future__ import annotations

import re

from .primeiro_item import map as mapear_primeiro_item


def map(texts: list, boxes=None) -> int:
    del boxes
    value = mapear_primeiro_item(texts)
    if not value:
        return 0
    cleaned = re.sub(r"[^0-9-]", "", value).strip()
    if not cleaned:
        return 0
    try:
        return int(cleaned)
    except ValueError:
        return 0
