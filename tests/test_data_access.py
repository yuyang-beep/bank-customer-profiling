from pathlib import Path
import unittest

import pandas as pd

from data_access import MetricQuery, create_repository


ROOT = Path(__file__).resolve().parents[1]


class DataAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = create_repository(ROOT)
        cls.records = cls.repository.get_metric_records(MetricQuery(current_only=False))

    def test_query_filters_current_records(self) -> None:
        result = self.repository.get_metric_records(
            MetricQuery(
                province_codes=("650000",),
                years=(2024,),
                metric_keys=("population_wan",),
            )
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["value"], 2622.8)
        self.assertEqual(result.iloc[0]["version_status"], "current")

    def test_query_returns_only_active_display_records(self) -> None:
        result = self.repository.get_metric_records(
            MetricQuery(display_statuses=("active",))
        )
        self.assertEqual(
            set(result["metric_key"]),
            {"population_wan", "disposable_income_yuan", "consumption_expenditure_yuan"},
        )
        self.assertTrue(result["yellow_marked"].all())

    def test_core_indicator_definitions_are_exactly_the_agreed_six(self) -> None:
        definitions = self.repository.get_indicator_definitions()
        core = definitions.loc[
            definitions["is_core_indicator"].astype(str).str.lower().eq("true")
        ].sort_values("display_order")

        self.assertEqual(
            core["metric_name"].tolist(),
            [
                "住户贷款余额",
                "常住人口",
                "居民人均可支配收入",
                "住户存款余额",
                "居民人均消费支出",
                "人均地区生产总值（人均GDP）",
            ],
        )
        self.assertEqual(
            core["display_status"].tolist(),
            ["pending", "active", "active", "pending", "active", "pending"],
        )
        regional_names = set(
            definitions.loc[
                definitions["module"].eq("区域金融市场"), "metric_name"
            ]
        )
        self.assertEqual(
            regional_names,
            {"金融机构本外币各项存款余额", "金融机构本外币各项贷款余额"},
        )
        self.assertTrue(
            definitions.loc[
                definitions["module"].eq("区域金融市场"), "is_core_indicator"
            ].astype(str).str.lower().eq("false").all()
        )

    def test_valid_versioned_import_supersedes_prior_record(self) -> None:
        incoming = self.records.loc[
            self.records["metric_key"].eq("population_wan")
        ].head(1).copy()
        incoming["value"] = 2622.9
        incoming["record_version"] = 2
        incoming["supersedes_version"] = 1
        incoming["ingested_at"] = "2026-10-13T00:00:00+08:00"

        staged = self.repository.stage_import(incoming)
        versions = staged.loc[
            staged["metric_key"].eq("population_wan"),
            ["record_version", "version_status", "value"],
        ].sort_values("record_version")
        self.assertEqual(versions["record_version"].tolist(), [1, 2])
        self.assertEqual(versions["version_status"].tolist(), ["superseded", "current"])
        self.assertEqual(versions.iloc[1]["value"], 2622.9)

    def test_duplicate_record_is_rejected(self) -> None:
        duplicate = pd.concat([self.records.head(1), self.records.head(1)], ignore_index=True)
        report = self.repository.validate_import(duplicate)
        self.assertFalse(report.is_valid)
        self.assertIn("duplicate_version", {issue.code for issue in report.errors})

    def test_verified_missing_value_is_rejected(self) -> None:
        missing = self.records.head(1).copy()
        missing["value"] = pd.NA
        report = self.repository.validate_import(missing)
        self.assertIn("verified_missing_value", {issue.code for issue in report.errors})

    def test_unit_mismatch_is_rejected(self) -> None:
        wrong_unit = self.records.head(1).copy()
        wrong_unit["unit"] = "亿元"
        report = self.repository.validate_import(wrong_unit)
        self.assertIn("unit_mismatch", {issue.code for issue in report.errors})


if __name__ == "__main__":
    unittest.main()
