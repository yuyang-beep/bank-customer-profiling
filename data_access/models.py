"""统一查询对象，不包含 CSV 或 SQL 细节。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricQuery:
    province_codes: tuple[str, ...] = ()
    years: tuple[int, ...] = ()
    metric_keys: tuple[str, ...] = ()
    statistical_scopes: tuple[str, ...] = ()
    verification_statuses: tuple[str, ...] = ()
    display_statuses: tuple[str, ...] = ()
    current_only: bool = True
