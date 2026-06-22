# Internal Circulation Report Template

Use this template when the user asks for `外发版`, `内部流通版`, `给其他投研团队看`, `可分发报告`, or `给同事看的版本`. In this skill, those phrases mean internal cross-team circulation unless the user explicitly says external client distribution.

## Positioning

An internal circulation version is derived from a fund-wiki research working paper. It is easier for other investment teams to read, but it is still an internal research artifact.

Keep:

- Core conclusion and strategy framework
- Investment research reasoning
- Important definitions, boundaries, and risks
- Short methodology disclosure in plain language
- Internal-use disclaimer

Remove or rewrite:

- Raw file paths, UNC paths, local paths, index filenames, command lines
- Verbose query diagnostics, hard-filter debugging, and implementation details
- Long sample-funnel mechanics
- Evidence tables whose only purpose is reproducibility
- Unreviewed manager/product names in the main text

## Frontmatter

```yaml
---
artifact_type: internal_circulation_report
profile_type: ResearchReport
research_type: internal_circulation
research_topic: <topic_id>
topic: <Chinese topic>
title: <Chinese title>_内部流通版
reader: internal_investment_teams
use_case: cross_team_research_sharing
status: draft
review_status: draft
conclusion_status: circulation_draft
as_of_date: YYYY-MM-DD
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
docs_root: <fund_profile_wiki_docs path>
derived_from:
  - research/reports/<working-paper>.md
  - research/universes/<universe-artifact>.md
fact_layer_sources:
  - summarized_from_working_paper
research_layer_sources:
  - research/reports
evidence_policy: working_paper_primary_circulation_derived
not_primary_evidence: true
distribution_scope: internal_research_teams_only
---
```

## Suggested Structure

```markdown
# <Title>

## 摘要结论

用 4-6 条回答读者最关心的问题。不要写内部检索过程。

## 1. 研究背景与问题

- 为什么需要这套分类或比较框架
- 本文回答什么问题
- 本文不做什么

## 2. 核心分类框架

| 类别 | 核心收益来源 | 对冲/风险控制方式 | 适合比较的维度 | 主要风险 |
|---|---|---|---|---|

## 3. 投研使用方式

说明其他投研团队如何使用该框架做初筛、访谈、可比池构建、组合解释或风险复核。

## 4. 关键边界与风险提示

写清楚哪些产品容易被误归类、哪些结论依赖材料质量、哪些市场环境会影响分类有效性。

## 5. 示例说明（可选）

默认使用匿名示例。只有用户明确要求且事实层证据等级 A/B、无待复核标签时，才在附录放具名示例。

## 6. 内部使用声明

本文为公司内部投研交流材料，仅供研究参考，不构成投资建议、产品推荐、业绩承诺或收益预测。具体产品判断应以正式尽调、合规审查和最新材料为准。

## 附录：来源说明

用自然语言说明“本文基于 fund-wiki 已沉淀的产品画像、管理人画像和既有研究底稿整理”。不要列内部路径、命令或索引文件名。
```

## Naming

Use:

```text
research/reports/<topic>_内部流通版_YYYYMMDD.md
```

Do not overwrite the working paper.

## Manager And Product Names

Default: do not name specific managers/products in the main text.

Allowed alternatives:

- Anonymous examples: `某量化管理人 500 中性产品线`
- Category examples: `典型股票 Alpha/Beta 对冲中性产品`
- Named appendix only when the user explicitly asks and evidence grade is A/B with no material review flags

When named examples are included, mark them as examples, not recommendations.
