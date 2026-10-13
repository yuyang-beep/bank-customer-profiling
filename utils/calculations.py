"""跨指标计算守卫：仅允许同省、同年、同口径的已核验数据参与比值。"""

from __future__ import annotations

import pandas as pd


PROHIBITED_HOUSEHOLD_DERIVATIONS = {
    "household_deposits_per_capita_yuan",
    "household_loan_deposit_ratio",
}


def assert_no_unverified_household_derivations(records: pd.DataFrame) -> None:
    """当缺少住户存贷款存量口径时，拒绝伪装成住户派生指标。"""
    present = PROHIBITED_HOUSEHOLD_DERIVATIONS.intersection(records["metric_key"])
    if present:
        raise ValueError(f"存在未经授权的住户派生指标: {sorted(present)}")


def calculate_same_year_ratio(
    records: pd.DataFrame,
    province: str,
    year: int,
    numerator_key: str,
    denominator_key: str,
) -> float:
    """对明确指定的同年已核验记录计算比值，不自动跨年匹配。"""
    selected = records.loc[
        records["province_name"].eq(province)
        & records["year"].eq(year)
        & records["metric_key"].isin([numerator_key, denominator_key])
        & records["verification_status"].isin(["verified", "verified_cross_year"])
    ]
    values = selected.set_index("metric_key")["value"]
    missing = {numerator_key, denominator_key} - set(values.index)
    if missing:
        raise ValueError(f"缺少同年计算输入: {sorted(missing)}")
    denominator = float(values[denominator_key])
    if denominator == 0:
        raise ValueError("分母不能为 0")
    return float(values[numerator_key]) / denominator
