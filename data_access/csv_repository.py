"""CSV 存储适配器。Dashboard 不需要知道具体文件名。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from utils.data_loader import (
    load_enriched_geojson,
    load_metric_catalog,
    load_profiles,
)

from .models import MetricQuery
from .validation import (
    ValidationReport,
    apply_versioned_import,
    normalize_records,
    validate_records,
)


class CsvDataRepository:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self._paths = {
            "metric_catalog": self.data_dir / "metric_catalog.csv",
            "mock_profiles": self.data_dir / "mock_province_profiles.csv",
            "real_metrics": self.data_dir / "real_province_metrics.csv",
            "indicator_definitions": self.data_dir / "indicator_definitions.csv",
            "v1_metrics": self.data_dir / "v1_xinjiang_metrics.csv",
            "geojson": self.data_dir / "china_adm1.geojson",
            "crosswalk": self.data_dir / "province_crosswalk.csv",
        }

    def get_geojson(self) -> dict[str, Any]:
        return load_enriched_geojson(self._paths["geojson"], self._paths["crosswalk"])

    def get_metric_catalog(self, data_mode: str) -> pd.DataFrame:
        return load_metric_catalog(self._paths["metric_catalog"], data_mode)

    def get_mock_profiles(self, metric_catalog: pd.DataFrame) -> pd.DataFrame:
        return load_profiles(self._paths["mock_profiles"], metric_catalog)

    def get_indicator_definitions(self) -> pd.DataFrame:
        definitions = pd.read_csv(self._paths["indicator_definitions"])
        required = {
            "metric_key", "metric_name", "unit", "module", "value_type",
            "display_status", "yellow_marked", "source_cell", "status_reason",
            "is_core_indicator", "display_order", "reference_year", "source_name",
        }
        missing = required - set(definitions.columns)
        if missing:
            raise ValueError(f"指标定义表缺少字段: {sorted(missing)}")
        if definitions["metric_key"].duplicated().any():
            raise ValueError("指标定义表的 metric_key 必须唯一")
        if not definitions["display_status"].isin(
            {"active", "pending", "inactive"}
        ).all():
            raise ValueError("指标定义表含不支持的展示状态")
        return definitions

    def get_v1_metrics(self) -> pd.DataFrame:
        metrics = pd.read_csv(
            self._paths["v1_metrics"], dtype={"province_code": "string"}
        )
        required = {
            "province_name", "province_code", "source_cell", "metric_key",
            "metric_name", "value", "unit", "year", "verification_status",
            "source_name", "source_url", "verification_note", "display_order",
        }
        missing = required - set(metrics.columns)
        if missing:
            raise ValueError(f"V1指标清单缺少字段: {sorted(missing)}")
        if len(metrics) != 6:
            raise ValueError(f"V1指标必须恰好为6项，当前为{len(metrics)}项")
        if metrics["source_cell"].duplicated().any() or metrics["metric_key"].duplicated().any():
            raise ValueError("V1指标的单元格和指标代码必须唯一")
        metrics["value"] = pd.to_numeric(metrics["value"], errors="raise")
        metrics["year"] = pd.to_numeric(metrics["year"], errors="raise").astype(int)
        return metrics.sort_values("display_order").reset_index(drop=True)

    def _read_all_records(self) -> pd.DataFrame:
        records = pd.read_csv(self._paths["real_metrics"], dtype={"province_code": "string"})
        records = normalize_records(records)
        validate_records(records, self.get_indicator_definitions()).raise_for_errors()
        return records

    def get_metric_records(self, query: MetricQuery | None = None) -> pd.DataFrame:
        query = query or MetricQuery()
        records = self._read_all_records()
        if query.current_only:
            records = records.loc[records["version_status"].eq("current")]
        filters = {
            "province_code": query.province_codes,
            "year": query.years,
            "metric_key": query.metric_keys,
            "statistical_scope": query.statistical_scopes,
            "verification_status": query.verification_statuses,
            "display_status": query.display_statuses,
        }
        for column, accepted in filters.items():
            if accepted:
                records = records.loc[records[column].isin(accepted)]
        return records.reset_index(drop=True)

    def validate_import(self, records: pd.DataFrame) -> ValidationReport:
        return validate_records(records, self.get_indicator_definitions())

    def stage_import(self, records: pd.DataFrame) -> pd.DataFrame:
        """准备导入结果供复核，不覆盖 CSV。"""
        return apply_versioned_import(
            self._read_all_records(), records, self.get_indicator_definitions()
        )
