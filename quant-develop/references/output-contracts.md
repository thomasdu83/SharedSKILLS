# QuantSystem 输出契约规范

本规范定义研究项目、产品项目、监控项目对外输出的最小字段、语义边界、版本兼容规则和统一前端接入要求。

## 1. 设计原则

- 输出契约面向消费方，不面向项目内部实现
- 统一前端、工作流、注册表只消费标准化输出，不直接读取项目内部业务逻辑
- 项目内部可有自定义字段，但对外必须经适配层映射到统一 schema
- 原始快照尽量保留历史，索引层可做幂等更新

## 2. 输出类型

QuantSystem 当前统一三类输出：

- **因子输出**
- **产品输出**
- **监控输出**

## 3. 因子输出契约

### 3.1 最小字段

```yaml
project_id:
tradingday:
asset_code:
factor_name:
factor_value:
factor_version:
snapshot_time:
```

### 3.2 字段语义

| 字段 | 含义 |
|---|---|
| `project_id` | 输出来源项目 |
| `tradingday` | 因子归属交易日或评估日 |
| `asset_code` | 统一资产标识 |
| `factor_name` | 因子名称 |
| `factor_value` | 因子数值 |
| `factor_version` | 因子口径版本 |
| `snapshot_time` | 快照生成时间 |

### 3.3 可选字段

```yaml
asset_type:
universe_name:
as_of_date:
quality_flag:
```

## 4. 产品输出契约

### 4.1 最小字段

```yaml
project_id:
snapshot_time:
tradingday:
asset_code:
signal_score:
recommendation:
confidence:
summary:
detail_path:
```

### 4.2 字段语义

| 字段 | 含义 |
|---|---|
| `project_id` | 项目唯一标识 |
| `snapshot_time` | 输出快照生成时间 |
| `tradingday` | 决策日或信号归属日 |
| `asset_code` | 统一资产标识 |
| `signal_score` | 数值化信号强度 |
| `recommendation` | 推荐动作，如买入、增配、观察 |
| `confidence` | 输出置信度 |
| `summary` | 对当前输出的简短解释 |
| `detail_path` | 统一前端详情页或详情资源路径 |

### 4.3 可选字段

```yaml
rank:
portfolio_impact:
benchmark:
strategy_bucket:
risk_flag:
```

## 5. 监控输出契约

### 5.1 最小字段

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
detail_path:
```

### 5.2 字段语义

| 字段 | 含义 |
|---|---|
| `project_id` | 项目唯一标识 |
| `snapshot_time` | 记录生成时间 |
| `snapshot_date` | 监控快照所属日期 |
| `status` | 当前状态，如 normal / watch / alert |
| `alert_level` | 告警级别，如 low / medium / high |
| `status_change` | 与上期相比的变化摘要 |
| `trigger_reason` | 触发本次状态的主要原因 |
| `attention_required` | 是否需要人工关注 |
| `summary` | 监控摘要 |
| `detail_path` | 详情页路径 |

### 5.3 可选字段

```yaml
metric_name:
metric_value:
threshold:
previous_status:
```

## 6. 统一字段规则

### 6.1 时间字段

- `tradingday`：交易日、决策日、横截面评估日
- `snapshot_time`：生成时间戳
- `snapshot_date`：监控快照日期
- `as_of_date`：数据口径截止日

### 6.2 资产字段

- 外部统一字段使用 `asset_code`
- 项目内部可使用 `fundcode`、`secucode` 等
- 对外输出前必须映射成统一资产字段，或由适配层负责转换

### 6.3 文本字段

- `summary` 保持简短，可直接展示在前端卡片上
- `trigger_reason` 应聚焦单一主因，避免写成长报告
- `detail_path` 应指向稳定资源，不应指向临时文件名

## 7. 版本兼容规则

### 7.1 版本字段

推荐在输出中保留以下版本信息之一：

```yaml
contract_version:
```

或：

```yaml
factor_version:
signal_version:
monitor_version:
```

### 7.2 向后兼容原则

- 新增字段允许，但不得删除既有强依赖字段
- 字段语义改变必须伴随版本号提升
- 若字段类型发生破坏性变化，需同步升级适配层和消费方

## 8. 统一前端接入规则

- 统一前端只消费标准化输出或适配层结果
- 项目内部字段名不稳定时，必须由 `adapters` 层做转换
- 前端首页只展示最小字段，不直接依赖项目内部扩展字段
- 详情页可以读取更多扩展字段，但必须基于稳定 API 或标准化快照

## 9. 工作流消费规则

- `daily`、`weekly`、`backfill` 工作流应以标准输出为输入
- 工作流不得直接耦合项目内部 notebook、临时脚本、临时表结构
- 工作流读取快照后，可生成：
  - 最新索引表
  - 告警汇总表
  - 周报或日报中间层

## 10. 示例

### 10.1 产品输出示例

```yaml
project_id: bond-preference-factor
snapshot_time: 2026-04-08T20:30:00
tradingday: 2026-04-30
asset_code: 001234
signal_score: 0.83
recommendation: overweight
confidence: 0.76
summary: 因子分数显著高于同类债基均值
detail_path: /projects/bond-preference-factor
```

### 10.2 监控输出示例

```yaml
project_id: bond-preference-factor
snapshot_time: 2026-04-08T20:30:00
snapshot_date: 2026-04-08
status: watch
alert_level: medium
status_change: 过去三期分数分布明显收缩
trigger_reason: 因子横截面区分度下降
attention_required: true
summary: 因子有效性需人工复核
detail_path: /projects/bond-preference-factor
```

## 11. 反模式

- 前端直接依赖项目内部数据库表名
- 不同项目各自发明输出字段名
- 用 `date`、`xdate`、`score1` 这类语义不清字段对外输出
- 把扩展字段当最小字段，导致所有项目都负担过重
- 无版本字段却频繁改变字段语义

## 12. 快速检查清单

- 是否区分了因子输出、产品输出、监控输出
- 是否包含最小必填字段
- 是否使用统一时间字段
- 是否使用统一 `asset_code`
- 是否让前端通过标准化输出消费数据
- 是否保留版本字段或版本机制
- 是否避免破坏性字段变更
