# Shared Skill Map

这份库的目标不是“把所有技能都记住”，而是让 AI 先命中正确的主线，再少量下钻。

## 先选一个主入口

按用户意图和本阶段主交付物选择；canonical id、兼容别名和允许的辅助见 `skill-registry.yaml`。
注册表是模型读取的协议，`validate_route_decision.py` 校验结果结构，不会自动执行关键词分类。

| 用户主要要什么 | 主入口 |
|---|---|
| 新建量化策略/模型，包括按论文实现 | `ai-quant-development-router`；论文方法为辅助 |
| 轻量取数/计算/研究验证 | `quant-research-coding` |
| 原型正式化、共享定期运行 | `quant-develop` |
| 产品要素/合同/净值事实 | `wisdom-manager-product-research` |
| 尽调材料入库/查询 | `fund-wiki`；综合研究才进入 `fund-wiki-research` |
| 周度宏观判断、预测快照、到期复盘、持久机制框架 | `macro-strategy-learning` |
| 仅排版已有结果，或独立构建页面 | `frontend-page-router` → 选 report 或 ops |
| 技术图表 | `archify` |
| 仅审读来源、列复现缺口、审计已有复现 | `investment-paper-replication` |
| 孤立 bug/失败测试 | `systematic-debugging` |

- `frontend-design` → `frontend-page-router`，`architecture-diagram` → `archify`。旧名只作兼容，不形成第二个主入口。
- 每阶段一主、0–2 辅；转交后生成下一阶段记录，不一次预加载整个技能链。
- 已有页面结果的排版不重新计算模型。研究/工程任务附带网页时，页面技能只作交付辅助。
- 普通解释无需硬套流程；未知/歧义保留 unresolved，不捏造合法入口。

## 分析师咨询

点名咨询选对应分析师；未点名但明确需要中金视角时按最具体主题选一位。

| 分析师 | 默认专题 | Skill |
|---|---|---|
| 刘刚 Kevin | 港股、中概股、海外权益 | `cicc-research-analyst-kevin-skill` |
| 李求索 | A股策略、行业与主题配置 | `cicc-research-analyst-lqs-skill` |
| 李昭 | 黄金贵金属、跨资产配置 | `cicc-research-analyst-lz-skill` |
| 缪延亮 | 全球宏观、通胀、国际金融 | `cicc-research-analyst-myl-skill` |
| 韦璐璐 | 中国债市、利率和机构流动性 | `cicc-research-analyst-wll-skill` |
| 周彭 | 中国经济制度、资金配置、产业传导 | `cicc-research-analyst-zp-skill` |

明确点名优先于默认专题映射。跨专题同等匹配时澄清，普通概念解释不自动调用远程接口。
周度预测仍以 `macro-strategy-learning` 为主；点名观点是可选辅助来源，不能替代冻结快照和复盘。
六个 Skill 调用中金点睛服务，依赖统一登记；`active` 表示规则可用，不代表远程服务已通过实测。

## 编程风险分层

| 风险等级 | 典型场景 | 首选 skill | 验证要求 | 避免默认使用 |
|---|---|---|---|---|
| 一级：一次性小任务 | 临时取数、清洗、格式转换、快速图表、一次性计算 | `quant-research-coding` / `zmdata-data-api` | 样本输出、行数/日期/缺失值检查、脚本实际运行一次 | `quant-develop`、`old-coder`、正式计划文档、代码审查 |
| 二级：日常研究代码 | 可复跑研究脚本、轻量回测、静态 HTML 回测评审文档、报告素材表、基金筛选辅助 | `quant-research-coding` | 可复跑入口、关键 sanity checks、完成前验证 | `old-coder`、子代理开发、完整 PR 流程 |
| 三级：公司/客户敏感 | 投委会/客户材料、定期监控、共享信号、组合构建输入、定型模型跟踪工作台、只读指标监控 | `quant-develop` | 测试/契约/日志/代码审查/新鲜验证 | 只做手动检查 |
| 四级：重大损失级 | 生产交易、不可逆写入、权限安全、监管或极高损失链路 | `old-coder` + 人工审批/独立审查/外部控制 | SPEC、测试关卡、证据报告、部署门禁 | AI 自主交付或单一验证 |

## 主线路由

| 任务意图 | 首选 skill | 常见后续 | 说明 |
|---|---|---|---|
| 私募管理人 / 产品事实查询 | `wisdom-manager-product-research` | `fund-wiki-research` | 先拿事实，再做判断 |
| 私募尽调转录 / 路演材料生成同目录 Markdown | `private-fund-dd-note` | `mynotes-knowledge-manager` / `PE_ODD_Auditor` | 先整理定性尽调草稿，再决定是否入库、评分或归档 |
| ZM 数据接口 / 代码示例 / ID 映射 | `zmdata-data-api` | `quant-develop` | 作为底层数据能力 |
| 尽调材料入库、沉淀、查询 | `fund-wiki` | `fund-wiki-research` | 事实层与知识层分开 |
| 基于 fund-wiki 的专题研究 | `fund-wiki-research` | `research-report-writer` | 可比池、分类、研究稿 |
| fund-wiki + 当前数据层双源研究 | `fund-wiki-research` | `wisdom-manager-product-research` / `zmdata-data-api` | 适合策略/团队/绩效判断 |
| 轻量量化研究代码 / 一次性脚本 / 探索性回测 | `quant-research-coding` | `zmdata-data-api` / `verification-before-completion` | 一级、二级默认入口 |
| AI 辅助开发新的量化策略/模型（有无前端均可） | `ai-quant-development-router` | `quant-research-coding` / `quant-develop` / `frontend-page-router` / `verification-before-completion` | 自动识别最小可验证闭环并路由专业技能；不替代量化或前端实现规范 |
| 历史回测 / 模型研究评审 / 静态 HTML 回测文档 | `quant-research-coding` | `frontend-report-page` / `research-report-writer` | 专注模型假设、样本口径、表现、风险、稳健性和复现证据，不默认做交互系统 |
| 量化系统开发、回测、组合工程 | `quant-develop` | `systematic-debugging` | 正式项目、复用模块、工程与契约；进入组合时必须接 `investment-feedback` |
| 前后端触发数据更新/计算、缓存刷新、删除旧数据 | `quant-develop` | `frontend-ops-platform` / `verification-before-completion` | 先读 `quant-develop/references/data-lifecycle.md`，统一任务状态、预览确认、并发锁、缓存失效和空状态 |
| 定型模型跟踪 / 监控 / 发布门禁 / 运行工作台 | `quant-develop` | `frontend-ops-platform` / `verification-before-completion` | 只有进入跟踪、监控、发布或人工操作时才做前后端交互 |
| 非模型指标长期观察 / 只读监控 | `quant-develop`（轻量 `monitor_only`） | `frontend-ops-platform` 的 `read_only_monitor` | 按投资问题归组，不自动引入 Champion、回测或编辑审批链 |
| MyNotes/Obsidian 知识沉淀、Inbox 处理、MOC、AI知识库管理 | `mynotes-knowledge-manager` | `pdf` / `docx` / `investment-paper-replication` / `quant-develop` | 先沉淀知识，再决定是否项目化或联动 QuantSystem |
| 自动宏观研报评分、PDF上下文准备、结果归档到Excel/DB | `assets-score` | `macro-strategy-learning` | 只处理自动评分与归档，不负责定性周度判断或机制框架 |
| 周度全球多资产宏观判断、情景概率、预测快照、到期复盘、黄金/流动性/政策传导等专题框架积累 | `macro-strategy-learning` | `mynotes-knowledge-manager` / `assets-score` / `research-report-writer` | 负责定性判断学习闭环；`assets-score` 仍只负责研报评分与归档 |
| 高保障代码实现 / 证明它能跑 | `old-coder` | `test-driven-development` / `verification-before-completion` | SPEC → 测试关卡 → 证据报告 |
| 定量报告质检与解读 | `quant-report-qa-interpreter` | `research-report-writer` | 报告审查与再表达 |
| 投后归因报告 | `fof-risk-report-generator` | `fund-wiki-research` | 先归因，再写结论 |
| 策略标签 / 赛道审计 | `fund-track-tag-audit` | `fund-wiki` | 适合标签修正与证据核对 |
| ODD 审计 | `pe-odd-auditor`（兼容别名 `PE_ODD_Auditor`） | `docx` / `pptx` / `pdf` | 风控与合规穿透 |
| 研究报告写作 | `research-report-writer` | `docx` / `pptx` / `xlsx` | 负责表达和结构 |
| 论文 / 策略复现 | 来源审读用 `investment-paper-replication`；新模型用 `ai-quant-development-router` | 来源方法作为辅助 | 避免两个项目总控 |

## 辅助分组

### 文档与交付

- `pdf`
- `docx`
- `pptx`
- `xlsx`
- `frontend-report-page`
- `frontend-ops-platform`

### 代码与流程

- `quant-research-coding`
- `systematic-debugging`
- `verification-before-completion`
- `test-driven-development`
- `writing-plans`
- `executing-plans`
- `subagent-driven-development`
- `old-coder`
- `using-git-worktrees`
- `finishing-a-development-branch`

### 评审与沟通

- `requesting-code-review`
- `receiving-code-review`
- `chinese-code-review`
- `chinese-documentation`
- `chinese-git-workflow`
- `chinese-commit-conventions`

### 元技能

- `using-superpowers`
- `writing-skills`
- `skill-creator`
- `zm-skills-manager-local`
- `workflow-runner`

## 推荐工作流

1. 先事实：`wisdom-manager-product-research` 或 `zmdata-data-api`
2. 再沉淀：`fund-wiki`
3. 再判断：`fund-wiki-research`
4. 再表达：`research-report-writer`
5. 再质检或交付：`quant-report-qa-interpreter`、`fof-risk-report-generator`、`docx`、`pptx`、`xlsx`

## 最小路由规则

- 事实优先于观点。
- 域技能优先于元技能。
- 具体技能优先于通用技能。
- 入口越短，触发越稳。
- 新建或实质扩展量化策略/模型时，自动先进入 `ai-quant-development-router`；有无前端均适用，前端再按页面任务继续路由。
- 研究脚本先轻量验证，项目化信号出现后再上 `quant-develop`。
- 历史回测优先静态 HTML 评审文档；定型后跟踪才优先交互式工作台。
- `production` 表示输出建议权重/配置/信号；`monitor_only` 只表示状态、变化、告警和复核线索。
- 没有冻结研究产物、目标权重、组合约束、成本假设、实际持仓、成交和归因证据时，只能输出研究或待复核状态，不得声称已完成组合评估、实盘执行或模型退役。
- 项目阶段与模型版本状态分开；Registry 按跨项目治理需求启用，不作为所有项目的默认前置条件。
- 只读监控页面默认提供筛选、刷新和下钻，不增加编辑、审批或发布按钮。
- 普通 TDD 不触发 `old-coder`；只有用户明确要证据报告或高保障时才触发。

## 统一执行结果

核心入口完成启动检查后，都应按 `shared-contracts/execution.yaml` 返回最小结果：
`status`、`decision`、`evidence`、`limitations`、`unresolved`、`next_action`。
`blocked`、`needs_review` 和 `draft` 是可交付的真实状态，不能被改写成“已完成”或“已验证”。
