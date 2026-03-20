# -*- coding: ascii -*-
from __future__ import annotations

from functools import lru_cache
import json
import unicodedata
from pathlib import Path

_HEADERS_PATH = Path(__file__).resolve().parent / "layouts" / "headers.json"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_accents.upper().split())


def _parse_region(region: dict) -> tuple[int, int, int, int] | None:
    try:
        x = int(float(region["x"]))
        y = int(float(region["y"]))
        w = int(float(region["w"]))
        h = int(float(region["h"]))
    except (KeyError, TypeError, ValueError):
        return None

    if w <= 0 or h <= 0:
        return None

    return (x, y, w, h)


@lru_cache(maxsize=1)
def _load_headers() -> dict:
    if not _HEADERS_PATH.exists():
        return {}

    with _HEADERS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def detect_layout(text_reader, ocr_text_reader=None) -> str:
    payload = _load_headers()
    if not payload:
        return "v1"

    for layout_id, rules in payload.items():
        anchors = [_normalize_text(str(anchor)) for anchor in rules.get("anchors", [])]
        coords = _parse_region(rules.get("region", {}))
        if not coords or not anchors:
            continue

        texts = text_reader(coords)
        if not texts and ocr_text_reader is not None:
            texts = ocr_text_reader(coords)

        haystack = _normalize_text(" ".join(texts))
        if any(anchor in haystack for anchor in anchors):
            return layout_id

    if "v1" in payload:
        return "v1"
    return next(iter(payload), "v1")
