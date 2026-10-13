# Streamlit Community Cloud 部署检查报告

检查日期：2026-10-13

## 部署入口与环境

- 入口文件：`app.py`
- 从仓库根目录启动：`streamlit run app.py`
- Python：在 Community Cloud 的 Advanced settings 选择 Python 3.12
- Python依赖：根目录 `requirements.txt`
- 不需要 `packages.txt`、数据库、API Key或外部系统服务

## 云端运行必需文件

- `app.py`
- `requirements.txt`
- `data_access/`
- `utils/`
- `data/china_adm1.geojson`
- `data/province_crosswalk.csv`
- `data/mock_province_profiles.csv`
- `data/metric_catalog.csv`
- `data/v1_xinjiang_metrics.csv`
- `data/v1_review_metadata.csv`
- `THIRD_PARTY_NOTICES.md`

测试、同步脚本和文档建议一并上传，便于协作维护，但不是Dashboard启动必需文件。

## 数据路径与同步

Dashboard只读取项目内相对路径，不依赖MacBook路径、localhost接口或原始Excel。
部署使用已经生成的 `data/v1_xinjiang_metrics.csv`。原始Excel默认不上传。

本地更新流程：

1. 将最新Excel放入 `imports/`。
2. 运行 `python scripts/sync_v1_from_excel.py`。
3. 运行测试。
4. 人工复核 `data/v1_xinjiang_metrics.csv` 的六项指标与状态。
5. 经确认后提交生成的CSV和代码。

`data/v1_review_metadata.csv`独立保存核验状态，因此Excel新增数值不会自动变成“已核验”。

## 地图数据

GeoJSON包含34个ADM1要素，几何类型为Polygon或MultiPolygon，项目启动时会校验名称唯一性和经纬度范围。
数据来自geoBoundaries `gbOpen`，按CC BY 4.0使用，可上传GitHub，但必须保留归属声明。

## 公开仓库检查

- 未发现API Key、密码、私钥或个人身份信息。
- 新疆V1数据为公开统计指标，不包含个人级银行客户数据。
- `.streamlit/secrets.toml`、`.env*`、私钥、原始Excel和ChatGPT项目同步目录均已加入 `.gitignore`。
- Mock Data与V1数据由独立文件和页面模式加载；V1缺失值不会使用Mock Data填充。

## 当前限制

- V1只接入新疆，其他省份显示“暂无数据”。
- 住户存贷款两项保留Excel原始值，但明确标为待核验和口径不一致，不得用于正式分析。
- 人均GDP年份仍待统一。
- 当前目录不是Git仓库；创建GitHub仓库、提交和推送需在用户确认后执行。
