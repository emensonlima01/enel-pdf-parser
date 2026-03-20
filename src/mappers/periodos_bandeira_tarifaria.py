# -*- coding: ascii -*-
from __future__ import annotations

import re
from ..models import PeriodoBandeiraTarifaria
from ._utils import format_month_day, normalize_text

_COLOR_RANGE_RE = re.compile(
    r"(AMARELA|VERDE|VERMELHA)\s*:?\s*"
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\s*(?:-|A|ATE)\s*"
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)"
)


def _normalize_date(value: str) -> str:
    return format_month_day(value)


def map(message: str) -> list[PeriodoBandeiraTarifaria]:
    if not message:
        return []
    normalized = normalize_text(message, case="upper")
    results: list[PeriodoBandeiraTarifaria] = []
    seen = set()

    def add(flag: str, start_date: str, end_date: str) -> None:
        key = (flag, start_date, end_date)
        if key in seen:
            return
        seen.add(key)
        results.append(
            PeriodoBandeiraTarifaria(
                bandeira=flag,
                data_inicio=start_date,
                data_fim=end_date,
            )
        )

    for flag_name, start_date, end_date in _COLOR_RANGE_RE.findall(normalized):
        normalized_start = _normalize_date(start_date)
        normalized_end = _normalize_date(end_date)
        if not normalized_start or not normalized_end:
            continue
        add(flag_name, normalized_start, normalized_end)
        if len(results) >= 2:
            break

    return results
