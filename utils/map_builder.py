"""Plotly 地图构建逻辑，与 Streamlit 页面状态分离。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go


# 在约 1000×500 px 的桌面主栏中实际渲染验证。不设置 layout.map.bounds：
# bounds 是最大可移动范围，在宽而矮的容器中会强制缩放并裁切南北边界。
CHINA_CENTER = {"lon": 104.0, "lat": 36.0}
CHINA_ZOOM = 2.7


def build_choropleth(
    geojson: dict[str, Any],
    profiles: pd.DataFrame,
    metric: pd.Series,
    selected_province: str | None = None,
    source_label: str = "Mock Data",
) -> go.Figure:
    """生成省级分级设色图。指标的名称、单位和配色均来自配置表。"""
    metric_key = metric["key"]
    available = profiles.loc[profiles[metric_key].notna()].copy()
    geo_names = [f["properties"]["province_name"] for f in geojson["features"]]

    figure = go.Figure()
    figure.add_trace(
        go.Choroplethmap(
            geojson=geojson,
            featureidkey="properties.province_name",
            locations=geo_names,
            z=[0] * len(geo_names),
            colorscale=[[0, "#E5E7EB"], [1, "#E5E7EB"]],
            showscale=False,
            marker_line_color="#F8FAFC",
            marker_line_width=0.9,
            customdata=geo_names,
            hovertemplate="<b>%{location}</b><br>当前指标：暂无数据<extra></extra>",
            name="暂无数据",
        )
    )

    formatted_values = [
        f"{metric['format'].format(value)} {metric['unit']}"
        for value in available[metric_key]
    ]
    figure.add_trace(
        go.Choroplethmap(
            geojson=geojson,
            featureidkey="properties.province_name",
            locations=available["province_name"],
            z=available[metric_key],
            colorscale=metric["colorscale"],
            marker_line_color="#F8FAFC",
            marker_line_width=0.9,
            colorbar={
                "title": {"text": metric["unit"], "side": "top"},
                "thickness": 10,
                "len": 0.54,
                "x": 0.98,
                "xpad": 4,
                "outlinewidth": 0,
                "tickfont": {"size": 11, "color": "#64748B"},
            },
            customdata=formatted_values,
            hovertemplate=(
                "<b>%{location}</b><br>"
                + metric["label"]
                + "：%{customdata}<br><span style='color:#6B7280'>"
                + source_label
                + "</span>"
                + "<extra></extra>"
            ),
            name=metric["label"],
        )
    )

    if selected_province:
        figure.add_trace(
            go.Choroplethmap(
                geojson=geojson,
                featureidkey="properties.province_name",
                locations=[selected_province],
                z=[1],
                colorscale=[
                    [0, "rgba(217,244,238,0.52)"],
                    [1, "rgba(217,244,238,0.52)"],
                ],
                showscale=False,
                marker_line_color="#0F3D5E",
                marker_line_width=2.6,
                hoverinfo="skip",
                name="已选省份",
            )
        )

    figure.update_layout(
        map={
            "style": "white-bg",
            "center": CHINA_CENTER,
            "zoom": CHINA_ZOOM,
        },
        height=470,
        margin={"l": 0, "r": 6, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel={
            "bgcolor": "white",
            "bordercolor": "#CBD5E1",
            "font_size": 13,
            "font_color": "#0F172A",
        },
        showlegend=False,
        dragmode=False,
        clickmode="event+select",
        uirevision=f"map-{source_label}-{metric_key}",
    )
    return figure
