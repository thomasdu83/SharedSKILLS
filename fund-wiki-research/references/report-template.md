# Research Report Template

Use this template for internal investment research readers. Keep the writing direct, evidence-led, and decision-useful.

## Frontmatter

```yaml
---
artifact_type: research_report
profile_type: ResearchReport
research_type: strategy_taxonomy
research_topic: <topic_id>
topic: <Chinese topic>
title: <Chinese title>
reader: internal_investment_research
use_case: strategy_comparability
status: draft
review_status: draft
conclusion_status: draft_research_classification
as_of_date: YYYY-MM-DD
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
docs_root: <fund_profile_wiki_docs path>
strategy_tags:
  - <strategy tag>
source_profile_paths:
  - indexes/product_profiles.jsonl
source_queries:
  - <query text>
fact_layer_sources:
  - product_profiles
  - manager_profiles
  - indexes
research_layer_sources:
  - research/reports
evidence_policy: fact_layer_primary_research_layer_derived
not_primary_evidence: true
---
```

`profile_type: ResearchReport` is required for the installed research indexer. Use `profile_type: Methodology` for methodology notes and `profile_type: InsightCard` for insight cards.

Use `status: reviewed` or `status: final` only when the user or human reviewer confirms it.

This template is for the internal research working paper. If the user asks for `外发版`, `内部流通版`, `给其他投研团队看`, `可分发报告`, or `给同事看的版本`, first preserve or create the working paper, then derive a separate internal circulation version with `references/internal-circulation-template.md`. Do not overwrite the working paper.

## Suggested Structure

```markdown
# <Title>

## 一页结论

用 5-8 条说明最重要的研究判断。第一条必须回答本课题的核心问题。

## 1. 研究口径

- 读者：
- 用途：
- 研究对象：
- 不做什么：
- 验收标准：

## 2. fund-wiki 覆盖与召回

- 管理人覆盖：
- 产品覆盖：
- 召回命令：
- intent_mode：
- recognized_product / recognized_manager：
- hard_filters：
- 召回结果：
- 截断或限制：
- 结构化索引聚合：如使用，说明字段、规则和候选数量

## 3. 样本漏斗

For full-universe, strategy taxonomy, or comparable-pool reports, also write a reusable universe artifact under `research/universes/` and cite its path here.

| 层级 | 数量 | 说明 |
|---|---:|---|
| 全库覆盖 |  |  |
| 查询命中 |  |  |
| 强候选 |  |  |
| 正式可比池 |  |  |
| 观察池 |  |  |
| 边界/排除 |  |  |

## 4. 策略细分

| 子类 | 定义 | 可比维度 | 典型证据 | 主要歧义 |
|---|---|---|---|---|

## 5. 正式可比池

| 管理人 | 代表产品 | 子类 | 证据等级 | 一句研究判断 |
|---|---|---|---|---|

## 6. 观察池与边界池

| 管理人 | 当前判断 | 未进入正式池原因 | 需要补证 |
|---|---|---|---|

## 7. 主要不确定性

说明材料缺口、标签冲突、策略漂移、命名歧义、样本覆盖限制。

## 8. 反哺 fund-wiki 的建议

只写建议，不直接改 profile 事实。

## 附录：证据路径

列出使用的 product profile、manager profile、source note、研究 artifact 路径。
```

## Writing Standards

- Put conclusions before process details.
- Use "事实层证据显示" for fact-layer statements.
- Use "历史研究层曾判断" for derived research conclusions.
- Use "待复核" when the fact layer and research layer diverge.
- Avoid vague labels such as "较好", "不错", "值得关注" unless the comparison basis is stated.
- Do not include investment action unless the user explicitly requests it.
- Do not use this working-paper structure directly as an internal circulation report; it intentionally contains reproducibility details that should be summarized or removed for other-team readers.
