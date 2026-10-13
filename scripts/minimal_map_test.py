"""脱离 Streamlit 的最小中国省级 GeoJSON 渲染测试。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data_loader import load_enriched_geojson, province_names_from_geojson
from utils.map_builder import CHINA_CENTER, CHINA_ZOOM


def build_minimal_figure() -> go.Figure:
    geojson = load_enriched_geojson(
        ROOT / "data/china_adm1.geojson",
        ROOT / "data/province_crosswalk.csv",
    )
    names = province_names_from_geojson(geojson)
    figure = go.Figure(
        go.Choroplethmap(
            geojson=geojson,
            locations=names,
            featureidkey="properties.province_name",
            z=list(range(len(names))),
            colorscale="Tealgrn",
            marker_line_color="white",
            marker_line_width=1,
            showscale=False,
            hovertemplate="%{location}<extra></extra>",
        )
    )
    figure.update_layout(
        map={
            "style": "white-bg",
            "center": CHINA_CENTER,
            "zoom": CHINA_ZOOM,
        },
        width=1000,
        height=620,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return figure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/china_adm1_minimal.html"),
        help="独立 HTML 输出路径",
    )
    args = parser.parse_args()
    figure = build_minimal_figure()
    figure.write_html(args.output, include_plotlyjs=True, auto_open=False)
    print(f"features_rendered={len(figure.data[0].locations)}")
    print(f"trace_type={figure.data[0].type}")
    print(f"output={args.output.resolve()}")


if __name__ == "__main__":
    main()
