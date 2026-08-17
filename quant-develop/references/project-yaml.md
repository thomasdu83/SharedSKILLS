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
| `frontend` | 是否接入统一前端与接入位置；研究回测阶段默认不启用 |

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
- `research`：必须有可重复研究过程；历史回测默认只需要静态 HTML / Markdown 评审文档
- `candidate`：必须有固化输入输出与验证；可以有静态模型卡或定型评审页
- `production`：必须有可消费产品输出，例如建议权重、组合配置、评分或信号；可以同时提供 `publish` 和 `monitor`
- `monitor_only`：只输出状态、变化、告警或复核线索，不生成投资权重或配置建议；通常需要监控快照和跟踪索引
- `retired`：必须停止日常运行并保留归档说明

`project.yaml.stage` 只描述项目整体阶段。项目内部的模型版本、场景和求解器可以分别处于 Research、Candidate、Challenger、Champion 或 Rejected，不应通过修改项目阶段代替模型版本治理。

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
  publish: null
  monitor: null
```

规则：

- `research`：研究重跑或验证入口
- `publish`：产品快照或正式输出入口
- `monitor`：监控快照、告警或状态更新入口

如果某类入口不适用，可显式写 `null`，不要省略键名。
研究回测阶段通常只有 `research` 入口，`publish` 和 `monitor` 应显式写
`null`，不要为了模板完整而伪造生产发布或日常监控链路。
进入 `production` 或 `monitor_only` 后，再把对应入口改为实际脚本路径。

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

推荐按阶段增加落盘位置说明。

研究回测阶段：

```yaml
storage:
  research_runs: artifacts/research_runs
  research_reports: artifacts/research_runs/<run_id>/reports
```

定型发布或监控阶段：

```yaml
storage:
  production_snapshot_dataset: shared_data/parquet/fund/production_signal_bond_preference
  monitor_snapshot_dataset: shared_data/parquet/monitoring/monitor_snapshot_bond_preference
```

不要把绝对路径直接写死在 `project.yaml` 中。

## 9. `frontend` 规范

研究回测阶段默认不接统一前端：

```yaml
frontend:
  enabled: false
  preview_artifacts: artifacts/design_preview
  research_report_pattern: artifacts/research_runs/<run_id>/reports/backtest_review.html
```

定型后需要只读跟踪或监控时，建议写：

```yaml
frontend:
  enabled: true
  workspace: monitoring
  mode: read_only_monitor
  sections:
    - product
    - monitor
  detail_route: /projects/bond-preference-factor
```

说明：

- `workspace`：统一前端工作区
- `mode`：`read_only_monitor` 表示只读查看、筛选、刷新和下钻；只有明确存在维护或审批流程时才使用可编辑工作台
- `sections`：该项目出现在哪些工作台分区
- `detail_route`：项目详情页路径
- `preview_artifacts`：静态设计预览位置，不等同于统一前端接入
- `research_report_pattern`：研究回测阶段的静态 HTML 文档位置

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

## 11. 阶段化示例

### 11.1 研究回测阶段

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
  publish: null
  monitor: null
promotion_criteria:
  - 样本外有效
  - 成本后收益可接受
  - 可重复运行
risk_notes:
  - 季报披露滞后可能影响口径
storage:
  research_runs: artifacts/research_runs
  research_reports: artifacts/research_runs/<run_id>/reports
frontend:
  enabled: false
  preview_artifacts: artifacts/design_preview
  research_report_pattern: artifacts/research_runs/<run_id>/reports/backtest_review.html
```

### 11.2 候选定型阶段

```yaml
project_id: bond-preference-factor
name: 债券基金偏好因子
domain: fund.fixed_income
owner: thomas
stage: candidate
status: active
decision_frequency: monthly
input_contract: fund-factor-input-v1
output_contract: candidate-factor-output-v1
runtime_entrypoints:
  research: src/run_research.py
  publish: null
  monitor: null
promotion_criteria:
  - 候选模型配置已冻结
  - 样本外和稳健性检查已通过
  - 已形成定型评审 HTML
storage:
  research_runs: artifacts/research_runs
  candidate_review_report: artifacts/reports/model_candidate_review.html
frontend:
  enabled: false
  preview_artifacts: artifacts/design_preview
```

### 11.3 指标/状态跟踪阶段

```yaml
project_id: bond-preference-monitor
name: 债券基金偏好指标监控
domain: fund.fixed_income
owner: thomas
stage: monitor_only
status: active
description: 仅输出状态变化、风险提示和复核线索，不生成投资权重或配置建议
decision_frequency: monthly
input_contract: fund-factor-input-v1
output_contract: monitor-output-v1
runtime_entrypoints:
  research: src/run_research.py
  publish: null
  monitor: src/run_monitor.py
consumers:
  - unified-dashboard
  - monthly-workflow
storage:
  monitor_snapshot_dataset: shared_data/parquet/monitoring/monitor_snapshot_bond_preference
frontend:
  enabled: true
  workspace: monitoring
  mode: read_only_monitor
  sections:
    - monitor
  detail_route: /projects/bond-preference-monitor
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
