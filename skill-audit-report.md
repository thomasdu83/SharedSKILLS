# 量化投资工作经验沉淀体系审计与改进方案

审计日期：2026-09-10  
审计对象：

- `F:\Thomas\SharedSKILLS` 当前工作区中的 56 个 `SKILL.md` 及其附属资源；
- `F:\Thomas\QuantSystem\.trae\rules` 下的 3 个项目规则文件；
- `F:\Thomas\QuantSystem\.trae\skills` 下的项目内技能副本及项目资源；
- `F:\Thomas\QuantSystem\docs\templates` 下的指标监控与数据密集型前端模板。

审计方法：只阅读原始文件和目录结构，不调用这些项目中的 skill 工作流，也不把 skill 的自我描述当成有效性证明。审计视角是资深投资经理长期使用能力较弱的 LLM，重点关注研究判断质量、组合决策、证据链、路由稳定性、可复现性和维护成本。本报告评估的是制度设计和可执行性，不等同于对任何策略的实际收益、风险或管理人质量背书；尚未用历史任务样本做运行时路由压力测试，也没有把外部数据质量和实际团队执行率纳入评分。

## 一、结论先行

这套技能库已经超过“提示词集合”的阶段，正在形成一套投资研究操作系统。它最有价值的部分有四个：

1. **量化研究已经有风险分层。** `quant-research-coding`、`quant-develop`、`old-coder` 和 `verification-before-completion` 试图区分一次性探索、正式项目、高保障代码和完成前验证，方向正确。
2. **事实层和判断层开始分离。** `wisdom-manager-product-research`、`fund-wiki`、`fund-wiki-research` 的链路强调“先事实、再沉淀、再研究”，这是基金研究最重要的底层纪律。
3. **金融时间语义和证据链意识较强。** PIT、`as_of_date`、快照、fallback、审计漏斗、`run_id`、输出契约等内容，已经明显高于一般 LLM 工作流。
4. **宏观和尽调技能开始具备可复盘性。** `macro-strategy-learning` 强调情景概率、证伪条件、冻结快照和成熟度复盘；`private-fund-dd-note` 强调公开事实、管理人口径、冲突和待核实事项分层。

主要问题不是缺少规则，而是规则尚未被压缩成一个较弱模型也能稳定执行的系统：

- **路由层、专业流程层、交付层、工程层混在同一个技能命名空间。** 用户一句“做一个量化策略报告”可能同时命中 `ai-quant-development-router`、`investment-paper-replication`、`quant-research-coding`、`frontend-page-router`、`frontend-report-page` 和 `research-report-writer`。
- **技能正文普遍偏长，硬门槛与解释性内容没有分层。** 56 个技能中有多份超过 1,000 词；`writing-skills` 自身也有 1,311 词。较弱模型容易只读到前半段，或者把建议当成强制规则。
- **很多“必须”只存在于自然语言里，没有统一的状态机、输入契约、输出契约和失败处理。** 模型可以说“已验证”，却没有被要求给出结构化证据对象。
- **引用资源有明显漂移。** 多个技能要求读取当前仓库并不存在的 `docs/templates/...`、`references/...` 或 `scripts/...`；部分脚本真实存在于子项目下，但技能写的是技能根目录路径。强模型会自己修正，弱模型会报错、跳过，或臆造结果。
- **投资判断的“事实—推断—建议”隔离还没有成为全库统一协议。** 目前在基金、宏观、尽调技能中分别出现了类似规则，但字段、标签和证据等级不一致。
- **有些高风险规则存在内在矛盾。** `PE_ODD_Auditor` 第 25—40 行同时出现“推定违背”与“默认缺失视为满足”的反转表述；第 116—126 行又把缺失默认判为满足。这个矛盾足以导致审计结论方向相反。

我的总体评级：**研究工程治理较强，事实与时间纪律较强，技能产品化和路由治理中等，组合与实盘反馈闭环偏弱，弱模型可执行性不足。**

从投资结果链条看，当前体系覆盖最充分的是“投资问题之后到可复现研究产物”这一段，对“研究结论之后到组合收益与模型退役”覆盖不足。一个没有未来函数的回测仍可能没有 alpha；一个成功刷新的监控项目仍可能不改变配置；一份完整的尽调报告仍可能没有给出容量、条款和组合角色的可执行结论。

### 投资经理评分

以下评分不是对单个技能的代码质量打分，而是判断这套体系能否帮助投资经理在有限时间内作出可追溯、可执行、可复盘的决策。5 分表示已经形成稳定的制度和工具闭环，3 分表示关键环节依赖有经验的人补足，1 分表示容易产生不可接受的误判。

| 能力维度 | 评分 | 依据 | 对投资工作的含义 |
|---|---:|---|---|
| 研究工程与可复现性 | 4.0/5 | 有分级开发、验证、审计产物和项目阶段意识 | 能较好减少脚本不可复跑、结果不可解释的问题 |
| 数据时间语义与 PIT | 4.0/5 | 多处要求 `as_of_date`、历史快照、覆盖预检和禁止未来函数 | 适合建立可信研究输入，但仍需统一成一个数据契约 |
| 基金事实与尽调证据 | 3.5/5 | 有事实层、管理人口径、公开核验和 review gate | 基础纪律较好，ODD 评分逻辑矛盾会放大尾部风险 |
| 统计有效性与样本外治理 | 3.0/5 | 已提到成本、容量、稳健性，预注册和多重检验预算尚未成为硬门 | 容易把“回测通过”误解为“存在可持续 alpha” |
| 组合构建、交易与容量 | 2.0/5 | 有零散组合 API 和报告字段，缺少统一的信号到实际持仓链 | 研究结论难以稳定转化为风险预算、权重和执行计划 |
| 实盘监控、归因与模型退役 | 2.0/5 | 有投后归因和宏观复盘，但缺少预测—持仓—PnL 的统一闭环 | 可能发现异常，却不能自动判断减仓、暂停或退役 |
| 经验沉淀与知识反馈 | 3.0/5 | `project-retrospective` 已有复盘、抽象和 Skill 回写提案，但还缺少任务级复盘、结果影响、晋级验证和规则淘汰 | 能积累经验，但还不能证明经验已经转化为稳定的未来能力 |
| 较弱 LLM 的稳定执行 | 2.5/5 | 规则丰富但正文长、入口多、证据对象不统一 | 强模型可以补上下文，弱模型容易漏门槛或误路由 |

综合判断为 **3.0/5：一个较好的研究操作系统雏形，还不是完整的投资决策与投资组合操作系统**。下一轮工作应优先提高组合、实盘反馈和模型生命周期分数，而不是继续增加技能数量。

## 二、当前技能库的结构判断

从投资经理视角，目标不应只是“按正确 skill 完成任务”，而应服务于这条链：

```text
投资问题
→ 可证伪假设
→ 数据与时间口径
→ 研究设计
→ 样本内/样本外验证
→ 成本、容量与风险评估
→ 组合配置与执行
→ 实际收益和偏差归因
→ 预测校准、模型维护或退役
```

现有规则对前四步和研究工程部分覆盖较好，对后四步覆盖不完整。必须明确区分三类结论：代码是否正确运行、研究结论是否在正确样本和正确成本假设下成立、结论是否值得进入组合并持续创造风险调整后收益。当前体系不能把前两类证据自动当成第三类答案。

建议把现有技能分成四层，而不是让所有技能直接竞争触发：

| 层 | 职责 | 当前代表 | 主要问题 |
|---|---|---|---|
| 入口路由层 | 识别任务类型、风险和主交付物 | `ai-quant-development-router`、`frontend-page-router`、`brainstorming`、`writing-plans` | 入口过多，优先级不明确，容易连续加载 |
| 投资领域层 | 处理事实、数据、研究、尽调和判断 | `zmdata-data-api`、`public-data-collector`、`fund-wiki-research`、`macro-strategy-learning`、`PE_ODD_Auditor` | 各自有规则，但缺少统一证据和状态协议 |
| 交付层 | 生成报告、网页、文档、表格、归因产物 | `research-report-writer`、`frontend-report-page`、`docx`、`pptx`、`xlsx`、`FOF_Risk_Report_Generator` | 与领域技能边界重复，容易过早进入排版 |
| 工程保障层 | 验证、调试、项目化、审查和收尾 | `quant-develop`、`systematic-debugging`、`verification-before-completion`、`old-coder` | 规则很多，但较弱模型难以判断何时升级和如何留证 |

建议实际只保留一个主入口决策：

```text
任务意图 → 风险级别 → 事实/研究/工程模式 → 一个主技能 → 0–2 个辅助技能 → 统一证据包
```

不要让 LLM 自己在六个“可能都相关”的技能之间自由组合。主技能只负责当前目标，辅助技能只补一项缺口。

### 56 个技能的职责盘点

这次审计没有把所有技能都当成投资判断技能，而是按它们在工作链中的作用分组。这样可以避免因为某个文档或前端技能写得很完整，就误认为投资模型本身已经完成治理。

| 组别 | 技能范围 | 审计判断 |
|---|---|---|
| 路由与讨论 | `ai-quant-development-router`、`brainstorming`、`writing-plans`、`executing-plans`、`dispatching-parallel-agents`、`subagent-driven-development` | 有较清楚的“先澄清、再计划、再执行”意图，但入口和人工确认语义需要统一 |
| 量化研究与工程 | `quant-research-coding`、`quant-develop`、`quant-project-review`、`investment-paper-replication`、`old-coder`、`systematic-debugging`、`test-driven-development`、`verification-before-completion` | 是体系最强的一组，已有 PIT、preflight、运行证据和项目阶段；缺少统一组合与实盘生命周期 |
| 数据与事实 | `zmdata-data-api`、`public-data-collector`、`wisdom-manager-product-research`、`fund-wiki`、`fund-wiki-research`、`fund-track-tag-audit` | 内部源优先、事实层与研究层分离做得好；跨仓库路径和身份解析需要统一契约 |
| 基金与风控 | `private-fund-dd-note`、`PE_ODD_Auditor`、`quant-report-qa-interpreter`、`FOF_Risk_Report_Generator`、`assets-score` | 最接近投前和投后实际工作，但判定状态、缺失证据和分数边界存在高风险不一致 |
| 宏观与行业研究 | `macro-strategy-learning`、`commodity-meso-market-report` | 宏观快照和复盘成熟；需要把宏观概率、资产表达、实际仓位与归因连接起来 |
| 报告、文档与表格 | `research-report-writer`、`frontend-report-page`、`docx`、`pdf`、`pptx`、`xlsx` | 交付能力较完整；应强制消费冻结的研究 artifact，不能在排版阶段改写事实和判断 |
| 前端与图形 | `frontend-design`、`frontend-page-router`、`frontend-ops-platform`、`architecture-diagram-generator/architecture-diagram`、`archify`、`custom-gpt-image-2` | 页面模式判断和机构风格清楚；视觉规则不应成为研究质量或生产准入的替代品 |
| 知识库与项目沉淀 | `mynotes-knowledge-manager`、`project-retrospective`、`workflow-runner`、`mcp-builder` | 有利于经验沉淀和自动化，但必须区分“候选规则”“已批准规则”和“已应用规则” |
| 团队、Git 与规范 | `chinese-code-review`、`chinese-commit-conventions`、`chinese-documentation`、`chinese-git-workflow`、`github-project-workflow`、`receiving-code-review`、`requesting-code-review`、`finishing-a-development-branch`、`using-git-worktrees` | 工程协作规范丰富；不应把 Git 交付状态误当成投资模型通过状态 |
| Skill 与插件管理 | `skill-creator`、`writing-skills`、`zm-skills-manager-local`、`using-superpowers` | 能支持扩展和维护，但当前最需要的是注册、依赖、版本和回归测试，而不是继续增加入口 |

上述分组覆盖目录扫描的 56 个 `SKILL.md`；`fund-wiki-research` 等技能可以承担两个相邻职责，因此分组不是新的路由规则。

### SharedSKILLS 与 QuantSystem 副本

SharedSKILLS 的 56 个 `SKILL.md` 在 QuantSystem 副本中都能找到同路径且 SHA-256 一致；QuantSystem 另外还有一个嵌套的 `fund-wiki\fund-wiki-research\SKILL.md`，因此不能简单说两边都是同一份 56 个文件。QuantSystem 副本同时包含项目专用脚本、评估用例、历史报告、临时 JSON、缓存和编译产物，SharedSKILLS 也包含运行缓存。问题因此不是“今天是否一致”，而是以后修改时没有明确的 source of truth、版本锁定、覆盖规则和同步方式，弱模型还可能把历史产物当作规范。

建议明确两层模型：

```text
SharedSKILLS = 可复用 skill 源码和通用 references
QuantSystem/.trae/skills = 按项目锁定版本的发行快照 + 项目适配器
```

项目内增加 `skill-lock.yaml`，记录 `skill_id`、版本、源路径、内容 hash、项目覆盖项和同步时间。技能发行包排除 `__tmp_*`、`.mypy_cache`、`.pytest_cache`、`__pycache__`、历史 HTML 和调试输出；项目成果应留在项目 `artifacts/`。

### 规则和技能的优先级

`.trae\rules\always_rules.md` 和 `superpowers-zh.md` 明确标记为常驻规则，`karpathy-guidelines.md` 则以行为指南描述存在，加载语义没有同样明确。与此同时，`superpowers-zh.md` 又说明行为类规则应按需读取。这会让不同 LLM 对“是否必须加载”产生不一致。新量化项目需要确认后再做，轻量研究又应快速推进，不能只靠自然语言解决。

应改成机器可读的风险门控：低风险、可逆、研究专用任务可直接推进；改变方法学、数据契约、候选晋级的任务需要 review；影响生产信号、组合权重、客户材料或不可逆数据的任务需要 approve；删除、迁移、发布和交易相关动作需要显式确认及外部控制。

## 三、最值得保留的设计

### 1. 量化研究的轻量—正式升级路径

`skill-map.md`、`quant-research-coding` 和 `quant-develop` 对 Level 1/2/3/4 的区分是全库最成熟的设计。它避免把一次性取数强行做成完整项目，也避免把进入投资流程的结果当成普通脚本。应保留，但要把升级条件做成机器可检查的字段：

```yaml
risk_level: 1|2|3|4
output_use: research_only|internal_decision|portfolio_input|external_or_live
recurrence: one_off|repeatable|scheduled
consumer: analyst|team|workflow|portfolio|client
promotion_trigger: []
```

### 2. 基金研究的事实层—研究层分离

`fund-wiki-research` 的“事实层、研究层、正式池/观察池/边界池”设计很适合投资经理使用。尤其是“研究报告不能直接改写 `product_profiles` 或 `manager_profiles`”这一红线，应上升为全库治理规则。

下一步应统一为：

- `fact`：有来源、可定位、可复核的事实；
- `manager_claim`：管理人或电话访谈口径；
- `inference`：模型或研究员基于事实做出的推断；
- `judgment`：投研结论；
- `action`：进入候选池、观察、淘汰、复核或配置建议。

### 3. 宏观技能的冻结快照和成熟度复盘

`macro-strategy-learning` 已经具备投资流程真正需要的三点：固定信息截止、概率而不是单点预测、事后复盘时保留原始判断。建议将这三点抽成全库的 `forecast_contract`，供策略、资产配置和风险监控共同使用。

### 4. 尽调纪要的证据分层和 review gate

`private-fund-dd-note` 对“未检索到处罚”与“确认无处罚”的区分是高价值规则；默认草稿、`human_review_required: true` 也适合保留。它比很多通用报告技能更接近真实投资工作。

### 5. `project-retrospective` 是经验复利的关键反馈环

`project-retrospective` 的定位是把一次项目变成可复用知识，并明确要求同时产出项目复盘文档和共享 Skill 回写建议；它还把回写分为 `proposed / approved / applied`，把模板创建设为用户确认后的可选分支。这是当前体系中最直接连接“完成任务”和“改进未来能力”的组件，应保留为核心反馈环。

它已经具备四个重要优点：

1. **以过程而非最终文件为复盘对象。** 要求按时间线重建目标、用户修正、被否决路径、转折和最终收口，能捕捉隐含在交互中的真实决策变化。
2. **尝试区分稳定模式与一次性细节。** 要求把项目名称、页面、按钮和路径改写为一般化的行为规则，避免直接把项目细节污染公共 Skill。
3. **把 Skill 回写与实际修改分离。** 复盘阶段只提出变更建议，只有明确授权后才应用，降低一次偶然经历改变整个工作系统的风险。
4. **对模板化保持克制。** 只有当目录结构、配置中心、入口和输出模式稳定，且用户确认后才创建模板，这与 `docs/templates` 当前的设计原则一致。

但它目前仍主要是一个高质量的“项目复盘与回写提案器”，还不是完整的“经验学习与知识治理系统”。它缺少任务级快速复盘、跨项目规律复盘、结果影响评估、规则晋级与淘汰、回写后的回归验证，以及对运行证据和投资结果证据的结构化要求。若不补齐这些环节，系统容易变成“项目结束后写一篇总结，并不断增加 Skill 内容”，却不能证明新增规则真正提高了效率、质量或投资决策。

## 四、需要优先修复的高风险问题

### A. 路由和命名问题

1. **技能名不符合统一规范。** `FOF_Risk_Report_Generator` 和 `PE_ODD_Auditor` 含大写和下划线；实际目录使用的是 `fof-risk-report-generator` 和 `PE_ODD_Auditor`，而 `skill-map.md` 还把显示名直接当成目录名使用。应统一为小写连字符目录，并提供旧名别名映射。
2. **描述字段不稳定。** `PE_ODD_Auditor` 描述是角色宣言，不是触发条件；`brainstorming`、`verification-before-completion`、`research-report-writer` 等描述混入了大量流程或能力。应遵守“描述只说明何时使用”的规则，并统一中英文触发关键词。
3. **入口技能重复。** `ai-quant-development-router` 与 `investment-paper-replication` 都可以承担项目编排；`frontend-page-router` 与 `frontend-design` 都可能先触发；`brainstorming`、`writing-plans`、`executing-plans` 的前后关系也主要存在于自然语言。需要一张有优先级的路由表，而不是并列目录。

### B. 引用路径和资源治理问题

当前体系中明确存在以下资源解析风险。需要注意，`F:\Thomas\QuantSystem\docs\templates` 实际存在；问题是 SharedSKILLS 单独使用时没有仓库依赖解析协议：

- `ai-quant-development-router`、`frontend-*`、`quant-research-coding` 多处要求读取 `docs/templates/indicator-monitor/` 或 `docs/templates/frontend-interaction/`，这些目录位于 QuantSystem，而不是 SharedSKILLS 技能根目录。
- `ai-quant-development-router` 引用的 `references/data-lifecycle.md`、`references/output-contracts.md`、`references/validation.md` 不在该技能目录，而是在 `quant-develop/references/`。
- `fund-wiki` 的 `build_product_profiles.py`、`build_profile_index.py`、`ingest_raw_docs.py` 真实存在于 `fund-wiki/engine/scripts/`。技能中的包装脚本会把工作目录解析到 engine 后再调用它们，所以完整的 deposit 路径可以工作；但 `fund-wiki-research` 直接要求执行 `scripts\build_research_index.py`，SharedSKILLS 中没有该脚本，只有 QuantSystem 的额外嵌套副本提供了同名脚本，且入口没有声明这种项目覆盖。弱模型直接按技能根目录执行时会失败。
- `fund-wiki-research` 引用的 `build_research_index.py` 在当前 SharedSKILLS 中找不到，应改为显式依赖、补齐包装脚本，或删除该步骤；不能让模型通过猜路径解决。
- `docx` 和 `pptx` 的打包、解包、校验脚本真实位于各自技能目录的 `ooxml/scripts/`；技能命令默认以技能/项目根目录为工作目录，若宿主 LLM 在其他目录执行且不先解析 skill root，会出现路径错误。`pptx/scripts/thumbnail.py` 等辅助脚本则位于另一层目录，需在 manifest 中区分。
- `project-retrospective` 引用了 `docs/retrospectives/` 和 `docs/templates/<template-id>/`，这是目标项目路径，不是当前 skill 自带资源，应明确标记为 repository dependency 或 target path。

改进方式：每个技能必须有一个可机器检查的 `manifest.yaml`：

```yaml
skill_id: quant-develop
version: 0.4.0
entry: SKILL.md
references:
  - path: references/validation.md
    required_for: [signal, backtest, risk]
commands:
  - id: smoke
    command: python -m pytest
    required: false
external_paths:
  - path: F:/Thomas/QuantSystem/docs/templates/indicator-monitor
    reason: repository dependency
```

安装或提交前运行 `skill doctor`，检查所有必需引用、脚本和外部依赖。找不到资源时，技能必须停止并说明缺失，不允许让模型自行补路径。

### C. 高风险规则矛盾

`PE_ODD_Auditor` 必须立即修订。当前文字同时表达：

- 无证据时默认满足；
- 无证据时推定违背；
- “推定违背”是反转版，但又只在明确反向证据或冲突时判否。

这不是措辞问题，而是评分函数不确定。建议改成显式三态：

```yaml
status: pass|fail|insufficient_evidence|conflict
scoring:
  pass: 0
  fail: deduction_or_fail
  insufficient_evidence: no_score + required_evidence
```

一票否决项如果材料不足，默认应为 `insufficient_evidence`，不能在正式 ODD 中既当通过又当失败。只有用户明确选择“保守风控模式”时，才把 `insufficient_evidence` 映射为暂不通过；这也必须记录为模式参数。

同一类问题也出现在 `quant-report-qa-interpreter` 的入池和风险等级规则：入池要求“得分 >65”，但一级风险写成“得分 ≥65”；三级和四级对“得分不足或净值长度不足”的条件重叠，五级又按纯回测/模拟盘单独判断。应先定义优先级和互斥区间，例如 `score >65` 才能通过入池，`score ==65` 只能是边界待复核；风险等级使用从高风险到低风险的短路顺序，并把“净值长度不足”“数据缺失”“纯回测”作为独立原因字段，不把它们压成一个数字。

此外，ODD 规则把“产品名称没有出现回测/拟合/拼接字样”作为披露合规的补充通过依据，这只能证明名称没有标记风险，不能证明净值来自托管或监管认可的第三方。应改为 `evidence_missing`，要求托管流水、产品备案或第三方净值来源；材料名称最多作为线索，不能替代来源验证。

### D. 过度依赖“必须”而没有执行对象

大量技能要求“必须验证”“必须记录”“必须等待确认”，但没有规定验证对象的最小结构。对较弱模型，应统一要求每轮返回：

```yaml
decision:
  mode: research|candidate|production|monitor_only|audit
  status: pass|fail|blocked|needs_review
  evidence:
    - id:
      source:
      location:
      observed:
      supports:
  assumptions: []
  unresolved: []
  artifacts: []
  commands: []
  human_gate: none|review|approve|confirm_scope
```

这样，“我检查过了”变成可检查的对象，而不是一句自我声明。

### E. 研究结论到投资结果之间仍有断层

当前体系有不少研究质量要求，但没有把“研究结果可用”定义成一组可审计的投资门槛。建议把以下链条固定为一个不可跳过的对象：

```text
信号/判断
→ 预期收益或概率
→ 风险模型与相关性
→ 组合约束和风险预算
→ 目标权重
→ 交易成本、滑点和容量
→ 实际成交与实际权重
→ PnL、暴露、归因和偏差
→ 继续、降级、暂停或退役
```

在没有目标权重、实际权重、交易记录和成本数据时，技能只能输出研究结论，不能声称已经完成组合评估。组合页面、投后报告或网页展示也不能用信号排名代替组合决策。

量化项目至少需要一个研究预注册文件，字段包括：研究问题、经济机制、预期方向、投资标的集合、样本起止日、标签定义、信号可用时点、换仓频率、基准、交易成本和滑点场景、容量假设、约束、主评价指标、稳健性检验、停止条件和多重检验预算。探索阶段可以允许字段为空，但必须标记 `research_only: true`，不得自动进入候选池。

回测验收还应明确检查：训练/验证/测试切分、walk-forward、purge/embargo、生存者偏差、退市和公司行为、截面与时间对齐、缺失和流动性处理、参数稳定性、不同成本场景、容量曲线、拥挤与状态依赖。若只验证代码执行成功或只报告单一 Sharpe，状态只能是 `research_passed`，不能是 `portfolio_ready`。

### F. 模型生命周期和责任人需要显式化

建议把项目阶段和模型角色分开，使用以下最小状态机：

| 模型状态 | 允许的用途 | 晋级所需证据 | 退回或停止条件 |
|---|---|---|---|
| `research` | 研究讨论、假设比较 | 数据口径、预注册、可复跑结果 | 关键数据或机制无法解释 |
| `candidate` | 小规模纸面组合、候选池 | 样本外、成本容量、风险暴露、复核记录 | 稳健性不足或依赖单一时期 |
| `challenger` | 与当前模型并行比较 | 同口径实时或准实时记录 | 预测、成本或风险显著劣化 |
| `champion` | 进入正式组合决策 | 投委会/责任人批准，运行和回滚方案 | 达到 kill condition 或长期失效 |
| `retired` | 归档与复盘 | 退役原因、最后版本、收益和风险归因 | 不得无记录重新启用 |

每个生产或候选模型都应有 `model_card`，至少记录 owner、reviewer、版本、数据快照、决策用途、风险预算、人工覆盖、监控指标、复核周期和 `kill_conditions`。模型没有责任人和停止条件时，LLM 只能协助整理材料，不能替团队作出继续运行的判断。

### G. 经验沉淀流程需要从“项目复盘”扩展为三级反馈系统

你的长期设想是“AI 辅助完成任务 → 沉淀经验 → 改进 Skill → 下次复用 → 再次复盘”。这个循环是正确的，但不能让所有任务都进入同一种完整复盘。建议把 `project-retrospective` 扩展为三级模式：

| 模式 | 触发时机 | 最小产物 | 主要目的 |
|---|---|---|---|
| `micro-retro` | 一次研究运行、一次失败、一次报告返工或一个明显的用户纠正之后 | 事实、原因、动作、是否值得记录，5–10 分钟完成 | 快速捕捉高价值错误，避免小问题被遗忘 |
| `project-retro` | 项目完成、暂停、重大偏航或进入候选/生产阶段 | 完整时间线、决策演化、排障链、复用规则和回写提案 | 总结项目级工作法和稳定骨架 |
| `meta-retro` | 多个同类项目或季度周期结束后 | 规则使用次数、失败率、节省时间、冲突规则、应废弃项 | 判断哪些经验真正有效，哪些规则应修改或删除 |

如果所有任务都做完整项目复盘，成本会使复盘被跳过；如果只有项目复盘，又无法及时捕捉单次错误，也无法识别跨项目才显现的规律。

#### 经验复盘必须区分三类证据

`project-retrospective` 当前强调以对话上下文为主要证据，这适合回答“用户的目标和偏好如何变化”，但不能单独证明量化项目已经完成或策略有效。建议明确证据分工：

| 要回答的问题 | 首要证据 |
|---|---|
| 用户当时想解决什么、为何改变范围 | 用户明确确认、拒绝和反复反馈 |
| 代码、数据和报告是否按要求完成 | 命令、退出码、测试、运行日志、文件和 schema 检查 |
| 研究结论是否在正确样本和成本下成立 | PIT、覆盖、样本外、稳健性、成本容量和复现证据 |
| 结论是否改变了投资行为 | 判断快照、目标权重、实际权重、交易记录、人工覆盖和投委会决议 |
| 判断后来是否有效 | 实现收益、风险暴露、成本、归因、基准比较和预测校准 |

复盘文档应分别标注 `conversation_evidence`、`run_evidence`、`research_evidence`、`decision_evidence` 和 `outcome_evidence`。对话可以证明意图，运行证据可以证明执行，投资结果证据才可以支持“这条经验提高了决策质量”的判断。

#### 经验应先评估影响，再决定写入哪里

复盘不应默认把经验写入 Skill。建议在复盘中加入以下影响字段：

```yaml
efficiency:
  before_estimated_minutes:
  after_estimated_minutes:
  rework_reduced: []
quality:
  errors_prevented: []
  errors_remaining: []
decision_impact:
  changed_research_conclusion: false
  changed_portfolio_action: false
  evidence: []
outcome:
  realized_result:
  attribution: []
  calibration_review:
```

经验应按性质分流，而不是全部进入 Skill：

| 经验类型 | 推荐去向 |
|---|---|
| 一次性事实、决定和项目背景 | 项目复盘文档 |
| 稳定的触发、顺序、停止条件 | Skill |
| 稳定的输入输出结构 | 模板、schema 或 `research_artifact` |
| 必须确定性执行的检查 | 脚本、验证器或 `skill_doctor` |
| 投资原则、风险门槛和审批要求 | rules / policy |
| 某个模型的假设、参数、责任人和退役条件 | `model_card` / registry |
| 只对当前项目成立的路径、字段和一次性取舍 | 留在项目内部 |

#### Skill 晋级必须有候选状态和反向淘汰

建议增加经验状态：

```yaml
status: observed|proposed|trial|approved|applied|deprecated|reverted
evidence_count: 0
source_retros:
  - project_id:
    location:
validation_cases: []
conflicts: []
owner:
review_after:
supersedes:
```

一个经验至少在两个独立任务中重复出现，或修复过一次重大错误，或显著减少返工，才进入 `proposed`。进入 `approved` 前还必须满足：能够写成“触发条件 → 动作 → 停止条件”，有一个正例和一个反例，已检查与现有规则的冲突，并且不依赖具体路径、项目名称或临时数据源。

成熟的反馈环不能只有“增加规则”，还必须允许 `deprecated` 和 `reverted`。如果规则使用后没有减少错误、反而增加追问或误路由，应保留证据并回滚。否则知识库会持续增肥，却不会真正进化。

## 五、面向较弱 LLM 的核心改造

以后模型能力下降时，最容易丢失的不是某个 API 参数，而是顺序、边界和否定条件。因此每个领域技能都应采用“短入口 + 小状态机 + 模板化产物”的结构。

### 1. 每个技能只保留三段核心正文

`SKILL.md` 第一屏只放：

1. **触发/不触发**：最多 6 条；
2. **先做什么**：最多 5 步；
3. **不能越过的门槛**：最多 5 条。

长解释、API 字段、背景知识全部移到 references。弱模型先读到的内容必须足以避免最严重的错误。

### 2. 把否定规则改成“错误—动作”对

不要只写“不要用最新快照”。改成：

| 发现 | 立即动作 |
|---|---|
| 目标日期没有历史状态 | 停止正式回测，标记 `historical_state_unavailable` |
| 只有最新快照 | 可做现状描述，不得做历史判断 |
| 输入覆盖不足 | 核心结果返回 `blocked`，不得用 0 补齐 |
| 研究报告与事实层冲突 | 分开列示，进入复核队列 |
| 证据不足以评分 | 输出 `insufficient_evidence`，不猜测 |

### 3. 为每个技能提供一个最小正例和一个压力反例

现有 `evals` 只覆盖少数技能。应为所有投资主链路至少建立：

- 触发测试：应该使用哪个主技能；
- 越界测试：应该拒绝哪个相邻技能；
- 压力测试：时间紧、用户强推结论、材料冲突、缺数据；
- 产物测试：是否生成正确文件/状态/证据字段。

测试不需要依赖更强的子代理，可以先用固定 prompt + 人工评分表；关键是把“错误路由”和“漏掉硬门槛”记录下来。

### 4. 统一“事实—判断—动作”输出格式

投资工作中最危险的错误是把推断写成事实、把研究观点写成配置建议。建议所有投资领域技能共享以下输出顺序：

```text
事实（来源和时间）
→ 口径/限制
→ 推断（为什么）
→ 反例/证伪条件
→ 判断（当前置信度）
→ 动作或下一步核验
```

报告、网页和 Excel 都必须保留这些层，不能因为换了交付格式而丢失。

### 5. 用“停止条件”代替无限追问

较弱模型容易一边缺资料一边继续写。每个技能要给出明确停止条件：缺少哪些字段时 `blocked`，哪些字段可以降级为 `draft`，哪些字段可以用代理但必须加 caveat。不要让模型自行决定是否“信息大概够了”。

### 6. 给流程设置复杂度预算

风险分级应同时限制所需步骤和输出长度。Level 1 的一次性取数只需要数据状态、口径、结果和一个限制说明；Level 2 的可复跑研究增加配置、日志和基础稳健性；Level 3 的组合输入增加预注册、样本外、成本容量和 review；Level 4 的生产或交易相关工作必须由外部系统、权限和人工审批控制。所有任务都套用完整项目模板，会使团队绕开规范；完全不分级，又会使高风险结果混入日常分析。

### 7. `project-retrospective` 的建议执行顺序

为让较弱 LLM 也能稳定执行，复盘入口不应直接要求写长文，而应按以下顺序生成结构化中间结果：

```text
判断复盘粒度
→ 收集对话、运行、研究、决策和结果证据
→ 建立时间线与决策变化
→ 分离事实、推断、经验和意见
→ 评估效率、质量、风险和决策影响
→ 将经验分流到文档、Skill、模板、脚本、规则或 model card
→ 生成回写提案和正反评估用例
→ 人工批准后应用
→ 运行路由/行为回归
→ 在后续任务中复核、保留、修订、废弃或回滚
```

每一轮复盘至少应返回：`retro_level`、`project_id`、`evidence_manifest`、`timeline`、`decisions_changed`、`lessons`、`writeback_proposals`、`non_reusable_details`、`template_worthy`、`validation_cases` 和 `next_review_date`。其中 `writeback_proposals` 只能是提案，不得因为复盘完成就自动修改共享 Skill。

建议把“模板是否值得创建”与“Skill 是否值得修改”分开判断。一个流程可能已经值得写入 Skill，但目录结构还不稳定，不应创建模板；一个项目可以有很好的模板骨架，但其中的投资逻辑仍应留在项目中。

## 六、按投资经理日常主链路的具体建议

### 1. 数据取得：`zmdata-data-api` + `public-data-collector`

保留“内部数据优先，公开数据作为缺口补充”的顺序。新增统一的数据可用性判定：

```yaml
data_status: exact|proxy|latest_only|missing|unverified
historical_state: supported|unsupported|unknown
coverage: {start:, end:, entities:, missing_rate:}
```

任何进入回测、评分、组合或 ODD 的数据，都必须带 `data_status`。`latest_only` 只能支持当前描述，不能支持历史评估。

### 2. 量化研究：`quant-research-coding` → `quant-develop`

现在的升级思想正确，但升级触发条件应从散文变成四个问题：

1. 是否重复运行？
2. 是否被别人或工作流消费？
3. 是否会影响配置、组合、客户或投委会材料？
4. 是否需要历史可追溯、失败告警或权限控制？

任一回答“是”，至少进入候选升级评估。输出应默认带 `research_only: true/false`，防止研究结果被误当成生产信号。

### 3. 基金研究：`wisdom` → `fund-wiki` → `fund-wiki-research`

这是最适合固化为“流水线”的一组技能。建议增加一个统一的 `manager/product identity card`，在所有步骤中传递：

```yaml
manager_id:
product_id:
name_as_requested:
resolved_name:
resolution_confidence:
source_snapshot_time:
```

这样可以减少“同名管理人、短名产品、历史产品和当前产品”混淆。研究输出还应强制携带 universe artifact，而不是只在正文里写样本数量。

### 4. 尽调：`private-fund-dd-note` → `PE_ODD_Auditor`

两者边界已经存在：先整理纪要，再正式评分。需要增加一个中间状态：`dd_note_status: draft|source_checked|ready_for_odd`。只有 `ready_for_odd` 才能进入 ODD 评分。否则弱模型可能把一份尚未完成公开核验的纪要直接拿来打分。

ODD 输出建议强制三列：`判定`、`证据强度`、`待补材料`，并禁止用“无异常”覆盖“未核验”。

### 5. 宏观和策略判断：`macro-strategy-learning`

保留三情景、概率和证伪条件。新增两个投资经理真正需要的字段：

- `decision_horizon`: 1 周、4–6 周、3 个月或更长；
- `position_relevance`: 研究观察、组合倾向、实际交易或风险对冲。

这样可以避免一份宏观判断在不同时间尺度被误用。黄金、中国风格、海外权益等专题也应全部套用同一套 snapshot schema。

### 6. 报告和网页：先内容契约，再交付技能

`research-report-writer`、`frontend-report-page`、`docx`、`pptx`、`xlsx` 不应重新解释投资逻辑，只负责把已冻结的研究对象表达出来。建议所有交付技能读取同一个 `research_artifact.yaml`：

```yaml
title:
audience:
decision_use:
as_of:
thesis:
facts: []
judgments: []
risks: []
falsifiers: []
source_manifest: []
review_status: draft|reviewed|approved
```

这会显著降低“报告写得漂亮但把判断层改了”的风险。

### 7. 指标监控模板：从“可刷新”增加到“可决策”

`indicator-monitor` 已有配置中心、`raw / normalized / derived` 分层、诊断状态和研究到监控的演进路径，这是合理骨架。建议在 `project.yaml` 或主配置中增加：

```yaml
decision_use: research_only|monitoring|portfolio_input
economic_mechanism: ""
falsifiers: []
promotion_gate: []
monitoring_owner: ""
review_frequency: weekly|monthly|quarterly
kill_conditions: []
postmortem_path: ""
```

每次运行的快照除了抓取和验证状态，还应保存“本次变化是否改变判断、组合或风险预算”。否则项目会变成数据刷新器，无法证明监控结果改变了投资行为。

`frontend-interaction` 模板适合继续约束表格、筛选、图表和工作台交互，但不应扩展成投资方法论。页面必须显示 `as_of`、数据状态、研究/候选/生产用途、证据链接和最后复核时间；视觉规范不应代替风险提示或决策门槛。

## 七、建议的重构优先级

### P0：先修复会造成错误结论的内容

1. 修订 `PE_ODD_Auditor` 的三态证据和默认规则。
2. 修订 `quant-report-qa-interpreter` 的得分边界和风险等级互斥规则，并把 ODD 的“名称无风险字样”降级为线索。
3. 统一 `FOF_Risk_Report_Generator`、`PE_ODD_Auditor` 命名和目录映射。
4. 盘点并修复所有 references/scripts 路径；清理嵌套的重复 skill 目录、缓存和运行产物；没有资源就删除引用或明确外部依赖。
5. 为 `skill-map.md` 增加唯一主入口、优先级、停止条件和技能别名。
6. 给投资领域技能增加统一的事实—推断—判断—动作输出协议。

### P1：让较弱模型也能稳定执行

1. 每个主技能压缩成“触发—五步—五条红线—输出模板”四块。
2. 增加 `manifest.yaml` 和 `skill doctor`。
3. 为 `zmdata`、基金研究、量化研究、尽调、宏观五条主链路补齐最小 evals。
4. 把状态拆成正交字段，而不是一个混合枚举：`work_stage`（idea/research/candidate/production/retired）、`model_role`（research/candidate/challenger/champion/rejected）、`run_status`（queued/running/succeeded/failed/blocked）、`review_status`（draft/reviewed/approved）和 `decision_use`（research_only/portfolio_input/live）。
5. 所有完成性声明必须引用结构化验证证据，不接受“看起来正常”。

### P2：提升长期维护效率

1. 为所有技能增加版本、变更原因、兼容范围和废弃策略。
2. 建立技能依赖图，避免同一规则复制到多个技能后发生漂移。
3. 将重复的时间语义、证据等级、review gate、输出契约抽成共享 references。
4. 把 `project-retrospective` 扩展为 `micro-retro / project-retro / meta-retro` 三级反馈流程，并区分 `proposed`、`trial`、`approved`、`applied`、`deprecated`、`reverted`。
5. 每季度以真实任务样本做一次路由、经验晋级和压力回归，而不是只做文本审阅。

### 首轮 30 天落地顺序

不要一开始同时重写 56 个技能。先用五条主线建立可验证的最小治理闭环：

| 时间 | 交付 | 验收重点 |
|---|---|---|
| 第 1 周 | `skill-registry.yaml`、唯一主入口、状态字典、证据对象和路径解析规则 | 同一请求只选择一个主 skill；缺资源时返回 `blocked` |
| 第 2 周 | 修订 ODD 三态判定和定量报告分数边界；清理或隔离缓存与历史产物；建立 SharedSKILLS → QuantSystem 的锁定快照 | ODD 和入池判断不再因材料缺失或边界值产生相反结论；副本能追溯源版本 |
| 第 3 周 | 为量化研究和指标监控加入预注册、成本容量、`model_card`、`research_only` 和晋级门；为 `project-retrospective` 增加 `micro-retro` 输出 | 回测通过不能直接生成 `portfolio_ready`；监控快照能说明是否改变决策；单次错误能进入候选经验库 |
| 第 4 周 | 用真实任务做 30 个压力用例：五条主线各 5 个，加上 5 个复盘晋级/淘汰用例 | 记录误路由、漏门槛、伪验证、产物缺字段和错误回写，形成下一轮修订清单 |

30 天后的扩展顺序应是：先补齐组合目标权重与实际成交归因，再扩展到更多领域 skill，最后才做前端和文档模板的统一包装。这样改造直接连接投资结果，而不是先增加管理文件数量。

## 八、建议立即建立的最小治理文件

建议在仓库根目录增加：

```text
skill-map.md                 # 人类可读路由
skill-registry.yaml          # 机器可读注册表
shared-contracts/
  evidence.yaml              # 事实/推断/判断/动作
  lifecycle.yaml             # draft/reviewed/approved/production 等
  data-freshness.yaml        # exact/proxy/latest_only/missing
  artifact.yaml              # 报告、网页、表格共用
tests/
  routing-cases.yaml         # 路由正例/反例
  pressure-cases.yaml        # 压力场景
  retro-cases.yaml           # 经验晋级、回滚或留在项目内的判断
scripts/
  skill_doctor.py            # 路径、frontmatter、依赖检查
  run_skill_evals.py         # 固定 prompt 回归
```

`skill-registry.yaml` 的最小字段：

```yaml
- id: quant-research-coding
  layer: domain
  priority: 30
  triggers: [quick backtest, factor check, one-off data pull]
  excludes: [production signal, recurring workflow]
  escalates_to: quant-develop
  required_contracts: [evidence, data_freshness]
  outputs: [research_artifact]
  aliases: [轻量量化研究, 快速回测]
```

## 九、验收标准

改造完成后，不要以“所有 SKILL.md 都改过”为完成标准，而应满足以下行为标准：

- 对同一用户请求，主入口在重复运行中保持稳定；
- 较弱模型不会把一次性研究升级成完整平台，也不会把正式信号降级成临时脚本；
- 缺少 PIT、历史快照、关键身份或公开核验时，模型会停止、降级或明确标记，而不是猜测；
- 事实、管理人口径、推断、判断和动作可以逐条追溯；
- 研究、报告、网页和 Excel 的结论来自同一冻结 artifact；
- 任何“完成”“通过”“无异常”“可生产使用”的表述都能指向新鲜命令、样本、覆盖和输出证据；
- 资源路径、脚本路径和外部项目依赖可以由 `skill doctor` 自动发现；
- 在压力场景下，用户要求“直接给结论”“先凑一个”“不用复核”时，模型仍保留关键门槛。
- 每次复盘都能明确经验去向；候选规则有来源、正反用例、负责人和复核日期；无效规则可以被废弃或回滚。
- `micro-retro` 不会把一次性细节直接写入共享 Skill；`meta-retro` 能根据多个任务的真实数据判断规则是否产生了效率或质量收益。

## 十、最终建议

不要继续横向增加更多技能。下一阶段的高收益工作是把现有技能收敛成五条稳定主线：**数据取得、基金事实与研究、量化研究与升级、尽调与 ODD、宏观判断与复盘**，再用统一证据协议和交付协议连接报告、网页、表格和知识库。

如果只能做一轮改造，优先完成 P0，并为五条主线各做 5 个路由/压力用例。等这些用例证明较弱模型不会误路由、漏掉硬门槛或伪造验证后，再继续精简正文和补充模板。对于投资经理而言，少几个“看起来很专业”的技能并不重要；重要的是在数据不完整、时间紧、结论诱人、材料相互矛盾时，系统仍然知道什么时候可以判断，什么时候必须停下来。
