from pathlib import Path
import os
import tempfile
import unittest

import pandas as pd

from data_access import create_repository
from scripts.sync_v1_from_excel import extract_metrics, find_latest_excel, write_csv
from utils.data_loader import build_v1_map_profiles, build_v1_metric_catalog


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "v1_review_metadata.csv"
EXCEL_PATH = Path(os.environ["V1_EXCEL_PATH"]) if os.getenv("V1_EXCEL_PATH") else None


def require_source_excel() -> Path:
    if EXCEL_PATH is None or not EXCEL_PATH.exists():
        raise unittest.SkipTest("未设置V1_EXCEL_PATH；跳过原始Excel集成检查")
    return EXCEL_PATH


class V1SyncTests(unittest.TestCase):
    def test_latest_excel_yellow_metrics_are_exactly_six(self) -> None:
        excel = require_source_excel()
        metrics = extract_metrics(excel, REVIEW)

        self.assertEqual([row["source_cell"] for row in metrics], ["D35", "I35", "L35", "N35", "Q35", "Z35"])
        self.assertEqual(
            [row["metric_name"] for row in metrics],
            ["常住人口", "居民人均可支配收入", "住户存款余额", "居民人均消费支出", "住户贷款余额", "人均GDP"],
        )
        self.assertEqual([row["value"] for row in metrics], [2623, 30899, 35807.9, 19715, 33287.7, 81574])
        self.assertEqual([row["year"] for row in metrics], [2024, 2024, 2024, 2023, 2024, 2025])

    def test_pending_values_are_preserved_with_scope_warnings(self) -> None:
        metrics = extract_metrics(require_source_excel(), REVIEW)
        pending = {row["metric_name"]: row for row in metrics if row["verification_status"] == "pending"}

        self.assertEqual(pending["住户存款余额"]["value"], 35807.9)
        self.assertIn("不能作为住户存款使用", pending["住户存款余额"]["verification_note"])
        self.assertEqual(pending["住户贷款余额"]["value"], 33287.7)
        self.assertIn("不能作为住户贷款使用", pending["住户贷款余额"]["verification_note"])
        self.assertIn("年份尚未统一", pending["人均GDP"]["verification_note"])

    def test_sync_output_can_be_reloaded_without_dashboard_changes(self) -> None:
        metrics = extract_metrics(require_source_excel(), REVIEW)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "v1.csv"
            write_csv(metrics, output)
            reloaded = pd.read_csv(output)
        self.assertEqual(len(reloaded), 6)
        self.assertEqual(set(reloaded["verification_status"]), {"verified", "pending"})

    def test_dashboard_catalog_and_map_are_generated_from_v1_file(self) -> None:
        repository = create_repository(ROOT)
        metrics = repository.get_v1_metrics()
        catalog = build_v1_metric_catalog(metrics)
        profiles = build_v1_map_profiles(metrics)

        self.assertEqual(len(catalog), 6)
        self.assertEqual(catalog["label"].tolist(), metrics["metric_name"].tolist())
        self.assertEqual(profiles["province_name"].tolist(), ["新疆维吾尔自治区"])
        self.assertEqual(profiles.loc[0, "household_deposits_yi"], 35807.9)
        self.assertEqual(profiles.loc[0, "household_loans_yi"], 33287.7)


if __name__ == "__main__":
    unittest.main()
