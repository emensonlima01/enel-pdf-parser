# -*- coding: ascii -*-
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path


_LAYOUTS_DIR = Path(__file__).resolve().parent / "layouts"


@dataclass(frozen=True)
class Coordinates:
    description: str
    source: str
    x: int
    y: int
    width: int
    height: int


@lru_cache(maxsize=8)
def _load_layout(layout_id: str) -> tuple[Coordinates, ...]:
    layout_path = _LAYOUTS_DIR / f"{layout_id}.json"
    with layout_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    regions = payload.get("regions", [])
    return tuple(
        Coordinates(
            description=region["description"],
            source=region.get("source", "native"),
            x=region["x"],
            y=region["y"],
            width=region["width"],
            height=region["height"],
        )
        for region in regions
    )


def build_regions(layout_id: str = "v1") -> list[Coordinates]:
    return list(_load_layout(layout_id))
