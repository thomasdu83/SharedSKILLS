# QuantSystem 项目元数据规范

本规范定义 `project.yaml` 的最小字段、推荐字段、字段语义与阶段化维护规则。目标是让每个项目都能被注册、运行、展示、复核和退役，而不是仅仅存在于目录中。

## 1. 设计原则

- `project.yaml` 是项目控制面，不是说明性附件
- 每个项目必须且只能有一个主 `project.yaml`
- 生命周期状态靠 `project.yaml.stage` 管理，不靠目录迁移
- 工作流、统一前端、注册表都应优先读取 `project.yaml`

## 2. 最小字段

以下字段为所有项目必填：

```yaml
project_id:
name:
domain:
owner:
stage:
status:
decision_frequency:
runtime_entrypoints:
```

### 字段说明

| 字段 | 含义 | 示例 |
|---|---|---|
| `project_id` | 项目唯一标识，英文蛇形或连字符命名 | `bond-preference-factor` |
| `name` | 项目中文名称 | `债券基金偏好因子` |
| `domain` | 所属研究域 | `fund.fixed_income` |
| `owner` | 责任人 | `thomas` |
| `stage` | 生命周期阶段 | `research` |
| `status` | 当前运行状态 | `active` |
| `decision_frequency` | 决策或更新频率 | `monthly` |
| `runtime_entrypoints` | 标准入口 | `research / publish / monitor` |

## 3. 推荐字段

```yaml
description:
tags:
created_at:
last_review_date:
data_dependencies:
input_contract:
output_contract:
promotion_criteria:
consumers:
risk_notes:
storage:
frontend:
```

### 推荐字段语义

| 字段 | 含义 |
|---|---|
| `description` | 一句话说明项目解决什么问题 |
| `tags` | 项目标记，如 `factor`、`monitor`、`macro` |
| `created_at` | 项目创建日期 |
| `last_review_date` | 最近一次复核日期 |
| `data_dependencies` | 依赖的数据集或上游表 |
| `input_contract` | 输入契约名称或版本 |
| `output_contract` | 输出契约名称或版本 |
| `promotion_criteria` | 晋级标准 |
| `consumers` | 谁消费该项目输出，如前端、组合、工作流 |
| `risk_notes` | 风险边界和失效条件 |
| `storage` | 正式结果写入位置 |
| `frontend` | 是否接入统一前端与接入位置 |

## 4. `stage` 取值规范

仅允许以下取值：

- `idea`
- `research`
- `candidate`
- `production`
- `monitor_only`
- `retired`

### 语义约束

- `idea`：允许只有笔记和原型
- `research`：必须有可重复研究过程
- `candidate`：必须有固化输入输出与验证
- `production`：必须有可消费产品输出
- `monitor_only`：必须有统一监控输出
- `retired`：必须停止日常运行并保留归档说明

## 5. `status` 取值规范

推荐使用：

- `active`
- `paused`
- `deprecated`
- `retired`

说明：

- `stage` 表示生命周期阶段
- `status` 表示当前运行状态
- 两者不可混用

示例：

- `stage: production` + `status: active`
- `stage: production` + `status: paused`
- `stage: retired` + `status: retired`

## 6. `runtime_entrypoints` 规范

推荐至少定义以下键：

```yaml
runtime_entrypoints:
  research: src/run_research.py
  publish: src/publish.py
  monitor: src/run_monitor.py
```

规则：

- `research`：研究重跑或验证入口
- `publish`：产品快照或正式输出入口
- `monitor`：监控快照、告警或状态更新入口

如果某类入口不适用，可显式写 `null`，不要省略键名。

## 7. `data_dependencies` 规范

建议写上游数据集名称，而不是临时文件名：

正确示例：

```yaml
data_dependencies:
  - fund_quote
  - fund_asset
  - macro_liquidity_state
```

错误示例：

```yaml
data_dependencies:
  - tmp_data.xlsx
  - 最终结果表2.xlsx
```

## 8. `storage` 规范

推荐增加正式落盘位置说明：

```yaml
storage:
  research_runs: artifacts/research_runs
  production_snapshot_dataset: shared_data/parquet/fund/production_signal_bond_preference
  monitor_snapshot_dataset: shared_data/parquet/monitoring/monitor_snapshot_bond_preference
```

不要把绝对路径直接写死在 `project.yaml` 中。

## 9. `frontend` 规范

如果项目需要接统一前端，建议写：

```yaml
frontend:
  enabled: true
  workspace: monitoring
  sections:
    - product
    - monitor
  detail_route: /projects/bond-preference-factor
```

说明：

- `workspace`：统一前端工作区
- `sections`：该项目出现在哪些工作台分区
- `detail_route`：项目详情页路径

## 10. `promotion_criteria` 规范

不要写空泛描述，尽量写可验证条件。

推荐：

```yaml
promotion_criteria:
  - 样本外有效
  - 成本后收益可接受
  - 输入数据稳定可复现
  - 已接入统一输出契约
```

不推荐：

```yaml
promotion_criteria:
  - 效果不错
  - 感觉能用
```

## 11. 完整示例

```yaml
project_id: bond-preference-factor
name: 债券基金偏好因子
domain: fund.fixed_income
owner: thomas
stage: research
status: active
description: 用于债券基金优选的月频截面因子
tags:
  - factor
  - fund
  - fixed-income
created_at: 2026-04-08
last_review_date: 2026-04-08
decision_frequency: monthly
data_dependencies:
  - fund_quote
  - fund_asset
  - fund_type
input_contract: fund-factor-input-v1
output_contract: factor-output-v1
runtime_entrypoints:
  research: src/run_research.py
  publish: src/publish.py
  monitor: src/run_monitor.py
promotion_criteria:
  - 样本外有效
  - 成本后收益可接受
  - 可重复运行
consumers:
  - unified-dashboard
  - weekly-workflow
risk_notes:
  - 季报披露滞后可能影响口径
storage:
  research_runs: artifacts/research_runs
  production_snapshot_dataset: shared_data/parquet/fund/production_signal_bond_preference
frontend:
  enabled: true
  workspace: monitoring
  sections:
    - monitor
```

## 12. 反模式

- 用目录名而不是 `project.yaml.stage` 表示生命周期
- 缺少 `owner`，导致项目无人负责
- 缺少 `runtime_entrypoints`，导致工作流无法接入
- 把临时文件名写进 `data_dependencies`
- 在 `project.yaml` 中写绝对路径
- `stage` 和 `status` 混用

## 13. 快速检查清单

- 是否有唯一 `project_id`
- 是否有明确 `stage` 和 `status`
- 是否有责任人 `owner`
- 是否有标准入口 `runtime_entrypoints`
- 是否写明上游依赖 `data_dependencies`
- 是否写明晋级标准 `promotion_criteria`
- 是否避免了绝对路径和临时文件名
