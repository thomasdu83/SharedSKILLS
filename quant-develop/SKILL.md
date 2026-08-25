---
name: quant-develop
description: Use when building or standardizing recurring QuantSystem projects, data contracts, portfolio construction, backtests, labels, signals, monitoring modules, or performance bottleneck work that requires explicit dependencies, point-in-time correctness, coverage preflight, audit artifacts, or downstream consumption. Prefer quant-research-coding for one-off exploration.
---

# QuantDevelop 开发规范

面向可重复使用的 QuantSystem 项目，提供清晰、统一、可维护的工程标准。工程强度应由输出用途和风险决定，不因进入正式项目就默认建设 Registry、统一 API、复杂工作流或可编辑前端。

## 适用边界

只有当代码需要长期复用、多人协作、定期运行、进入 `registry/` /
`workflows/`、生成可被投资流程消费的输出，或需要从研究原型晋级为正式
QuantSystem 项目时，才使用本技能。

不要把本技能套到所有量化研究代码上。一次性数据检查、临时取数、探索性
回测、图表生成、报告素材处理、用于判断想法是否值得继续的轻量原型，优先
使用 `quant-research-coding`。这些任务只需要清晰脚本、最小可复跑入口和
有证据的结果校验，不需要默认建立 `project.yaml`、`registry/`、`workflows/`
或完整项目目录。

升级到本技能的信号：
- 脚本会被反复运行，且结果会进入研究或投资管理流程。
- 输出会被他人消费、复核、归档或用于客户/投委会材料。
- 需要固定数据契约、运行频率、日志、配置、权限或失败告警。
- 轻量原型已经证明有价值，用户明确要求项目化或平台化。

### 项目类型与生命周期边界

- `project.yaml.stage` 表示项目整体阶段，不表示项目内每个模型版本的阶段。
- 一个模型项目可以同时保留 Research、Candidate、Challenger、Champion 和 Rejected 版本；版本角色与项目阶段应在运行 manifest 或独立决议记录中区分。
- 输出建议权重、组合配置或可直接进入投资流程的结果，使用 `production`；同一项目可以同时提供 `publish` 和 `monitor` 入口。
- 只输出状态、变化、告警或复核线索且不产生权重/配置建议的项目，使用 `monitor_only`。
- 非模型指标按投资问题或使用场景归组为轻量监控项目，不为每个指标复制完整模型治理链路。

### 晋级与证据保留

从研究脚本晋级正式项目时，至少带走假设、入口、参数、PIT/data scope、验证证据、失败条件和晋级理由。探索期临时脚本无需永久登记；正式比较批次中的失败模型必须保留结果和排除原因。

### 回测与跟踪前端门禁

不要把“历史回测需要可读产物”和“定型模型需要运行工作台”混为一类。

- `research` 阶段的历史回测默认不接统一前端，也不建设前后端交互系统。优先交付可复现入口、运行 manifest、审计证据，以及静态 HTML 回测评审文档。
- `candidate` 阶段可以生成静态模型卡、定型评审页或候选模型 HTML 文档，用于确认模型假设、样本外表现、失败条件和晋级标准；除非用户明确要求，不默认接入日常操作台。
- `production` 模型定型后可以建设跟踪工作台；发布门禁和人工确认只有在该工作台实际承载这些流程时才加入。
- `monitor_only` 默认建设只读监控视图，覆盖数据新鲜度、运行状态、变化、告警和证据下钻，不默认加入写操作。
- 前端 preview 不是生产前端。研究期 preview 应放在 `artifacts/design_preview/` 或 `artifacts/research_runs/<run_id>/reports/`，并明确标注其静态评审用途。

### 前后端数据生命周期门禁

当项目需要通过前端触发更新/计算、查询缓存状态或删除旧数据时，必须把读取、计算、删除视为同一条数据生命周期：

- 前端只提交强类型、allowlist 约束的参数并消费标准 API；业务计算仍由 CLI/领域服务唯一实现，禁止在页面或 Web 路由中复制金融逻辑、拼接 SQL 或直接删文件。
- 长计算使用独立 job store、单写入任务和 `queued/running/success/partial_success/failed` 状态；记录 `run_id`、参数、退出码、增量日志和每个日期的失败原因。任务提交与全量清理争抢同一写锁。
- 更新前做依赖、日期覆盖、字段/唯一键、缓存新鲜度和版本 preflight；所有结果层完成且覆盖检查通过后才能标记成功，部分结果不得伪装为 ready。
- 删除必须拆成只读 preview 与 execute；preview 返回表/日期/行数/文件影响，范围变化后失效，execute 由后端再次校验并要求 `DELETE` / `DELETE ALL` 强确认。
- 全量清理先冻结并校验 regular file/directory、sidecar 和根目录边界，先删可重建产物、后删数据库；活动计算时返回冲突，失败立即停止并保留审计资产。成功后清理进程内缓存，重启和重复执行都要进入可解释的空状态。
- 前端必须显式处理 loading、empty、error、queued、running、partial 和 failed；同一作用域的新请求要取消或淘汰旧响应，计算/删除成功后重新读取元数据和新鲜度。

完整的请求/响应、任务、缓存、删除和验证矩阵见 [data-lifecycle.md](references/data-lifecycle.md)。

## 1. 核心原则 (Core Principles)

- **Fail Fast**: 参数校验在函数入口立即执行，禁止静默失败。
- **Explicit**: 显式依赖注入，显式类型注解，显式参数传递。
- **Config-Driven**: 业务参数（如权重、路径、阈值）必须在 YAML 配置中，禁止硬编码。
- **No Print**: 严禁使用 `print()`，必须使用 `logging`。
- **Single Project Home**: 一个项目一个主目录，项目整体生命周期只由 `project.yaml.stage` 管理，不靠搬目录。
- **Outputs First**: 先定义主输出物、消费方和运行频率，再决定目录、入口和工作流。
- **Point-in-Time First**: 先证明每个输入在目标 `tradingday` / `as_of_date` 可见，再讨论计算结果。
- **Evidence Chain**: 主结果、运行参数、依赖覆盖、审计明细和验证证据必须能够关联到同一个 `run_id`。

## 2. 工作流 (Workflow)

### 2.1 任务三部曲
1. **分析 (Analysis)**:
   - 优先使用 MCP 查询数据/代码。
   - 明确当前任务是“新项目建设”“旧项目标准化”还是“已有项目功能开发”。
   - 明确数据源 (DB/Parquet/SQLite/Excel)。
     - **DBSource (默认主链路)**: 适用于最新数据、研究主链路和生产主链路。
     - **ParquetSource**: 适用于本地快照、批量历史读取和稳定回放。
     - **SQLite**: 仅限于极少量元数据、配置或轻量级关系型数据。
     - **Excel**: 仅限于手工输入或展示。
   - 明确每个时间字段的语义：`tradingday`、`as_of_date`、`snapshot_time`、自然日或交易日。
   - 对每个外部输入记录可用日期范围、关键字段覆盖范围和数据版本；不能只检查文件是否存在。
   - 列出依赖图：哪些入口是独立入口，哪些入口必须先运行上游快照或特征任务。
   - 若任务涉及项目建设，先回答以下问题：
     - 项目属于 `domains/`、`platform/`、`workflows/`、`registry/` 还是 `archive/`
     - 主输出是动作/配置/评分/信号，还是状态/提醒/研究报告
     - 输出是否直接服务投资决策
     - 运行频率是什么
     - 原始输入来自哪里，是否真的需要复制进项目目录
     - 当前阶段需要静态 HTML 回测评审文档，还是定型后的交互式跟踪工作台
     - 是否真的需要接入统一前端、`registry/`、`workflows/`
   - 若涉及标签、因子、信号、回测、风控或 fallback，先阅读 [validation.md](references/validation.md)。
2. **规划 (Planning)**:
   - 正式项目、共享模块或生产链路涉及 Add/Mod/Del 功能时，必须先列出计划。
   - 单文件小改、轻量规则调整或研究脚本可使用 3-5 行内联计划，不新建计划文档。
   - 检查配置文件的兼容性。
   - 若任务涉及新项目或项目标准化，先阅读：
     - [architecture.md](references/architecture.md)
     - [project-bootstrap.md](references/project-bootstrap.md)
     - [project-yaml.md](references/project-yaml.md)
     - [storage.md](references/storage.md)
     - [workflows.md](references/workflows.md)
3. **执行 (Execution)**:
   - 用户确认后执行。
   - 正式项目的公开函数、共享模块和数据契约必须编写 Docstrings。
   - 按风险运行 Lint/Type Check/测试；标签、信号、风控和 PnL 模块还必须运行时点一致性、覆盖期和约束测试。
   - 核心金融逻辑缺关键输入、覆盖不足或依赖未满足时必须中断；展示层和诊断层才允许明确标注的降级。

### 2.2 路径规范
- **单一权威源**: 所有路径必须基于 `main_config.py: MAIN_PATH`。
- **相对路径**: 配置文件中只写相对路径 (e.g., `data/sqlite/db.sqlite`)。
- **自动解析**: 加载配置时自动拼接 `MAIN_PATH`。

### 2.3 项目建设默认顺序
1. 先确定项目归属域与 `project_id`
2. 再确定主输出物、消费方、阶段与运行频率
3. 建标准目录与 `project.yaml`
4. 实现 `research` / `publish` / `monitor` 中适用入口，不适用的键显式写 `null`；研究回测期不要为了模板完整而伪造 `publish` 或 `monitor`
5. 分离原始输入、固定资产、单次产物
6. 按“数据快照层 - 共享特征层 - 标签/信号层”拆分职责
7. 为每个正式入口定义 preflight、依赖覆盖和 `run_id`
8. 先让结果正确落到 `artifacts/`，再考虑平台级 `shared_data/`
9. 只有跨项目检索、多人治理或统一工作流确有需要时才接入 `registry/`
10. 需要日常运行时接入 `workflows/`
11. 补最小测试、输出契约和审计检查
12. 最后再扩前端、适配层和平台化能力；定型跟踪使用工作台，纯状态指标使用只读监控视图

## 3. 架构规范 (Architecture)

### 3.1 依赖注入
所有外部依赖（数据库、API、配置）必须通过构造函数注入，禁止在类内部实例化具体实现。

```python
# ✓ 正确
class FundData:
    def __init__(self, data_source: DataSource):
        self._source = data_source

# ✗ 错误
class FundData:
    def __init__(self):
        self._source = SqliteSource("path/to/db")
```

### 3.2 数据层分级
- **Entities/Config**: 使用 `Pydantic Models` (强类型校验)。
- **Bulk Data**: 使用 `pandas.DataFrame` (性能优先)。

### 3.3 工厂模式
使用 `create_data_access_objects(source_type)` 统一管理数据源的创建与切换。

### 3.4 新项目默认落点
- 具体投资命题、研究项目、产品项目、监控项目，优先放 `domains/<domain>/<project_id>/`
- 跨项目复用能力，放 `platform/`
- 纯调度编排，放 `workflows/`
- 台账、实验记录、晋级/退役决议，放 `registry/`
- 冻结历史实现，放 `archive/`

### 3.5 生命周期判断
- 输出动作、配置、评分、信号、候选准入结果，优先判为 `production`
- 输出状态、变化、告警、复核线索，优先判为 `monitor_only`
- 尚处于可重复研究但未形成稳定消费关系，通常为 `research`
- 仅有历史回测、参数比较、模型定型评审或静态 HTML 说明，不代表已经进入 `production` 或 `monitor_only`
- 仅停止日常运行、保留历史价值，才进入 `retired`

## 4. 工程标准 (Engineering)

- **Type Hints**: 公开方法必须包含参数和返回值的类型注解。
- **Docstrings**: 公开方法必须包含 `Args`, `Returns`, `Raises`。
- **Logging**: 
  - `INFO`: 关键流程节点 (开始/结束/统计)。
  - `WARNING`: 可恢复的异常/跳过处理。
  - `ERROR`: 导致中断的错误。

## 5. 项目建设硬约束

- 不要因为项目从 `research` 晋级到 `production` 就搬目录。
- 不要把原始输入默认复制进项目目录；能追溯、能访问时只记录来源。
- 不要在 `src/` 中混放数据库、临时输出、最终报告。
- 不要让 `workflows/` 承载业务实现或直接 import 项目内部函数。
- 不要让统一前端直接消费项目内部临时文件。
- 不要在历史回测阶段默认建设交互式前后端；静态 HTML 评审文档通常已经足够。
- 不要把 Excel 当作核心中间层。
- 不要把只读监控页面做成默认可编辑、可审批或可发布的管理控制台。

## 6. 参考指南 (References)

- **项目建设流程**: 详见 [project-bootstrap.md](references/project-bootstrap.md)
- **架构与边界**: 详见 [architecture.md](references/architecture.md)
- **项目元数据**: 详见 [project-yaml.md](references/project-yaml.md)
- **存储与命名**: 详见 [storage.md](references/storage.md)
- **运行编排**: 详见 [workflows.md](references/workflows.md)
- **代码审查**: 详见 [code_review.md](references/code_review.md)
- **量化验证**: 详见 [validation.md](references/validation.md)
- **LLM开发**: 详见 [llm_dev.md](references/llm_dev.md)
- **Web开发**: 详见 [web.md](references/web.md)
- **计算优化**: 详见 [compute.md](references/compute.md)
- **前后端数据生命周期与删除**: 详见 [data-lifecycle.md](references/data-lifecycle.md)
- **生命周期路由**: 详见 [lifecycle-routing.md](references/lifecycle-routing.md)
