# QuantSystem 运行编排规范

本规范定义 `workflows/` 目录下日频、周频、补数任务的组织方式、最小字段、调用边界、输入输出关系和失败处理原则。目标是让项目运行从“手工找脚本”升级为“可注册、可复跑、可索引”的统一编排。

## 1. 设计原则

- 工作流是编排层，不是业务实现层
- 工作流应调用项目标准入口，不应直接耦合项目内部函数
- 工作流优先消费标准化快照、标准化输出、标准化索引
- 日常运行与历史回补严格分离
- 工作流必须幂等或可恢复，避免重复运行污染结果

## 2. 目录职责

```text
workflows/
├─ daily/
├─ weekly/
└─ backfill/
```

### `daily/`

用于日频或准实时任务：

- 市场数据更新
- 日常监控快照
- 告警刷新
- 日报索引更新

### `weekly/`

用于周频或低频批处理任务：

- 周度评分
- 周度筛选
- 周报素材生成
- 周度产品快照汇总

### `backfill/`

用于历史回补与重算：

- 补历史数据
- 全样本重跑
- 口径切换后的回补
- 重建前端索引

## 3. 工作流与项目的边界

工作流只应依赖项目的 `runtime_entrypoints`。

示例：

```yaml
runtime_entrypoints:
  research: src/run_research.py
  publish: src/publish.py
  monitor: src/run_monitor.py
```

规则：

- `daily` 可调用 `publish` 或 `monitor`
- `weekly` 可调用 `publish`、`monitor`、特定周频入口
- `backfill` 可调用 `research`、`publish` 或专门的 backfill 入口

禁止：

- 在工作流里直接 import 项目内部函数
- 在工作流里写项目专属硬编码路径
- 在工作流里直接操作项目内部临时文件

## 4. 工作流定义最小字段

推荐每个工作流配置至少包含：

```yaml
workflow_id:
name:
schedule_type:
owner:
enabled:
target_projects:
steps:
outputs:
```

### 字段说明

| 字段 | 含义 |
|---|---|
| `workflow_id` | 工作流唯一标识 |
| `name` | 工作流名称 |
| `schedule_type` | `daily` / `weekly` / `backfill` |
| `owner` | 责任人 |
| `enabled` | 是否启用 |
| `target_projects` | 参与该工作流的项目 |
| `steps` | 编排步骤 |
| `outputs` | 工作流最终产物 |

## 5. `steps` 结构建议

```yaml
steps:
  - step_id: run-monitor
    action: project_entrypoint
    project_id: bond-preference-factor
    entrypoint: monitor
  - step_id: update-index
    action: refresh_index
    dataset: monitoring_index
  - step_id: publish-dashboard
    action: notify_dashboard
```

### 推荐 `action` 类型

- `project_entrypoint`
- `refresh_index`
- `publish_snapshot`
- `validate_contract`
- `notify_dashboard`
- `rebuild_cache`

## 6. 输出与落盘规则

工作流本身不创造新的业务 schema，而是组织已有标准输出的写入与索引。

### 常见输出

- 产品快照
- 监控快照
- 最新索引表
- 告警汇总表
- 周报或日报中间层

### 输出位置

- 业务快照：写入 `shared_data/parquet/...`
- 索引表：写入 `shared_data/sqlite/...`
- 项目内备份：写入 `artifacts/...`

## 7. daily 规范

适用场景：

- 监控项目每日状态更新
- 前端首页最新状态刷新
- 告警列表生成

规则：

- 输出应追加历史快照
- 最新状态索引允许覆盖
- 若输入数据不完整，应 fail fast 或显式降级并记录日志

## 8. weekly 规范

适用场景：

- 周度宏观评分
- 周度基金筛选
- 周度产品信号汇总

规则：

- 周频任务优先使用 `publish` 入口产出正式快照
- 周报类任务可消费前一环节的标准输出，不直接调用原始研究脚本

## 9. backfill 规范

适用场景：

- 回补历史监控快照
- 修改口径后重建历史结果
- 重建前端索引

规则：

- backfill 必须显式指定时间范围
- backfill 不得复用 daily 的默认调度逻辑
- backfill 应记录运行范围、版本、结果位置
- backfill 结束后若影响正式消费层，应刷新索引

## 10. 错误处理与幂等性

### 错误处理

- 数据缺失：报错或显式标记降级
- 契约校验失败：终止后续依赖步骤
- 快照写入失败：不更新索引

### 幂等性

- 同一 `tradingday` 或 `snapshot_date` 重跑应可重复覆盖索引
- 原始快照重复写入必须可检测，避免产生重复消费

## 11. 与统一前端的关系

工作流通常承担三类前端相关任务：

- 更新最新状态索引
- 生成前端所需汇总表
- 通知或触发 dashboard 刷新

统一前端不应等待项目内部脚本，而应等待工作流产出的标准索引或快照。

## 12. 示例

### 12.1 日频监控工作流示例

```yaml
workflow_id: daily-monitoring-refresh
name: 日频监控刷新
schedule_type: daily
owner: thomas
enabled: true
target_projects:
  - bond-preference-factor
steps:
  - step_id: run-monitor
    action: project_entrypoint
    project_id: bond-preference-factor
    entrypoint: monitor
  - step_id: validate-monitor-contract
    action: validate_contract
    contract: monitor-output-v1
  - step_id: refresh-monitor-index
    action: refresh_index
    dataset: monitoring_index
outputs:
  - shared_data/parquet/monitoring/monitor_snapshot_bond_preference
  - shared_data/sqlite/monitoring_index.db
```

### 12.2 周频产品工作流示例

```yaml
workflow_id: weekly-fund-publish
name: 周度基金产品输出
schedule_type: weekly
owner: thomas
enabled: true
target_projects:
  - bond-preference-factor
steps:
  - step_id: run-publish
    action: project_entrypoint
    project_id: bond-preference-factor
    entrypoint: publish
  - step_id: validate-product-contract
    action: validate_contract
    contract: product-output-v1
  - step_id: refresh-product-index
    action: refresh_index
    dataset: product_snapshot_index
outputs:
  - shared_data/parquet/fund/production_signal_bond_preference
```

## 13. 反模式

- 把工作流写成另一个业务脚本目录
- daily、weekly、backfill 共用一个混乱入口
- 工作流直接读取 notebook 输出文件
- 工作流跳过契约校验
- 索引已更新但原始快照写入失败
- 用工作流替代项目本身的业务实现

## 14. 快速检查清单

- 是否区分了 `daily`、`weekly`、`backfill`
- 是否通过 `runtime_entrypoints` 调用项目
- 是否避免直接耦合项目内部实现
- 是否定义了清晰 `steps`
- 是否明确输出位置
- 是否先写快照再更新索引
- 是否考虑错误处理与幂等性
