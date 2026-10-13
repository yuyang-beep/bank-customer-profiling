# 数据管理架构

## 目标

Dashboard 只依赖 `DataRepository` 接口，不依赖 CSV 文件名或 Pandas 读取细节。当前 `CsvDataRepository` 是唯一存储适配器。迁移 SQLite 或 PostgreSQL 时，实现同一接口即可保留页面、地图和查询调用。

```text
Streamlit Dashboard
        |
        v
DataRepository + MetricQuery
        |
        +-- CsvDataRepository       当前
        +-- SQLiteDataRepository    未来
        +-- PostgresDataRepository  未来
```

## 业务标识与版本

一条统计观测的业务键为：

```text
province_code + year + metric_key + statistical_scope
```

`record_version` 加入物理唯一键。同一业务键只能有一个 `version_status=current` 版本。修订数据时新增更高版本，通过 `supersedes_version` 指向旧版本，旧记录保留并标记为 `superseded`。

CSV 阶段不直接原地修改历史值。`stage_import()` 只在内存中生成待复核结果，不写文件。

## 长表字段

- 业务键：`province_code`、`year`、`metric_key`、`statistical_scope`
- 值与定义：`value`、`unit`、`metric_name`、`module`
- 时间与来源：`statistical_period`、`source_name`、`source_url`
- 质量：`verification_status`、`verification_note`、`is_derived`
- 展示控制：`display_status`（active/pending/inactive）、`yellow_marked`、`source_cell`
- 版本：`record_version`、`version_status`、`ingested_at`、`supersedes_version`

`indicator_definitions.csv` 是指标字典，控制每个 `metric_key` 的标准单位和模块归属。
Dashboard 只有在记录为 `active`、来源单元格标黄且核验通过时才显示数值；
`pending` 和 `inactive` 指标仍保留在字典中，但页面显示“暂无数据”。

核心指标通过 `is_core_indicator=true` 和 `display_order` 显式定义。当前核心区固定为
住户贷款余额、常住人口、居民人均可支配收入、住户存款余额、居民人均消费支出、
人均地区生产总值（人均GDP）六项。金融机构本外币各项存贷款余额属于独立的
“区域金融市场”，不得替代住户口径指标。

## 导入和查询

- `get_metric_records(MetricQuery(...))`：按省份代码、年份、指标、口径、核验状态查询。
- `validate_import(frame)`：校验字段、必填值、重复键、单位、核验状态和当前版本唯一性。
- `stage_import(frame)`：校验新版本并生成包含历史版本的待复核数据集。

## 迁移数据库

SQLite/PostgreSQL 可以使用三张主表：`metric_observations`、`indicator_definitions`和 `provinces`。对观测表建立唯一约束：

```text
(province_code, year, metric_key, statistical_scope, record_version)
```

再用部分唯一索引或事务规则保证每个业务键只有一个 `current` 版本。页面不需要因此修改。
