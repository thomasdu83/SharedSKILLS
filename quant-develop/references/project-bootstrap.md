# QuantSystem 新项目建设参考

当任务是“创建新项目”“把散落脚本收敛成标准项目包”“补齐 `project.yaml` / `registry` / `workflows` 接入”时，读取本文件。

## 1. 先判断项目应该放在哪里

- 具体投资命题、研究项目、产品项目、监控项目：放 `domains/<domain>/<project_id>/`
- 跨项目通用能力：放 `platform/`
- 纯调度编排：放 `workflows/`
- 项目台账、实验记录、晋级或退役决议：放 `registry/`
- 冻结的历史实现：放 `archive/`

不要因为项目从 `research` 晋级到 `production` 就搬目录。目录是项目主家，阶段只改 `project.yaml.stage`。

## 2. 创建前必须回答的问题

- 这个项目属于哪个研究域
- 最终输出是什么：动作、配置、评分、信号、状态、提醒，还是研究报告
- 输出是否直接服务投资决策
- 更新频率是什么：日频、周频、月频、季频、事件驱动或一次性研究
- 输入来自哪里：数据库、Parquet、Excel、网盘、API、人工维护表
- 原始输入是否真的需要复制进项目目录
- 当前阶段需要静态 HTML 研究/回测评审文档，还是定型后的交互式跟踪工作台
- 未来是否真的需要接入统一前端、统一 `workflows/` 或 `registry/`

## 3. 生命周期阶段判断

仅允许以下 `stage`：

- `idea`
- `research`
- `candidate`
- `production`
- `monitor_only`
- `retired`

快速判断：

- 输出“动作”或“配置”，优先判为 `production`
- 输出“状态”或“提醒”，优先判为 `monitor_only`
- 有可重跑研究入口和研究输出，但尚未形成稳定消费链路，通常为 `research`
- 历史回测、参数比较、模型定型评审或静态 HTML 说明，不等于已经进入 `production` 或 `monitor_only`
- 已停止主动运行、只保留历史参考，才进入 `retired`

### 项目阶段与模型版本

`project.yaml.stage` 只描述项目整体阶段。模型家族内部的版本、场景和求解器可以有各自的 Research、Candidate、Challenger、Champion 或 Rejected 状态，不应通过搬目录或修改项目阶段代替版本治理。

`production` 适用于输出建议权重、配置、评分或信号的项目；`monitor_only` 只适用于输出状态、变化、告警和复核线索的项目。一个 `production` 项目可以同时拥有 `publish` 与 `monitor` 入口。

### 研究晋级包与淘汰结果

从轻量研究升级为正式项目时，至少保留：研究假设、可复跑入口、参数集、PIT/data scope、验证证据、失败条件和晋级理由。临时脚本不必登记；进入正式比较批次的失败模型必须保留 manifest、结果和排除原因，不能通过删除失败项美化比较。

## 4. 标准目录

推荐新项目默认目录：

```text
domains/<domain>/<project_id>/
├─ project.yaml
├─ README.md
├─ configs/
│  └─ default.yaml
├─ src/
│  └─ <python_package>/
│     ├─ __init__.py
│     ├─ run_research.py
│     ├─ publish.py          # production 阶段需要时再创建
│     ├─ run_monitor.py      # monitor_only 阶段需要时再创建
│     ├─ core/
│     ├─ contracts/
│     ├─ inputs/
│     └─ outputs/
├─ tests/
├─ runtime_assets/
└─ artifacts/
   ├─ research_runs/
   ├─ production_snapshots/
   ├─ monitor_snapshots/
   ├─ charts/
   └─ reports/
```

目录边界：

- `src/` 只放源码与运行必需配置
- `runtime_assets/` 放长期保留的小型资产，如 SQLite、Excel、映射表
- `artifacts/` 放单次运行产物、图表、报告
- 原始输入默认留在原始数据源或外部目录，只记录来源

常见反模式：

- `src/db`
- `src/output`
- `src/tmp`
- `结果最终版.xlsx`
- `monitor_final_final.xlsx`

## 5. `project.yaml` 最小要求

最小字段：

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

关键规则：

- `stage` 表示生命周期阶段，`status` 表示当前运行状态，二者不可混用
- `runtime_entrypoints` 必须显式写出 `research`、`publish`、`monitor`
- 某类入口不适用时写 `null`，不要省略键名
- research 回测阶段通常只有 `research`，不要为了模板完整而创建空的 `publish.py` 或 `run_monitor.py`
- `data_dependencies` 写数据集名称，不写临时文件名
- `storage` 写相对路径或标准数据集位置，不写机器绑定绝对路径

## 6. 标准入口

- `research`：研究重跑、验证、实验复现，允许生成结构化审计证据和静态 HTML 回测评审文档
- `publish`：生成正式产品快照、评分、信号、权重或结构化结果；research / candidate 阶段默认 `null`
- `monitor`：生成监控快照、状态变化、告警或复核线索；只有定型后跟踪或监控时填写

入口要求：

- 参数显式传入，避免依赖当前工作目录
- 路径通过配置或项目根推导
- 参数校验 fail fast
- 使用 `logging`
- 输出结构化结果；研究回测的静态 HTML 是评审文档，不能替代 manifest、审计表和可复现输出

## 7. 输入、固定资产和运行产物

三类内容必须分开：

- 原始输入：保留在原始数据源或外部目录，默认不复制进项目
- 固定资产：放 `runtime_assets/`
- 单次产物：放 `artifacts/`

默认做法：

- 研究阶段先写 `artifacts/research_runs/`
- 进入 `candidate`、`production`、`monitor_only` 后，正式消费数据逐步写入平台级 `shared_data/`

## 8. Registry 与 Workflow

新项目创建后，按实际消费关系考虑：

- 是否需要登记到 `registry/projects.yaml`
- 是否需要在 `registry/promotion/` 留下晋级、暂停、退役决议
- 是否需要接入 `workflows/daily`、`workflows/weekly` 或 `workflows/backfill`

边界规则：

- `workflows/` 只调度项目标准入口
- 不在工作流中写项目业务算法
- 不在工作流中硬编码项目内部临时文件

## 9. 最小测试要求

至少覆盖：

- 配置文件能被正确加载
- `project.yaml` 必填字段存在
- 至少一个标准入口能在最小样本下运行
- 输出目录与命名符合规范
- 关键输入缺失时 fail fast
- 输出 schema 与契约一致

## 10. 推荐执行顺序

1. 确定项目归属域和 `project_id`
2. 建 `domains/<domain>/<project_id>/` 标准目录
3. 编写 `project.yaml`
4. 编写 `README.md`
5. 建 `configs/`
6. 实现适用入口
7. 梳理输入、固定资产和运行产物边界
8. 把研究结果先落到 `artifacts/research_runs/`
9. 补最小测试
10. 只有确有跨项目检索、多人治理或统一工作流需求时才登记到 `registry`
11. 需要日常运行时接入 `workflows`
12. 需要展示时先做静态报告或 preview；只有定型跟踪、监控、发布或人工操作才接统一前端或标准 adapter

## 11. 验收清单

- 位于正确的 `domains/<domain>/<project_id>/` 目录下
- 已有唯一主 `project.yaml`
- `stage` 与 `status` 语义清晰
- 已有 `README.md`
- 已区分原始输入、固定资产、运行产物
- `src/` 未混入输出、数据库或临时文件
- 至少一个标准入口可运行
- 结果写入 `artifacts/` 标准子目录
- 已有最小测试或最小验证脚本
- 若项目需要跨项目检索或统一治理，已登记到 `registry`
- 若仍处于 research 阶段，前端产物应是静态 HTML 评审文档或 preview，而不是交互式运行工作台

晋级到正式消费前，再检查：

- 输出契约是否稳定
- 正式快照是否可被下游或前端消费
- `workflow` 是否只负责编排
- 失败路径是否不会静默产出空结果
- 晋级决议是否已留痕
