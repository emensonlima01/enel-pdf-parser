# -*- coding: ascii -*-
from __future__ import annotations

import io
from typing import Iterable, List, Tuple

import numpy as np
from PIL import Image


class ImageCropper:
    def __init__(self, image: np.ndarray | bytes) -> None:
        if isinstance(image, np.ndarray):
            self._image = np.ascontiguousarray(image)
            return

        loaded_image = Image.open(io.BytesIO(image)).convert("RGB")
        loaded_image.load()
        self._image = np.ascontiguousarray(np.asarray(loaded_image).copy())

    @property
    def size(self) -> Tuple[int, int]:
        height, width = self._image.shape[:2]
        return (width, height)

    def crop(self, coord: Tuple[int, int, int, int]) -> bytes:
        cropped = self.crop_ndarray(coord)
        out = io.BytesIO()
        Image.fromarray(cropped).save(out, format="PNG")
        return out.getvalue()

    def crop_ndarray(self, coord: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, width, height = coord
        return np.ascontiguousarray(self._image[y : y + height, x : x + width])

    def crop_many_ndarray(
        self, coords: Iterable[Tuple[int, int, int, int]]
    ) -> List[np.ndarray]:
        return [self.crop_ndarray(coord) for coord in coords]


def crop_image_bytes(image: np.ndarray | bytes, coord: Tuple[int, int, int, int]) -> bytes:
    """
    coord = (x, y, width, height)
    retorna bytes PNG do recorte.
    """
    return ImageCropper(image).crop(coord)
