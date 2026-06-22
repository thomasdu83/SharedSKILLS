# QuantSystem 架构与项目边界参考

当需要决定项目应该放在哪里、如何分层、如何晋级、默认数据源怎么选、哪些属于平台能力时，读取本文件。

## 顶层结构

```text
QuantSystem/
├─ platform/
│  ├─ data/
│  ├─ research/
│  ├─ portfolio/
│  ├─ monitoring/
│  │  ├─ dashboard/
│  │  ├─ api/
│  │  ├─ schemas/
│  │  └─ adapters/
│  ├─ reporting/
│  └─ llm/
├─ domains/
│  ├─ macro/
│  ├─ fund/
│  ├─ cta/
│  ├─ equity/
│  └─ allocation/
├─ registry/
│  ├─ projects.yaml
│  ├─ experiments/
│  └─ promotion/
├─ workflows/
│  ├─ daily/
│  ├─ weekly/
│  └─ backfill/
└─ archive/
   └─ legacy/
```

## 各层职责

| 目录 | 作用 | 应放内容 | 不应放内容 |
|---|---|---|---|
| `platform` | 平台共用能力 | 数据访问、回测组件、统一前端、监控接口、LLM 工具 | 单一投资命题代码 |
| `domains` | 项目主目录 | 研究项目、产品项目、监控项目 | 跨项目共享工具 |
| `registry` | 项目治理层 | 项目台账、实验记录、晋级记录 | 业务计算逻辑 |
| `workflows` | 运行编排层 | 日频、周频、补数、回补任务 | 复杂业务实现 |
| `archive` | 历史归档层 | 停止扩展但需保留的旧代码 | 新开发代码 |

## 生命周期模型

项目状态是元数据，不是目录迁移。

| Stage | 含义 | 典型产物 | 是否可直接用于投资 |
|---|---|---|---|
| `idea` | 命题与原型阶段 | 笔记、草稿、探索脚本 | 否 |
| `research` | 可重复研究阶段 | 因子构建、验证、研究报告 | 否 |
| `candidate` | 候选晋级阶段 | 固化 schema、快照、候选入口 | 否 |
| `production` | 产品化阶段 | 排名、评分、信号、组合影响 | 是 |
| `monitor_only` | 监控化阶段 | 状态、告警、变化、复核线索 | 否 |
| `retired` | 退役阶段 | 归档说明、历史结果 | 否 |

### 生命周期规则

- 不要为 `idea`、`research`、`production` 分别建三套目录。
- 同一项目目录内可以同时保留 `research/notes`、`research/prototypes`、`src`、`tests`、`artifacts`、`app`。
- 项目升级时修改 `project.yaml.stage`，并在 `registry/promotion/` 中记录依据。

## 项目包标准

```text
domains/<domain>/<project_id>/
├─ project.yaml
├─ README.md
├─ configs/
│  └─ default.yaml
├─ src/
├─ tests/
├─ runtime_assets/
├─ research/
│  ├─ notes/
│  ├─ prototypes/
│  └─ reports/
├─ artifacts/
│  ├─ research_runs/
│  ├─ production_snapshots/
│  ├─ monitor_snapshots/
│  ├─ charts/
│  └─ reports/
└─ app/
```

补充说明：

- `README.md` 面向人工阅读，说明项目目标、输入、输出和运行方式
- `configs/` 放业务参数配置，不要把阈值、权重、路径散落在代码里
- `runtime_assets/` 放长期保留的小型本地资产，不放单次运行结果
- `artifacts/` 放单次运行产物、图表、报告和项目内快照备份

### 范围收敛

- 一期先定义最小可交付闭环，不要同时并行推进研究平台、前端工作台、监控系统、报告中心。
- 先明确主输出物，再设计实现路径。常见输出物包括全量研究主表、标准化快照、总报告、单只详情页。
- 若场景是个人研究或轻量决策支持，优先交付可重复运行入口、全量主表、快照落地、最小报告。

## 路径与配置

- 所有绝对路径最终都必须基于 `main_config.py: MAIN_PATH`。
- YAML 中只写相对路径，例如 `shared_data/parquet/fund/`。
- 禁止在项目中另写一套 `sys.path` 猜根目录逻辑。
- 调试入口例外：允许在项目 `debug/` 下做最小路径注入，详见 `debug-entrypoints.md`。

## 数据访问与默认源

### 依赖注入

所有外部依赖通过构造函数或工厂传入，禁止在类内部硬编码具体数据源。

```python
class FundData:
    def __init__(self, data_source: DataSource):
        self._source = data_source
```

### 默认优先级

- 默认优先级固定为：`DBSource > ParquetSource > ExcelSource > SqliteSource`
- 新项目、调试入口、研究入口、批处理入口如未显式指定数据源，默认优先尝试 `DBSource`
- `DBSource` 不可用时，默认回退到 `ParquetSource`
- `SqliteSource` 不得作为默认主入口，仅用于元数据、小型状态或人工确认后的特殊场景
- 不要口头假设默认源；实现前先检查 `platform.data.core`、工厂函数和项目 loader 的真实代码

### 选择规则

- 最新数据、研究主链路、生产主链路、真实调试链路：优先 `DBSource`
- 本地快照消费、批量历史读取、数据库不可用时的稳定回放：使用 `ParquetSource`
- 注册表、小型状态、轻量索引：可使用 `SqliteSource`
- 人工输入、外部导入导出：使用 `ExcelSource`

### 实现要求

- `create_data_access_objects()`、项目 loader、debug 入口、批量入口要保持一致的默认优先级
- 如果有回退逻辑，必须记录主数据源、回退原因、实际启用的数据源
- 测试至少覆盖：
  - 默认选择 `DBSource`
  - `DBSource` 失败时回退 `ParquetSource`
  - 项目级 loader 不会悄悄退回 `SqliteSource`

## 全量样本与字段兼容

- 存在“全量观察、统一筛选、后续打标或排序”语义时，优先先构建全量样本主表。
- 行情、分类、费率、资金流、标签、画像等辅助数据默认通过 `left merge` 补到主表。
- 不要让辅助表决定主表保留范围，除非需求明确要求筛掉主对象。
- 辅助数据缺失时默认保留主对象，并显示为 `NA` / `NaN` / `None`，而不是静默删除。
- 平台层和项目层之间优先在入口层统一字段口径，不要把别名、大小写、历史字段差异散落到下游逻辑。
- 字段兼容逻辑必须带回归测试。
- 新增基础维度字段时，至少检查研究主表、产品/监控快照、JSON/Parquet/CSV 输出层和报表/前端消费层。

## 产品与监控边界

- 产品负责决策输出，监控负责状态观察与告警。
- 统一前端不得直接 import 项目内部业务逻辑。
- 统一前端只消费标准化快照、标准 API 或适配层输出。
- 项目内可视化用于研究原型、特殊图表、调试页；统一工作台用于正式消费、跨项目比较和告警中心。

## 何时直接推进

- 目录整理
- 项目包标准化
- 输出契约补齐
- 统一前端接入
- 日志、类型、配置外置

## 何时必须停下

- 改变回测方法学或收益定义
- 改变金融指标口径
- 破坏已有 API / schema / config 兼容性
- 增加或升级依赖
- 删除历史数据或执行破坏性迁移

## 常见反模式

- 按生命周期搬项目目录，而不是维护单项目主目录
- 在业务项目里重复实现数据访问、前端壳、路径解析
- 用 Excel 作为核心中间层
- 让统一前端直接读取项目内部数据库表结构
- 每个 `monitor_only` 项目都建完整独立前端
- 把平台能力塞进 `domains`
- 把业务命题塞进 `platform`
- 新代码继续散落在仓库根目录
- 把结果表直接做成筛选后的名单，而不是先保留全量研究对象
- 让辅助数据缺失隐式删掉主对象
- 在调试时依赖 IDE 私有参数配置，却没有项目内可复现的调试入口
- 优化性能前不定位热点，直接大面积改写实现
- 新增字段后只在 `DataFrame` 中出现，但未检查快照、JSON 序列化和报表链路
