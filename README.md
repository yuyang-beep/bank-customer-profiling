# 全国潜在银行客群画像地图 Prototype V0.2

一个使用 Python、Pandas、Streamlit、Plotly 和 GeoJSON 构建的可运行原型。页面支持明确分离的 **Mock Data** 模式和“新疆真实数据”模式。

## 已实现

- 中国省级 GeoJSON 交互式分级设色图，使用稳定的显式中国视口
- 悬停查看省份和当前指标
- 稳定的省份下拉选择器
- 基于 Streamlit 1.65 / Plotly 6.9 selection event 的地图点击选择
- 常住人口、人均可支配收入、人均存款三个演示指标
- 无数据区域灰色显示并标注“暂无数据”
- 省份画像卡片、当前指标与 Mock 样本中位数对比图
- 现代化白色/深蓝/蓝绿金融数据 Dashboard 界面
- GeoJSON 要素数、名称、几何类型和坐标范围自动校验
- 数据年份和 Mock 来源声明
- CSV/Excel 通用读取入口、数据结构校验和独立地图构建模块
- 2024 年作为新疆真实画像基准年，其他年份只作带年份补充展示
- 真实模式下未采集省份显示“暂无数据”，不使用 Mock 值填充
- 新疆画像分为人口结构、收入与财富、区域金融市场三个模块
- 区域金融市场的本外币各项存贷款不作为住户指标，也不生成住户派生比值
- 真实模式仅展示 Excel 新疆行中标黄且已核验的指标，并保留 active/pending/inactive 状态
- 页面采用固定上下布局：全国地图独占一行，省份指标卡片和来源位于地图下方
- 新疆V1核心指标由最新Excel中新疆行的黄色填充自动识别，Dashboard不手写指标名称或数值
- 待核验指标保留Excel原始值，并显示口径或年份风险提示

## 目录结构

```text
.
├── app.py
├── data_access/
│   ├── base.py
│   ├── csv_repository.py
│   ├── models.py
│   └── validation.py
├── data/
│   ├── china_adm1.geojson
│   ├── mock_province_profiles.csv
│   ├── real_province_metrics.csv
│   ├── indicator_definitions.csv
│   ├── metric_catalog.csv
│   ├── province_crosswalk.csv
│   └── README.md
├── utils/
│   ├── data_loader.py
│   ├── calculations.py
│   ├── map_builder.py
│   └── ui_components.py
├── tests/
│   ├── test_data.py
│   └── test_data_access.py
├── docs/
│   └── data_management.md
├── requirements.txt
└── README.md
```

## 启动

建议使用 Python 3.11–3.14 和虚拟环境。`requirements.txt` 已锁定 V0.2 验证过的依赖版本：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

打开终端返回的本地地址，通常是 <http://localhost:8501>。

## 接入真实数据

Dashboard 通过 `DataRepository` 读取数据，不直接依赖 CSV 文件名。完整设计见 [`docs/data_management.md`](docs/data_management.md)。

1. 从国家统计局、中国人民银行、省级统计年鉴等权威渠道收集数据，并记录指标定义、统计口径、年份和 URL。
2. 将真实值追加到 `real_province_metrics.csv`，每行保留省份、年份、指标、值、单位、统计口径、来源 URL 和核验状态。
3. 需要在地图中显示的基准年指标，在 `metric_catalog.csv` 增加 `data_mode=real` 配置。
4. 新省份名称需与 `province_crosswalk.csv` 一致；未收集数据保持缺失，不从 Mock 表回填。
5. 跨年记录只展示原年份。如需计算比值，先确认同年、同单位、同时点和同统计口径。
6. 修订数据时新增 `record_version`，使用 `supersedes_version` 指向旧版本，不直接删除历史记录。

### 同步新疆 V1 黄色指标

```bash
source .venv/bin/activate
python scripts/sync_v1_from_excel.py
```

该命令自动选择项目内 `imports/` 中最新的非临时 `.xlsx` 文件，按省份名称定位新疆，
识别黄色指标并生成 `data/v1_xinjiang_metrics.csv`。运行 `--check-only` 可只检查不写入。
核验状态和风险说明保存在 `data/v1_review_metadata.csv`，同步新数值不会自动将待核验指标改为已核验。
新增黄色指标、单位变化或指标字典缺项会中止同步并要求人工复核。
同步完成后刷新Dashboard即可读取新清单，不需要修改页面代码。

## Streamlit Community Cloud 部署准备

- 仓库入口文件填写 `app.py`。
- 在 Advanced settings 中选择 Python 3.12。
- 云端直接读取项目内 `data/v1_xinjiang_metrics.csv`，不依赖原始Excel或MacBook路径。
- 原始Excel放在本地 `imports/` 更新数据；该目录中的Excel已被Git忽略。
- GeoJSON来自geoBoundaries `gbOpen`，按CC BY 4.0上传并保留归属声明。
- 完整检查清单见 [`docs/deployment_checklist.md`](docs/deployment_checklist.md)。

## 数据与边界声明

边界使用 geoBoundaries `gbOpen` CHN ADM1 简化图层。完整来源、许可和版本记录见 [`data/README.md`](data/README.md)。边界数据仅供可视化原型使用，不代表法律认定。

GeoJSON 遵循经度在前、纬度在后的顺序。V0.2 启动时校验全部几何和坐标，并在 Plotly 中使用经度 `70–138`、纬度 `16–56` 的显式可视窗口。这一设置只稳定显示范围，不修改原始行政区几何。

## 验证

```bash
python -m py_compile app.py utils/*.py tests/test_data.py
python -m unittest discover -s tests -v
```

V0.2 测试覆盖 34 个边界要素、31 条 Mock 画像、新疆真实数据长表、2024 年地图透视和跨年计算拦截。

## 当前限制

- 真实数据当前仅展示新疆的常住人口、居民人均可支配收入和居民人均消费支出；消费支出明确标注为2023年。
- 金融机构存贷款总量因与 Excel 的住户口径冲突暂不显示；人均GDP因年份元数据冲突保持 pending。
- 住户存贷款存量、农村居民收入、数字普惠金融指数原始链接等仍待核验。
- Plotly 省份点击使用 Streamlit 原生 `on_select="rerun"` selection event，不引入第三方组件；下拉选择器仍是跨浏览器的稳定备选方式。
- 暂无历史年份、城市级下钻、用户登录、数据库或模型评分。
