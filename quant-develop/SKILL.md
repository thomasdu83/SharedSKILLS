---
name: quant-develop
description: QuantSystem 机构级量化投资系统开发与项目建设规范。适用于新项目创建、旧项目标准化改造、`project.yaml` 设计、`registry/` 与 `workflows/` 接入、数据输出契约落地，以及数据获取、组合构建、回测分析等全流程开发。
---

# QuantDevelop 开发规范

机构级量化投资系统的核心开发规范，旨在提供清晰、统一、可维护的工程标准，并让项目从一开始就具备可治理、可接入、可复核的结构。

## 1. 核心原则 (Core Principles)

- **Fail Fast**: 参数校验在函数入口立即执行，禁止静默失败。
- **Explicit**: 显式依赖注入，显式类型注解，显式参数传递。
- **Config-Driven**: 业务参数（如权重、路径、阈值）必须在 YAML 配置中，禁止硬编码。
- **No Print**: 严禁使用 `print()`，必须使用 `logging`。
- **Single Project Home**: 一个项目一个主目录，生命周期只由 `project.yaml.stage` 管理，不靠搬目录。
- **Outputs First**: 先定义主输出物、消费方和运行频率，再决定目录、入口和工作流。

## 2. 工作流 (Workflow)

### 2.1 任务三部曲
1. **分析 (Analysis)**:
   - 优先使用 MCP 查询数据/代码。
   - 明确当前任务是“新项目建设”“旧项目标准化”还是“已有项目功能开发”。
   - 明确数据源 (Parquet/DB/Excel)。
     - **Parquet (默认)**: 适用于所有高频、时序、大批量数据（行情、因子、财务）。
     - **SQLite**: 仅限于极少量元数据、配置或轻量级关系型数据。
     - **Excel**: 仅限于手工输入或展示。
   - 若任务涉及项目建设，先回答以下问题：
     - 项目属于 `domains/`、`platform/`、`workflows/`、`registry/` 还是 `archive/`
     - 主输出是动作/配置/评分/信号，还是状态/提醒/研究报告
     - 输出是否直接服务投资决策
     - 运行频率是什么
     - 原始输入来自哪里，是否真的需要复制进项目目录
     - 是否需要接入统一前端、`registry/`、`workflows/`
2. **规划 (Planning)**:
   - 涉及 Add/Mod/Del 功能时，必须先列出计划。
   - 检查配置文件的兼容性。
   - 若任务涉及新项目或项目标准化，先阅读：
     - [architecture.md](references/architecture.md)
     - [project-bootstrap.md](references/project-bootstrap.md)
     - [project-yaml.md](references/project-yaml.md)
     - [storage.md](references/storage.md)
     - [workflows.md](references/workflows.md)
3. **执行 (Execution)**:
   - 用户确认后执行。
   - 必须编写 Docstrings。
   - 运行 Lint/Type Check 验证。

### 2.2 路径规范
- **单一权威源**: 所有路径必须基于 `main_config.py: MAIN_PATH`。
- **相对路径**: 配置文件中只写相对路径 (e.g., `data/sqlite/db.sqlite`)。
- **自动解析**: 加载配置时自动拼接 `MAIN_PATH`。

### 2.3 项目建设默认顺序
1. 先确定项目归属域与 `project_id`
2. 再确定主输出物、消费方、阶段与运行频率
3. 建标准目录与 `project.yaml`
4. 实现 `research` / `publish` / `monitor` 中适用入口，不适用的键显式写 `null`
5. 分离原始输入、固定资产、单次产物
6. 先让结果正确落到 `artifacts/`，再考虑平台级 `shared_data/`
7. 接入 `registry/`
8. 需要日常运行时接入 `workflows/`
9. 补最小测试与契约检查
10. 最后再扩前端、适配层和平台化能力

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
- 不要把 Excel 当作核心中间层。

## 6. 参考指南 (References)

- **项目建设流程**: 详见 [project-bootstrap.md](references/project-bootstrap.md)
- **架构与边界**: 详见 [architecture.md](references/architecture.md)
- **项目元数据**: 详见 [project-yaml.md](references/project-yaml.md)
- **存储与命名**: 详见 [storage.md](references/storage.md)
- **运行编排**: 详见 [workflows.md](references/workflows.md)
- **代码审查**: 详见 [code_review.md](references/code_review.md)
- **LLM开发**: 详见 [llm_dev.md](references/llm_dev.md)
- **Web开发**: 详见 [web.md](references/web.md)
- **计算优化**: 详见 [compute.md](references/compute.md)
