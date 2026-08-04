# Shared Skill Map

这份库的目标不是“把所有技能都记住”，而是让 AI 先命中正确的主线，再少量下钻。

## 使用原则

1. 先判断任务属于哪一类，再加载 skill。
2. 同类冲突时，优先更具体的 domain skill。
3. 元技能只在维护 skill 库本身时使用。
4. 参考类 skill 只在需要时再读，避免预加载全文。

## 主线路由

| 任务意图 | 首选 skill | 常见后续 | 说明 |
|---|---|---|---|
| 私募管理人 / 产品事实查询 | `wisdom-manager-product-research` | `fund-wiki-research` | 先拿事实，再做判断 |
| ZM 数据接口 / 代码示例 / ID 映射 | `zmdata-data-api` | `quant-develop` | 作为底层数据能力 |
| 尽调材料入库、沉淀、查询 | `fund-wiki` | `fund-wiki-research` | 事实层与知识层分开 |
| 基于 fund-wiki 的专题研究 | `fund-wiki-research` | `research-report-writer` | 可比池、分类、研究稿 |
| fund-wiki + 当前数据层双源研究 | `fund-wiki-research` | `wisdom-manager-product-research` / `zmdata-data-api` | 适合策略/团队/绩效判断 |
| 量化系统开发、回测、组合工程 | `quant-develop` | `systematic-debugging` | 偏工程与契约 |
| MyNotes/Obsidian 知识沉淀、Inbox 处理、MOC、AI知识库管理 | `mynotes-knowledge-manager` | `pdf` / `docx` / `investment-paper-replication` / `quant-develop` | 先沉淀知识，再决定是否项目化或联动 QuantSystem |
| 高保障代码实现 / 证明它能跑 | `old-coder` | `test-driven-development` / `verification-before-completion` | SPEC → 测试关卡 → 证据报告 |
| 定量报告质检与解读 | `quant-report-qa-interpreter` | `research-report-writer` | 报告审查与再表达 |
| 投后归因报告 | `FOF_Risk_Report_Generator` | `fund-wiki-research` | 先归因，再写结论 |
| 策略标签 / 赛道审计 | `fund-track-tag-audit` | `fund-wiki` | 适合标签修正与证据核对 |
| ODD 审计 | `PE_ODD_Auditor` | `docx` / `pptx` / `pdf` | 风控与合规穿透 |
| 研究报告写作 | `research-report-writer` | `docx` / `pptx` / `xlsx` | 负责表达和结构 |
| 论文 / 策略复现 | `investment-paper-replication` | `quant-develop` / `research-report-writer` | 先复现，再落地 |

## 辅助分组

### 文档与交付

- `pdf`
- `docx`
- `pptx`
- `xlsx`
- `frontend-report-page`
- `frontend-ops-platform`

### 代码与流程

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
5. 再质检或交付：`quant-report-qa-interpreter`、`FOF_Risk_Report_Generator`、`docx`、`pptx`、`xlsx`

## 最小路由规则

- 事实优先于观点。
- 域技能优先于元技能。
- 具体技能优先于通用技能。
- 入口越短，触发越稳。
