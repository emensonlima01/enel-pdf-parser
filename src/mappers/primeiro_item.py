# -*- coding: ascii -*-
from __future__ import annotations


def map(texts: list, boxes: list | None = None) -> str:
    del boxes
    for text in texts:
        if not text:
            continue
        texto_limpo = str(text).strip()
        if texto_limpo:
            return texto_limpo.upper()
    return ""
