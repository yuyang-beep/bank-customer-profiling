# 数据说明

## `china_adm1.geojson`

- 数据集：geoBoundaries `gbOpen` 中国 ADM1 简化边界
- 边界 ID：`CHN-ADM1-43563684`
- 边界表示年份：2019
- 构建日期：2023-12-12
- 来源：geoBoundaries, Wikimedia Commons
- 分发许可：geoBoundaries `gbOpen`，CC BY 4.0；公开使用和上传需保留归属声明
- 下载日期：2026-10-11
- API：<https://www.geoboundaries.org/api/current/gbOpen/CHN/ADM1/>
- 文档：<https://www.geoboundaries.org/api.html>

说明：geoBoundaries `gbOpen` 要求使用时进行归属声明。本项目在 README、页面脚注、本文件及 `THIRD_PARTY_NOTICES.md` 中保留归属信息。该图层包含 34 个 ADM1 边界；本原型的 Mock 画像表仅为内地 31 个省级行政区提供演示值。

## `mock_province_profiles.csv`

全部数值是为交互原型手工构造的 **Mock Data**，不是真实统计数据，不应用于研究结论或金融决策。

## `metric_catalog.csv`

指标元数据：字段名、显示名称、类别、单位、格式、Plotly 配色和数据模式。`mock` 与 `real` 指标独立加载。

## `real_province_metrics.csv`

真实数据使用长表，每行为一个“省份—年份—指标”记录，并保留单位、统计时点、口径、来源 URL 和核验状态。

- 第一轮仅覆盖新疆，2024 年是核心画像基准年。
- 2020、2023 和 2025 年数据可展示，但不自动纳入 2024 年地图或比值计算。
- `financial_deposits_total_yi` 和 `financial_loans_total_yi` 是区域金融机构本外币各项余额，不是住户存贷款。
- 住户存贷款存量未核验前，不生成人均住户存款或住户贷存比。
- 业务标识为 `province_code + year + metric_key + statistical_scope`；`record_version` 区分历史版本。
- `version_status=current` 表示当前版本，`superseded` 表示已被更新版本取代。

## `indicator_definitions.csv`

真实指标字典，为每个 `metric_key` 定义标准名称、单位、模块和值类型。真实数据导入时使用该表进行单位校验。
