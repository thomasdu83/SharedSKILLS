# QuantSystem 本地数据保存与命名规范

本规范定义 QuantSystem 在本地文件系统中的标准存储格式、目录层级、命名方式与最小字段约束。目标是让研究项目、产品项目、监控项目都能被统一工作流和统一前端稳定消费。

## 1. 介质选择

| 介质 | 默认用途 | 允许场景 | 禁止场景 |
|---|---|---|---|
| Parquet | 大批量时序、因子、快照、监控历史 | 研究结果、产品信号、监控快照、宽表和长表数据 | 人工手改主数据 |
| SQLite | 小型结构化状态与索引 | 项目台账、实验记录、晋级记录、前端索引、小型状态表 | 大规模行情、全历史因子主存储 |
| Excel | 人工输入与交付导出 | 人工维护白名单、一次性交付表、汇报附件 | 生产链路中的唯一数据源、核心中间层 |

## 2. 存储边界

- **项目内 `artifacts/`**：存放单项目研究产物、局部图表、临时快照、项目专属结果
- **平台级 `shared_data/`**：存放需要被跨项目、统一工作流、统一前端消费的正式数据集
- 研究阶段可先写入项目内 `artifacts/research_runs/`
- 一旦进入 `candidate`、`production`、`monitor_only`，正式消费数据应迁移到平台级标准目录

## 3. 平台级目录规范

```text
shared_data/
├─ parquet/
│  ├─ fund/
│  ├─ macro/
│  ├─ cta/
│  └─ monitoring/
├─ sqlite/
│  ├─ registry.db
│  ├─ monitoring_index.db
│  └─ project_state.db
├─ excel/
└─ artifacts/
```

## 4. Parquet 目录规范

### 4.1 目录结构

推荐采用“数据集 + 分区目录”模式：

```text
shared_data/parquet/<domain>/<dataset_name>/
└─ tradingday=YYYY-MM-DD/
   └─ data.parquet
```

监控快照推荐：

```text
shared_data/parquet/monitoring/<dataset_name>/
└─ snapshot_date=YYYY-MM-DD/
   └─ data.parquet
```

### 4.2 数据集命名

- 因子数据：`factor_<project_id>`
- 产品信号：`production_signal_<project_id>`
- 监控快照：`monitor_snapshot_<project_id>`
- 中间特征：`feature_<project_id>`

示例：

```text
shared_data/parquet/fund/factor_bond_preference/
shared_data/parquet/fund/production_signal_bond_preference/
shared_data/parquet/monitoring/monitor_snapshot_bond_preference/
```

### 4.3 分区字段

默认规则：

- 研究结果、因子、信号：`tradingday`
- 监控快照：`snapshot_date`
- 极少数需要口径截止日时可使用：`as_of_date`

禁止同类数据集中同时混用：

- `date`
- `xdate`
- `dt`
- `日期`

### 4.4 文件命名

- 分区目录内统一使用 `data.parquet`
- 不建议在分区目录内自定义复杂文件名
- 如果必须单文件存储，不分区时使用：
  - `<dataset_name>__<YYYY-MM-DD>.parquet`

示例：

```text
factor_bond_preference__2026-04-30.parquet
```

## 5. SQLite 规范

### 5.1 数据库命名

- `registry.db`：项目台账、实验记录、晋级记录
- `monitoring_index.db`：统一前端索引、最新状态与告警索引
- `project_state.db`：小型项目状态库

### 5.2 表命名

- `projects`
- `experiments`
- `promotion_log`
- `monitor_snapshot_index`
- `product_snapshot_index`

表名使用蛇形命名，禁止中文表名、临时后缀、版本号堆叠。

### 5.3 索引字段

最少考虑以下索引：

- `project_id`
- `tradingday`
- `snapshot_time`
- `stage`
- `status`

## 6. 时间字段规范

统一字段语义：

| 字段 | 含义 |
|---|---|
| `tradingday` | 交易日、决策日、横截面评估日 |
| `snapshot_time` | 系统生成该条记录的时间戳 |
| `snapshot_date` | 监控快照所属日期 |
| `as_of_date` | 数据口径截止日 |

禁止不同项目自造含义不清的字段名：

- `date`
- `time1`
- `update_time2`
- `日期`

## 7. 最小字段规范

### 7.1 因子表

```yaml
tradingday:
asset_code:
factor_name:
factor_value:
factor_version:
snapshot_time:
```

如果是基金项目，可将 `asset_code` 具体化为 `fundcode`，但对外适配层需能映射回统一资产字段。

### 7.2 产品信号表

```yaml
project_id:
tradingday:
asset_code:
signal_score:
recommendation:
confidence:
summary:
snapshot_time:
```

### 7.3 监控快照表

```yaml
project_id:
snapshot_time:
snapshot_date:
status:
alert_level:
status_change:
trigger_reason:
attention_required:
summary:
```

## 8. 追加式与覆盖式规则

- **研究结果**：允许追加式保存，按 `tradingday` 或试验批次沉淀
- **产品快照**：推荐追加式保存，保留历史可追溯性
- **监控快照**：推荐追加式保存，并由统一前端索引层提取最新一条
- **索引表**：允许覆盖或幂等更新，例如最新状态表

原则：

- 原始快照尽量追加，保证可回溯
- 衍生索引可以覆盖，保证查询效率

## 9. 项目内 `artifacts/` 规范

```text
artifacts/
├─ research_runs/
├─ production_snapshots/
├─ monitor_snapshots/
├─ charts/
└─ reports/
```

说明：

- `research_runs/`：原型研究输出、临时试验结果
- `production_snapshots/`：产品化后的项目内备份快照
- `monitor_snapshots/`：监控化后的项目内备份快照
- `charts/`：图表资源
- `reports/`：项目内报告、复盘、HTML 导出

## 10. 命名反模式

禁止以下命名：

- `结果最终版.xlsx`
- `tmp_data_new2.parquet`
- `monitor_final_final.xlsx`
- `因子数据备份最新版.db`

推荐命名：

- `factor_bond_preference`
- `production_signal_bond_preference`
- `monitor_snapshot_bond_preference`
- `registry.db`

## 11. 前端消费规则

- 统一前端优先读取平台级标准快照或索引
- 统一前端不得直接依赖项目内部临时文件名
- 项目若输出自定义字段，必须经 `adapters` 转换为统一 schema 后再供前端使用

## 12. 快速检查清单

- 是否优先使用 Parquet 保存大批量数据
- 是否避免用 Excel 做核心中间层
- 是否使用统一时间字段
- 是否采用标准数据集命名
- 是否使用分区目录而不是散落文件
- 是否保留历史快照而不是只保留最新结果
- 是否让统一前端消费标准化输出而非项目内部文件
