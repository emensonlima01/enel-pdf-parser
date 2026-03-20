# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Final

import fitz  # PyMuPDF
import numpy as np

DEFAULT_DPI: Final[int] = 300


def _resolve_dpi(default: int) -> int:
    value = os.getenv("PDF_DPI")
    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError:
        return default

    return parsed if parsed > 0 else default


class PdfPageRegionExtractor:
    def __init__(self, pdf_bytes: bytes, page_number: int, dpi: int = DEFAULT_DPI) -> None:
        if page_number < 1:
            raise ValueError("page_number deve ser 1 ou maior")

        self._dpi = _resolve_dpi(dpi)
        self._doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_number > self._doc.page_count:
            self._doc.close()
            raise ValueError("page_number maior que o total de paginas")

        self._page = self._doc.load_page(page_number - 1)
        self._page_rect = self._page.rect
        self._zoom = self._dpi / 72.0
        self._matrix = fitz.Matrix(self._zoom, self._zoom)

    def __enter__(self) -> "PdfPageRegionExtractor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._doc.close()

    def _coord_to_pdf_rect(
        self, coord: tuple[int, int, int, int], padding_px: int = 0
    ) -> fitz.Rect:
        x, y, width, height = coord
        padding = padding_px / self._zoom
        x0 = max(self._page_rect.x0, (x / self._zoom) - padding)
        y0 = max(self._page_rect.y0, (y / self._zoom) - padding)
        x1 = min(self._page_rect.x1, ((x + width) / self._zoom) + padding)
        y1 = min(self._page_rect.y1, ((y + height) / self._zoom) + padding)
        return fitz.Rect(x0, y0, x1, y1)

    def extract_text_lines(self, coord: tuple[int, int, int, int]) -> list[str]:
        rect = self._coord_to_pdf_rect(coord, padding_px=2)
        text = self._page.get_text("text", clip=rect, sort=True)
        return [line.strip() for line in text.splitlines() if line and line.strip()]

    def render_region_to_ndarray(
        self, coord: tuple[int, int, int, int]
    ) -> np.ndarray:
        rect = self._coord_to_pdf_rect(coord)
        pix = self._page.get_pixmap(
            matrix=self._matrix,
            colorspace=fitz.csRGB,
            alpha=False,
            clip=rect,
        )
        return (
            np.frombuffer(pix.samples, dtype=np.uint8)
            .reshape(pix.height, pix.width, 3)
            .copy()
        )
