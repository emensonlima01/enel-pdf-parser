# -*- coding: ascii -*-
from __future__ import annotations

from .primeiro_item import map as mapear_primeiro_item


def map(texts: list, boxes=None) -> str:
    del boxes
    return mapear_primeiro_item(texts)
