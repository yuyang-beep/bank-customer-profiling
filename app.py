"""全国潜在银行客群画像地图 Prototype V0.2。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from data_access import create_repository

from utils.data_loader import (
    build_v1_map_profiles,
    build_v1_metric_catalog,
    province_names_from_geojson,
)
from utils.map_builder import build_choropleth
from utils.ui_components import (
    inject_theme,
    render_footer,
    render_header,
    render_profile,
    render_real_profile,
)


BASE_DIR = Path(__file__).resolve().parent
repository = create_repository(BASE_DIR)

st.set_page_config(
    page_title="全国潜在银行客群画像",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data
def load_app_data(data_revision: int) -> tuple[
    dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    del data_revision  # 仅用于使 Streamlit 缓存随V1清单更新时间失效。
    mock_catalog = repository.get_metric_catalog("mock")
    mock_profiles = repository.get_mock_profiles(mock_catalog)
    v1_metrics = repository.get_v1_metrics()
    geojson = repository.get_geojson()
    return geojson, mock_profiles, mock_catalog, v1_metrics


def extract_clicked_province(event: Any) -> str | None:
    """兼容 Streamlit Plotly selection 的字典和类字典返回值。"""
    if not event:
        return None
    selection = event.get("selection", {}) if hasattr(event, "get") else {}
    points = selection.get("points", []) if hasattr(selection, "get") else []
    if not points:
        return None
    point = points[0]
    return point.get("location") or point.get("customdata")


v1_data_revision = (BASE_DIR / "data" / "v1_xinjiang_metrics.csv").stat().st_mtime_ns
geojson, mock_profiles, mock_catalog, v1_metrics = load_app_data(v1_data_revision)
all_provinces = province_names_from_geojson(geojson)
inject_theme()

if "selected_province" not in st.session_state:
    st.session_state.selected_province = "北京市"
if "active_data_mode" not in st.session_state:
    st.session_state.active_data_mode = "mock"

data_mode = st.session_state.active_data_mode
render_header(data_mode)
mode_label = st.radio(
    "数据模式",
    ["演示数据（Mock）", "新疆 V1 数据原型"],
    index=0 if data_mode == "mock" else 1,
    horizontal=True,
    label_visibility="collapsed",
    key="data_mode_radio",
)
requested_mode = "mock" if mode_label.startswith("演示") else "real"
if requested_mode != data_mode:
    st.session_state.active_data_mode = requested_mode
    st.session_state.selected_province = (
        "北京市" if requested_mode == "mock" else "新疆维吾尔自治区"
    )
    st.rerun()

catalog = mock_catalog if data_mode == "mock" else build_v1_metric_catalog(v1_metrics)
profiles = mock_profiles if data_mode == "mock" else build_v1_map_profiles(v1_metrics)
source_label = "Mock Data"

if data_mode == "real":
    st.warning("当前为V1数据展示原型，部分指标尚待核验，不应用于正式金融分析。")

with st.container(border=True):
    metric_col, province_col, help_col = st.columns([1.05, 1.05, 2.4], vertical_alignment="bottom")
    with metric_col:
        metric_label = st.selectbox("地图指标", catalog["label"].tolist())
    with province_col:
        selected = st.selectbox(
            "省份选择",
            all_provinces,
            index=all_provinces.index(st.session_state.selected_province),
            key=f"province_dropdown_{data_mode}",
        )
        if selected != st.session_state.selected_province:
            st.session_state.selected_province = selected
            st.rerun()
    with help_col:
        st.caption("可使用下拉框稳定选择省份，或点击地图区域更新画像。")

metric = catalog.loc[catalog["label"] == metric_label].iloc[0]
if data_mode == "real":
    selected_record = v1_metrics.loc[v1_metrics["metric_key"].eq(metric["key"])].iloc[0]
    status_label = "已核验" if selected_record["verification_status"] == "verified" else "待核验"
    source_label = f"{int(metric['baseline_year'])} V1 Excel原始值 · {status_label}"

with st.container(border=True):
    st.markdown('<div class="v02-section-label">全国省级分布</div>', unsafe_allow_html=True)
    figure = build_choropleth(
        geojson, profiles, metric, st.session_state.selected_province,
        source_label=source_label,
    )
    event = st.plotly_chart(
        figure,
        width="stretch",
        key=f"province_map_{data_mode}_{metric['key']}",
        on_select="rerun",
        selection_mode="points",
        config={"displayModeBar": False, "scrollZoom": False, "responsive": True},
    )
    clicked = extract_clicked_province(event)
    if clicked in all_provinces and clicked != st.session_state.selected_province:
        st.session_state.selected_province = clicked
        st.rerun()
    st.caption(
        "颜色越深代表当前指标值越高；灰色表示暂无数据。"
        + ("当前为 Mock Data。" if data_mode == "mock" else f"V1模式显示Excel黄色指标原始值；当前指标为{int(metric['baseline_year'])}年。")
    )

with st.container(border=True):
    if data_mode == "mock":
        render_profile(st.session_state.selected_province, profiles, catalog, metric)
    else:
        render_real_profile(st.session_state.selected_province, v1_metrics)

st.divider()
render_footer(data_mode)
st.caption("边界仅用于可视化原型，不代表对行政边界的法律认定。")
