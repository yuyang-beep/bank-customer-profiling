"""真实指标长表的结构、版本、缺失值和单位校验。"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


BUSINESS_KEY = ["province_code", "year", "metric_key", "statistical_scope"]
VERSION_KEY = [*BUSINESS_KEY, "record_version"]
REQUIRED_COLUMNS = {
    "province_name", "province_code", "year", "metric_key", "metric_name",
    "value", "unit", "module", "source_name", "source_url",
    "statistical_period", "statistical_scope", "verification_status",
    "verification_note", "is_core_2024", "is_derived", "record_version",
    "version_status", "ingested_at", "supersedes_version",
    "display_status", "yellow_marked", "source_cell",
}
VERIFICATION_STATUSES = {"verified", "verified_cross_year", "pending", "rejected"}
VERSION_STATUSES = {"current", "superseded", "rejected"}
DISPLAY_STATUSES = {"active", "pending", "inactive"}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"
    rows: tuple[int, ...] = ()


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def add(self, code: str, message: str, rows=(), severity: str = "error") -> None:
        self.issues.append(ValidationIssue(code, message, severity, tuple(rows)))

    def raise_for_errors(self) -> None:
        if self.errors:
            details = "; ".join(f"{issue.code}: {issue.message}" for issue in self.errors)
            raise ValueError(details)


def normalize_records(records: pd.DataFrame) -> pd.DataFrame:
    normalized = records.copy()
    if "province_code" in normalized:
        normalized["province_code"] = normalized["province_code"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(6)
    for column in ["year", "record_version", "supersedes_version"]:
        if column in normalized:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce").astype("Int64")
    if "value" in normalized:
        normalized["value"] = pd.to_numeric(normalized["value"], errors="coerce")
    for column in ["is_core_2024", "is_derived", "yellow_marked"]:
        if column in normalized:
            normalized[column] = normalized[column].map(
                lambda value: value if isinstance(value, bool) else str(value).strip().lower() == "true"
            )
    return normalized


def validate_records(records: pd.DataFrame, definitions: pd.DataFrame) -> ValidationReport:
    report = ValidationReport()
    missing_columns = REQUIRED_COLUMNS - set(records.columns)
    if missing_columns:
        report.add("missing_columns", f"缺少字段: {sorted(missing_columns)}")
        return report

    data = normalize_records(records)
    required_values = [
        "province_name", "province_code", "year", "metric_key", "metric_name",
        "unit", "module", "statistical_period", "statistical_scope",
        "verification_status", "record_version", "version_status", "ingested_at",
    ]
    for column in required_values:
        bad = data[column].isna() | data[column].astype("string").str.strip().eq("")
        if bad.any():
            report.add("missing_value", f"{column} 存在缺失值", data.index[bad])

    verified = data["verification_status"].isin(["verified", "verified_cross_year"])
    for column in ["value", "source_name", "source_url"]:
        bad = verified & (data[column].isna() | data[column].astype("string").str.strip().eq(""))
        if bad.any():
            report.add("verified_missing_value", f"已核验记录缺少 {column}", data.index[bad])

    duplicate = data.duplicated(VERSION_KEY, keep=False)
    if duplicate.any():
        report.add("duplicate_version", "业务键与版本号重复", data.index[duplicate])

    current = data.loc[data["version_status"].eq("current")]
    duplicate_current = current.duplicated(BUSINESS_KEY, keep=False)
    if duplicate_current.any():
        report.add("multiple_current_versions", "同一业务键只能有一个 current 版本", current.index[duplicate_current])

    invalid_verification = ~data["verification_status"].isin(VERIFICATION_STATUSES)
    if invalid_verification.any():
        report.add("invalid_verification_status", "存在未支持的核验状态", data.index[invalid_verification])
    invalid_version = ~data["version_status"].isin(VERSION_STATUSES)
    if invalid_version.any():
        report.add("invalid_version_status", "存在未支持的版本状态", data.index[invalid_version])
    invalid_display = ~data["display_status"].isin(DISPLAY_STATUSES)
    if invalid_display.any():
        report.add("invalid_display_status", "存在未支持的展示状态", data.index[invalid_display])
    invalid_active = data["display_status"].eq("active") & (
        ~data["yellow_marked"] | ~verified
    )
    if invalid_active.any():
        report.add(
            "invalid_active_record",
            "active 记录必须来自黄色单元格且已经核验",
            data.index[invalid_active],
        )

    unit_map = definitions.set_index("metric_key")["unit"]
    unknown_metric = ~data["metric_key"].isin(unit_map.index)
    if unknown_metric.any():
        report.add("unknown_metric", "指标代码未在指标定义表中登记", data.index[unknown_metric])
    known = ~unknown_metric
    expected_units = data.loc[known, "metric_key"].map(unit_map)
    wrong_unit = data.loc[known, "unit"].ne(expected_units)
    if wrong_unit.any():
        report.add("unit_mismatch", "单位与指标定义不一致", data.loc[known].index[wrong_unit])

    invalid_core = data["is_core_2024"] & data["year"].ne(2024)
    if invalid_core.any():
        report.add("invalid_core_year", "2024 核心画像不能包含其他年份", data.index[invalid_core])
    return report


def apply_versioned_import(
    existing: pd.DataFrame, incoming: pd.DataFrame, definitions: pd.DataFrame
) -> pd.DataFrame:
    """在内存中准备版本化导入，不写入存储。"""
    old = normalize_records(existing)
    new = normalize_records(incoming)
    validate_records(new, definitions).raise_for_errors()

    prepared = old.copy()
    for _, row in new.iterrows():
        same_key = pd.Series(True, index=prepared.index)
        for column in BUSINESS_KEY:
            same_key &= prepared[column].eq(row[column])
        if (same_key & prepared["record_version"].eq(row["record_version"])).any():
            raise ValueError("导入版本已存在")
        if row["version_status"] == "current":
            prior = prepared.loc[same_key & prepared["version_status"].eq("current")]
            if not prior.empty:
                previous_version = int(prior["record_version"].max())
                if pd.isna(row["supersedes_version"]) or int(row["supersedes_version"]) != previous_version:
                    raise ValueError("新 current 版本必须正确声明 supersedes_version")
                if int(row["record_version"]) <= previous_version:
                    raise ValueError("新版本号必须大于现有版本")
                prepared.loc[prior.index, "version_status"] = "superseded"
    combined = pd.concat([prepared, new], ignore_index=True)
    validate_records(combined, definitions).raise_for_errors()
    return combined
