# 代码审查 (Code Review)

当用户提及 "review", "审查", "检查代码" 时，自动进入审查模式。

## 1. 审查模式

- **快速审查 (Quick Scan)**: 5分钟内，检查 `print`, 类型注解, 硬编码路径。
- **深度审查 (Deep Review)**: 模块级检查，覆盖架构、设计模式、数据层规范。

## 2. 检查清单 (Checklist)

### 2.1 Critical (必须修复)
- [ ] **Hardcoding**: 是否存在硬编码路径或配置？
- [ ] **Dependency Injection**: 核心类是否通过构造函数注入依赖？
- [ ] **Fail Fast**: 是否在入口处校验参数？
- [ ] **Silent Failure**: 是否存在空的 `except:` 块？
- [ ] **Logging**: 是否使用 `print()` 而非 `logger`？
- [ ] **Data Format**: 大批量数据是否使用 Parquet 而非 CSV/Excel/SQLite？

### 2.2 Warning (强烈建议)
- [ ] **Type Hints**: 公开方法是否有类型注解？
- [ ] **Docstrings**: 是否包含 `Args/Returns/Raises`？
- [ ] **Complexity**: 单文件是否超过 1000 行？
- [ ] **Performance Instrumentation**: 性能优化前是否已有 `module/label_type -> stage` 级耗时证据？

### 2.3 Quant Critical (量化核心逻辑)
- [ ] **Point-in-Time**: join、rolling、resample、label、signal 是否引入未来信息？
- [ ] **Date Semantics**: `tradingday`、`as_of_date`、`snapshot_time` 和交易日历是否明确？
- [ ] **Coverage Preflight**: 是否检查日期覆盖、字段覆盖、缓存新鲜度和上游依赖，而不只是文件存在？
- [ ] **Dependency Graph**: CLI 或入口是否声明真实前置步骤？名称为“独立入口”时是否真的独立？
- [ ] **Duplicate Keys**: `pivot`、聚合或 as-of join 前是否检查重复键？
- [ ] **Fail Fast**: 核心标签、信号、风控、PnL 缺数据时是否中断，而不是静默补值？
- [ ] **Fallback Gate**: 兜底只在严格规则结果为空时触发，且不会覆盖严格结果？
- [ ] **Fallback Scope**: 严格为空的判断粒度是否明确，是全模块、单标签、单日期还是单实体组？
- [ ] **Audit Separation**: 主结果和审计证据是否分层保存，并能通过 `run_id` 关联？
- [ ] **Rule Tests**: 是否同时覆盖正确性、边界和“约束不能被放宽”的测试？

### 2.4 Performance Review (性能优化)
- [ ] **Measured Bottleneck**: 优化目标是否来自日志，而不是感觉？
- [ ] **Instrumentation Gate**: 没有 stage 耗时证据时，是否避免并行改造或大面积 `groupby.apply` 改写？
- [ ] **Duplicate Work**: 同一运行日是否重复读取宽表、universe、持仓、风格快照或分类快照？
- [ ] **Cache Invalidation**: 进程内缓存是否有清理/失效策略，并与上游写入或配置变更联动？
- [ ] **Structural Blowup**: 是否构造了 `asset x category x date` 这类不必要全量网格？
- [ ] **Vectorization**: 可用 `agg`、`transform`、`sum`、`cumprod` 的计算是否仍使用 `groupby.apply(lambda ...)`？
- [ ] **Wrong Target**: 写库耗时接近 0 时，是否仍在过度优化 SQLite/Parquet 写出？
- [ ] **Stop Rule**: 是否定义并遵守本轮优化终止条件？
- [ ] **Contract Safety**: 提速是否保持标签定义、时点口径、默认数据源和输出契约不变？

## 3. 需要提供的验证证据

量化代码审查不能只看静态代码。根据风险，至少提供：

- 实际运行命令、退出码和目标输入日期范围；
- 输入/输出行数、实体数、最小/最大日期和缺失统计；
- 关键筛选或标签模块的审计漏斗；
- 结果为 0、覆盖不足、重复键和 fallback 触发时的行为；
- 针对 `merge_asof`、rolling、阈值和 fallback 的测试结果。
- 性能优化前后的 stage 耗时对比，以及本轮是否达到终止条件。
- 性能优化后的受影响模块测试、输出行数/分布对比和关键标签/信号一致性证据。

## 4. 输出格式

```markdown
# 代码审查报告

**审查对象**: `[文件/模块]`
**审查模式**: [快速/深度]

---

## ⛔ Critical
1. **[位置]**: 问题描述
   - *修复建议*: ...

## ⚠️ Warning
1. **[位置]**: 问题描述

## ✅ 合规项
- ...

## 📋 改进计划
1. 立即修复: ...
2. 后续优化: ...
```
