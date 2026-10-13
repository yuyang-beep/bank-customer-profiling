"""数据读取、校验与 GeoJSON 中文名称增强。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_PROFILE_COLUMNS = {"province_name", "data_year", "data_source"}
REQUIRED_METRIC_COLUMNS = {
    "key", "label", "category", "unit", "format", "colorscale", "data_mode"
}
REQUIRED_REAL_COLUMNS = {
    "province_name",
    "province_code",
    "year",
    "metric_key",
    "metric_name",
    "value",
    "unit",
    "module",
    "source_name",
    "source_url",
    "statistical_period",
    "statistical_scope",
    "verification_status",
    "verification_note",
    "is_core_2024",
    "is_derived",
    "display_status",
    "yellow_marked",
    "source_cell",
}
VERIFIED_STATUSES = {"verified", "verified_cross_year"}


def load_table(path: str | Path) -> pd.DataFrame:
    """读取 CSV 或 Excel。后续切换真实数据时不需修改地图代码。"""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"不支持的数据格式: {suffix}")


def load_metric_catalog(path: str | Path, data_mode: str | None = None) -> pd.DataFrame:
    catalog = load_table(path)
    missing = REQUIRED_METRIC_COLUMNS - set(catalog.columns)
    if missing:
        raise ValueError(f"指标配置缺少字段: {sorted(missing)}")
    if catalog.duplicated(["data_mode", "key"]).any():
        raise ValueError("指标 key 必须唯一")
    if data_mode is not None:
        catalog = catalog.loc[catalog["data_mode"] == data_mode].reset_index(drop=True)
        if catalog.empty:
            raise ValueError(f"指标配置中没有 {data_mode} 模式")
    return catalog


def load_profiles(path: str | Path, metric_catalog: pd.DataFrame) -> pd.DataFrame:
    profiles = load_table(path)
    required = REQUIRED_PROFILE_COLUMNS | set(metric_catalog["key"])
    missing = required - set(profiles.columns)
    if missing:
        raise ValueError(f"画像数据缺少字段: {sorted(missing)}")
    if profiles["province_name"].duplicated().any():
        raise ValueError("画像数据中的省份名称必须唯一")
    return profiles


def load_real_records(path: str | Path) -> pd.DataFrame:
    """读取已核验真实数据长表，保留每条记录的年份和口径。"""
    records = load_table(path)
    missing = REQUIRED_REAL_COLUMNS - set(records.columns)
    if missing:
        raise ValueError(f"真实数据缺少字段: {sorted(missing)}")
    if not records["verification_status"].isin(VERIFIED_STATUSES).all():
        invalid = sorted(set(records["verification_status"]) - VERIFIED_STATUSES)
        raise ValueError(f"真实数据含未通过核验的状态: {invalid}")
    if records.duplicated(["province_name", "year", "metric_key"]).any():
        raise ValueError("真实数据的省份、年份和指标必须唯一")
    records["year"] = pd.to_numeric(records["year"], errors="raise").astype(int)
    records["value"] = pd.to_numeric(records["value"], errors="raise")
    for column in ["is_core_2024", "is_derived", "yellow_marked"]:
        records[column] = records[column].map(
            lambda value: value if isinstance(value, bool) else str(value).lower() == "true"
        )
    invalid_core = records["is_core_2024"] & records["year"].ne(2024)
    if invalid_core.any():
        raise ValueError("2024 核心画像中不能包含其他年份记录")
    invalid_active = records["display_status"].eq("active") & (
        ~records["yellow_marked"]
        | ~records["verification_status"].isin(VERIFIED_STATUSES)
    )
    if invalid_active.any():
        raise ValueError("active 记录必须来自黄色单元格且已经核验")
    return records


def build_real_map_profiles(
    records: pd.DataFrame, metric_catalog: pd.DataFrame, baseline_year: int = 2024
) -> pd.DataFrame:
    """仅将基准年已核验记录透视为地图宽表。"""
    metric_keys = set(metric_catalog["key"])
    baseline = records.loc[
        records["year"].eq(baseline_year)
        & records["verification_status"].isin(VERIFIED_STATUSES)
        & records["metric_key"].isin(metric_keys)
        & records["display_status"].eq("active")
    ]
    if baseline.empty:
        return pd.DataFrame(columns=["province_name", *metric_catalog["key"]])
    profiles = baseline.pivot(
        index="province_name", columns="metric_key", values="value"
    ).reset_index()
    profiles.columns.name = None
    for key in metric_catalog["key"]:
        if key not in profiles:
            profiles[key] = pd.NA
    profiles["data_year"] = baseline_year
    profiles["data_source"] = "已核验真实数据"
    return profiles


def build_v1_metric_catalog(metrics: pd.DataFrame) -> pd.DataFrame:
    """由同步生成的V1清单构建地图指标配置，不硬编码指标名称。"""
    rows = []
    colorscales = ["Blues", "YlGnBu", "Teal", "YlOrRd", "PuBuGn", "Viridis"]
    for index, (_, record) in enumerate(metrics.sort_values("display_order").iterrows()):
        value = float(record["value"])
        rows.append(
            {
                "key": record["metric_key"],
                "label": record["metric_name"],
                "category": "V1核心指标",
                "unit": record["unit"],
                "format": "{:,.0f}" if value.is_integer() else "{:,.1f}",
                "colorscale": colorscales[index % len(colorscales)],
                "data_mode": "real",
                "baseline_year": int(record["year"]),
            }
        )
    return pd.DataFrame(rows)


def build_v1_map_profiles(metrics: pd.DataFrame) -> pd.DataFrame:
    """将V1黄色指标长表转为地图使用的宽表；待核验值仍保留。"""
    profiles = metrics.pivot(
        index="province_name", columns="metric_key", values="value"
    ).reset_index()
    profiles.columns.name = None
    return profiles


def load_enriched_geojson(
    geojson_path: str | Path, crosswalk_path: str | Path
) -> dict[str, Any]:
    with Path(geojson_path).open(encoding="utf-8") as file:
        geojson = json.load(file)

    crosswalk = load_table(crosswalk_path)
    mapping = dict(zip(crosswalk["geo_name"], crosswalk["province_name"], strict=True))
    missing_names: list[str] = []
    for feature in geojson.get("features", []):
        geo_name = feature.get("properties", {}).get("shapeName")
        province_name = mapping.get(geo_name)
        if province_name is None:
            missing_names.append(str(geo_name))
            continue
        feature["properties"]["province_name"] = province_name

    if missing_names:
        raise ValueError(f"名称对照表缺少: {missing_names}")
    validate_geojson(geojson)
    return geojson


def _iter_positions(coordinates: Any):
    """递归产生 GeoJSON 坐标点（经度、纬度）。"""
    if (
        isinstance(coordinates, list)
        and len(coordinates) >= 2
        and isinstance(coordinates[0], (int, float))
        and isinstance(coordinates[1], (int, float))
    ):
        yield float(coordinates[0]), float(coordinates[1])
        return
    if isinstance(coordinates, list):
        for item in coordinates:
            yield from _iter_positions(item)


def validate_geojson(geojson: dict[str, Any]) -> None:
    """检查原型所需的省级要素、几何类型与 RFC 7946 坐标范围。"""
    features = geojson.get("features", [])
    if len(features) < 31:
        raise ValueError(f"GeoJSON 省级要素数量异常: {len(features)}")

    names: list[str] = []
    point_count = 0
    for feature in features:
        properties = feature.get("properties", {})
        name = properties.get("province_name")
        if not name:
            raise ValueError("GeoJSON 要素缺少 province_name")
        names.append(name)

        geometry = feature.get("geometry", {})
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"{name} 的几何类型不支持: {geometry.get('type')}")
        for longitude, latitude in _iter_positions(geometry.get("coordinates")):
            point_count += 1
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                raise ValueError(f"{name} 含有非法坐标: {longitude}, {latitude}")

    if len(names) != len(set(names)):
        raise ValueError("GeoJSON 中文省份名称不唯一")
    if point_count == 0:
        raise ValueError("GeoJSON 没有可用坐标")


def province_names_from_geojson(geojson: dict[str, Any]) -> list[str]:
    return sorted(
        feature["properties"]["province_name"] for feature in geojson["features"]
    )
