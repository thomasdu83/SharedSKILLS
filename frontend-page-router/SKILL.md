---
name: frontend-page-router
description: Use when building a frontend page, dashboard, or HTML artifact and the agent must decide whether the primary task is internal operation or external reading and explanation.
---

# Frontend Page Router

Use this skill before creating structure for any finance, research, portfolio,
risk, or fund-related page.

## Decision Goal

Decide whether the page is:

- an internal operations platform
- an external report-oriented page
- unclear and requires a user question

Do not skip this step.

## Classification Questions

Answer these in order:

1. Who uses the page most often: internal operators or external readers?
2. What is the primary task: filter, edit, maintain, monitor, construct, or
   explain, conclude, review, persuade?
3. What does success look like: finishing actions faster or understanding
   conclusions faster?

If two or more answers point to the same mode, use that mode.

## Route To Operations Platform

Choose `frontend-ops-platform` when the page is mainly for:

- daily internal use
- maintenance and data updates
- filtering and triage
- editing and state changes
- monitoring and exception handling
- portfolio construction or workbench tasks

Typical keywords:

- `工作台`
- `管理平台`
- `维护`
- `筛选`
- `编辑`
- `组合构建`
- `监控`
- `内部使用`

## Route To Report Page

Choose `frontend-report-page` when the page is mainly for:

- reading and interpretation
- external distribution
- report delivery
- attribution review
- strategy explanation
- conclusions and evidence presentation

Typical keywords:

- `报告`
- `外发`
- `展示`
- `复盘`
- `解读`
- `观点`
- `结论`
- `HTML 报告`

## Ask The User When Unclear

If the prompt is ambiguous, ask a short routing question instead of mixing both
structures. Typical ambiguous cases:

- `做一个组合分析页面`
- `做一个投后归因页面`
- `做一个组合看板`
- `做一个分析首页`

Example clarification:

`这个页面主要给内部团队日常操作，还是给外部读者阅读结论？`

## Hard Rules

- Never start with visual style before page classification.
- Never merge report-page hero blocks into an internal workbench by default.
- Never turn a reader-facing report into a pure CRUD console.
- If a page contains both reading and operation areas, choose one primary mode
  and treat the other as a secondary module.

## Pressure Tests

Use these as self-checks:

- `做一个基金池维护平台` -> operations platform
- `做一个宏观打分 HTML 报告` -> report page
- `做一个组合分析页面` -> ask the user
- `做一个投后归因页面，给客户看` -> report page
- `做一个投后归因页面，投研每天用` -> operations platform
- `做一个组合监控台账，投研团队每天用` -> operations platform
- `做一个基金复盘网页，准备外发` -> report page
