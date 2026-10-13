from pathlib import Path
import unittest

import pandas as pd

from utils.data_loader import (
    build_real_map_profiles,
    load_enriched_geojson,
    load_metric_catalog,
    load_profiles,
    load_real_records,
    province_names_from_geojson,
)
from utils.calculations import (
    assert_no_unverified_household_derivations,
    calculate_same_year_ratio,
)
from utils.map_builder import CHINA_CENTER, CHINA_ZOOM, build_choropleth


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class DashboardDataTests(unittest.TestCase):
    def test_data_contract_and_map_build(self) -> None:
        catalog = load_metric_catalog(DATA / "metric_catalog.csv", "mock")
        profiles = load_profiles(DATA / "mock_province_profiles.csv", catalog)
        geojson = load_enriched_geojson(
            DATA / "china_adm1.geojson", DATA / "province_crosswalk.csv"
        )

        self.assertEqual(len(catalog), 3)
        self.assertEqual(len(profiles), 31)
        self.assertEqual(len(province_names_from_geojson(geojson)), 34)
        self.assertTrue(profiles["data_source"].eq("Mock Data").all())

        figure = build_choropleth(geojson, profiles, catalog.iloc[0], "北京市")
        self.assertEqual(len(figure.data), 3)
        self.assertEqual(len(figure.data[0].locations), 34)
        self.assertEqual(len(figure.data[1].locations), 31)
        self.assertTrue(all(trace.type == "choroplethmap" for trace in figure.data))
        layout = figure.to_plotly_json()["layout"]["map"]
        self.assertEqual(layout["style"], "white-bg")
        self.assertNotIn("bounds", layout)
        self.assertEqual(figure.layout.height, 470)
        self.assertEqual(layout["center"], CHINA_CENTER)
        self.assertEqual(layout["zoom"], CHINA_ZOOM)

    def test_real_data_contract_and_2024_map(self) -> None:
        catalog = load_metric_catalog(DATA / "metric_catalog.csv", "real")
        records = load_real_records(DATA / "real_province_metrics.csv")
        profiles = build_real_map_profiles(records, catalog, baseline_year=2024)

        self.assertEqual(len(records), 9)
        self.assertEqual(set(records["year"]), {2020, 2023, 2024, 2025})
        self.assertTrue(records.loc[records["is_core_2024"], "year"].eq(2024).all())
        self.assertEqual(profiles["province_name"].tolist(), ["新疆维吾尔自治区"])
        self.assertEqual(profiles.loc[0, "population_wan"], 2622.8)
        self.assertEqual(profiles.loc[0, "disposable_income_yuan"], 30899)
        self.assertNotIn("financial_deposits_total_yi", set(catalog["key"]))
        self.assertNotIn("financial_loans_total_yi", set(catalog["key"]))
        self.assertNotIn("北京市", set(profiles["province_name"]))
        assert_no_unverified_household_derivations(records)

    def test_only_active_yellow_verified_records_are_displayable(self) -> None:
        records = load_real_records(DATA / "real_province_metrics.csv")
        active = records.loc[records["display_status"].eq("active")]

        self.assertEqual(
            set(active["metric_key"]),
            {"population_wan", "disposable_income_yuan", "consumption_expenditure_yuan"},
        )
        self.assertTrue(active["yellow_marked"].all())
        self.assertTrue(
            active["verification_status"].isin({"verified", "verified_cross_year"}).all()
        )
        pending_keys = {
            "financial_deposits_total_yi",
            "financial_loans_total_yi",
            "gdp_per_capita_yuan",
        }
        self.assertTrue(
            records.loc[records["metric_key"].isin(pending_keys), "display_status"]
            .eq("pending")
            .all()
        )
        self.assertTrue(
            records.loc[~records["yellow_marked"], "display_status"]
            .eq("inactive")
            .all()
        )

    def test_2023_active_metric_keeps_its_own_year(self) -> None:
        catalog = load_metric_catalog(DATA / "metric_catalog.csv", "real")
        records = load_real_records(DATA / "real_province_metrics.csv")
        profiles = build_real_map_profiles(records, catalog, baseline_year=2023)

        self.assertEqual(profiles.loc[0, "consumption_expenditure_yuan"], 19715)
        self.assertEqual(profiles.loc[0, "data_year"], 2023)
        self.assertTrue(pd.isna(profiles.loc[0, "population_wan"]))

    def test_cross_year_ratio_is_not_implicitly_calculated(self) -> None:
        records = load_real_records(DATA / "real_province_metrics.csv")
        with self.assertRaisesRegex(ValueError, "缺少同年计算输入"):
            calculate_same_year_ratio(
                records,
                "新疆维吾尔自治区",
                2024,
                "consumption_expenditure_yuan",
                "disposable_income_yuan",
            )


if __name__ == "__main__":
    unittest.main()
