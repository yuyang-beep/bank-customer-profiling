"""Streamlit 页面组件，与数据处理和地图构建分离。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #F5F7FA; color: #172033; }
        [data-testid="stHeader"] { background: rgba(245, 247, 250, 0.92); }
        .block-container { max-width: 1500px; padding-top: .7rem; padding-bottom: 2rem; }
        h1, h2, h3 { color: #123B5D; letter-spacing: 0; }
        h1 { font-size: 1.62rem !important; line-height: 1.15 !important; margin-bottom: .2rem !important; }
        h3 { font-size: 1.05rem !important; margin: .05rem 0 .35rem !important; }
        [data-testid="stVerticalBlock"] { gap: .55rem; }
        [data-testid="stHorizontalBlock"] { gap: .8rem; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;
            border-color: #E2E8F0 !important;
            border-radius: 12px;
            box-shadow: 0 5px 18px rgba(15, 59, 94, 0.055);
        }
        [data-testid="stMetric"] {
            background: #F8FAFC;
            border: 1px solid #E7EDF3;
            border-radius: 9px;
            padding: .42rem .65rem;
        }
        [data-testid="stMetricLabel"] { color: #52647A; font-size: .78rem; }
        [data-testid="stMetricValue"] { color: #123B5D; font-size: 1.12rem; }
        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricValue"] > div {
            white-space: normal !important;
            overflow-wrap: anywhere;
            line-height: 1.3 !important;
        }
        .v02-kicker { color: #087F8C; font-size: .69rem; font-weight: 700; letter-spacing: .09em; }
        .v02-title { color: #123B5D; font-size: 1.62rem; line-height: 1.2; font-weight: 720; margin: .08rem 0 .28rem; }
        .v02-subtitle { color: #607186; font-size: .82rem; margin-top: -.25rem; }
        .v02-badges { display: flex; gap: .4rem; margin: .22rem 0 .48rem; }
        .v02-badge { border-radius: 999px; padding: .2rem .52rem; font-size: .68rem; font-weight: 650; }
        .v02-version { background: #DDF4F1; color: #08736F; }
        .v02-mock { background: #FFF3D7; color: #8A5A00; }
        .v02-real { background: #DDF4F1; color: #08736F; }
        .v02-section-label {
            display: block;
            position: relative;
            z-index: 2;
            min-height: 1.75rem;
            padding: .12rem 0 .55rem;
            color: #64748B;
            font-size: .76rem;
            font-weight: 700;
            line-height: 1.35;
            letter-spacing: .05em;
            text-transform: uppercase;
        }
        .v02-source { color: #64748B; font-size: .78rem; line-height: 1.55; }
        .v02-compact-note { background: #FFF8E8; color: #76520B; border: 1px solid #F4E2B9; border-radius: 8px; padding: .42rem .55rem; font-size: .72rem; line-height: 1.35; }
        .v02-real-note { background: #EEF8F6; color: #0B625F; border: 1px solid #CFEAE5; border-radius: 8px; padding: .42rem .55rem; font-size: .72rem; line-height: 1.35; }
        div[data-testid="stPlotlyChart"] { border-radius: 10px; overflow: hidden; }
        @media (max-width: 900px) {
            .block-container { padding: .65rem 1rem 1.5rem; }
            h1 { font-size: 1.55rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(data_mode: str) -> None:
    mode_badge = (
        '<span class="v02-badge v02-mock">Mock Data · 非真实统计</span>'
        if data_mode == "mock"
        else '<span class="v02-badge v02-real">V1 原型 · 含待核验指标</span>'
    )
    st.markdown('<div class="v02-kicker">PROVINCIAL MARKET OVERVIEW</div>', unsafe_allow_html=True)
    # 使用普通标题容器，避免部分 Chromium 缩放比例下 heading 锚点发生文字重叠。
    st.markdown('<div class="v02-title">全国潜在银行客群画像</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="v02-subtitle">中国省级市场指标的交互式可视化原型</div>'
        '<div class="v02-badges"><span class="v02-badge v02-version">Prototype V0.2</span>'
        + mode_badge
        + "</div>",
        unsafe_allow_html=True,
    )


def format_metric(value: Any, metric: pd.Series) -> str:
    if pd.isna(value):
        return "暂无数据"
    return f"{metric['format'].format(value)} {metric['unit']}"


def build_comparison_chart(
    province: str, row: pd.Series, profiles: pd.DataFrame, metric: pd.Series
) -> go.Figure:
    """仅比较当前指标与 Mock 样本中位数，不生成业务结论。"""
    key = metric["key"]
    median = profiles[key].median()
    values = [median, row[key]]
    labels = ["Mock 样本中位数", province]
    colors = ["#C9D5E2", "#159A9C"]
    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[metric["format"].format(value) for value in values],
            textposition="outside",
            hovertemplate="%{y}<br>%{x:,.0f} " + metric["unit"] + "<extra></extra>",
        )
    )
    max_value = max(values) if max(values) > 0 else 1
    figure.update_xaxes(visible=False, range=[0, max_value * 1.28])
    figure.update_yaxes(
        autorange="reversed", tickfont={"size": 11, "color": "#52647A"}, fixedrange=True
    )
    figure.update_layout(
        height=118,
        margin={"l": 4, "r": 10, "t": 2, "b": 2},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        bargap=0.42,
        font={"color": "#334155"},
    )
    return figure


def render_profile(
    province: str,
    profiles: pd.DataFrame,
    catalog: pd.DataFrame,
    active_metric: pd.Series,
) -> None:
    st.markdown('<div class="v02-section-label">当前省份</div>', unsafe_allow_html=True)
    st.markdown(f"### {province}")
    match = profiles.loc[profiles["province_name"] == province]
    if match.empty:
        st.info("暂无该省级行政区的演示画像数据。")
        st.caption("数据年份：暂无 · 数据来源：暂无")
        return

    row = match.iloc[0]
    for _, metric in catalog.iterrows():
        st.metric(metric["label"], format_metric(row[metric["key"]], metric))

    st.markdown('<div class="v02-section-label" style="margin-top:.25rem">当前指标对比</div>', unsafe_allow_html=True)
    st.plotly_chart(
        build_comparison_chart(province, row, profiles, active_metric),
        width="stretch",
        config={"displayModeBar": False},
        key=f"profile_comparison_{active_metric['key']}_{province}",
    )
    st.caption(f"数据年份：{row['data_year']} · 数据来源：{row['data_source']}")
    st.markdown(
        '<div class="v02-compact-note">全部数值为 Mock Data，仅演示界面与交互，不代表真实客群结论。</div>',
        unsafe_allow_html=True,
    )


def render_real_profile(province: str, metrics: pd.DataFrame) -> None:
    """严格以同步生成的六项黄色指标渲染3×2卡片。"""
    st.markdown('<div class="v02-section-label">当前省份</div>', unsafe_allow_html=True)
    st.markdown(f"### {province}")
    province_records = metrics.loc[metrics["province_name"].eq(province)].copy()
    template = metrics.sort_values("display_order").reset_index(drop=True)
    values_by_key = {row["metric_key"]: row for _, row in province_records.iterrows()}

    st.markdown(
        '<div class="v02-section-label" style="margin-top:.28rem">V1 黄色指标（六项）</div>',
        unsafe_allow_html=True,
    )
    for start in (0, 3):
        columns = st.columns(3, gap="medium")
        for column, (_, definition) in zip(columns, template.iloc[start : start + 3].iterrows()):
            record = values_by_key.get(definition["metric_key"])
            with column:
                with st.container(border=True):
                    if record is None:
                        st.metric(definition["metric_name"], "暂无数据")
                        st.caption(f"单位：{definition['unit']} · 年份：暂无 · 未接入")
                    else:
                        value = f"{record['value']:,.3f}".rstrip("0").rstrip(".")
                        st.metric(record["metric_name"], f"{value} {record['unit']}")
                        status = "已核验" if record["verification_status"] == "verified" else "待核验"
                        st.caption(f"{int(record['year'])}年 · {status}")
                        if status == "待核验":
                            st.warning(record["verification_note"])
                        elif record["verification_note"]:
                            st.caption(record["verification_note"])

    source_count = province_records["source_url"].nunique()
    if source_count:
        with st.expander("六项指标来源与核验状态"):
            for _, record in province_records.sort_values("display_order").iterrows():
                status = "已核验" if record["verification_status"] == "verified" else "待核验"
                st.markdown(
                    f"- **{record['metric_name']}**：{int(record['year'])}年，{record['unit']}，"
                    f"{status}。[来源]({record['source_url']})"
                )
    st.caption(f"V1指标：6项 · 当前省份已接入：{len(province_records)}项 · 来源：{source_count}个")
    st.markdown(
        '<div class="v02-real-note">指标选择来自最新Excel中新疆行的黄色单元格。待核验指标保留原始值并明确标注，不用于正式金融分析。</div>',
        unsafe_allow_html=True,
    )


def render_footer(data_mode: str = "mock") -> None:
    st.markdown("#### 数据与后续分析")
    info_col, source_col, future_col = st.columns(3)
    with info_col:
        st.markdown("**数据说明**")
        st.markdown(
            '<div class="v02-source">'
            + ("当前提供 31 个省级行政区的演示指标。" if data_mode == "mock" else "真实数据当前仅覆盖新疆；其他省份显示暂无数据。")
            + "</div>",
            unsafe_allow_html=True,
        )
    with source_col:
        st.markdown("**数据来源**")
        st.markdown(
            '<div class="v02-source">'
            + ("画像数值：Mock Data" if data_mode == "mock" else "画像数值：自治区统计局、人民银行新疆分行")
            + "<br>边界：geoBoundaries CHN ADM1（2019）</div>",
            unsafe_allow_html=True,
        )
    with future_col:
        st.markdown("**后续扩展**")
        st.markdown(
            '<div class="v02-source">可接入真实统计年份、新增指标、区域排名与多年趋势，当前不生成金融评分。</div>',
            unsafe_allow_html=True,
        )
