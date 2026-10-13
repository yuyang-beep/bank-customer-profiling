"""存储无关的数据访问接口。"""

from __future__ import annotations

from typing import Any, Protocol

import pandas as pd

from .models import MetricQuery
from .validation import ValidationReport


class DataRepository(Protocol):
    def get_geojson(self) -> dict[str, Any]: ...

    def get_metric_catalog(self, data_mode: str) -> pd.DataFrame: ...

    def get_mock_profiles(self, metric_catalog: pd.DataFrame) -> pd.DataFrame: ...

    def get_indicator_definitions(self) -> pd.DataFrame: ...

    def get_v1_metrics(self) -> pd.DataFrame: ...

    def get_metric_records(self, query: MetricQuery | None = None) -> pd.DataFrame: ...

    def validate_import(self, records: pd.DataFrame) -> ValidationReport: ...

    def stage_import(self, records: pd.DataFrame) -> pd.DataFrame: ...
