---
name: frontend-page-router
description: Use when building a frontend page, dashboard, workbench, HTML report, score report, weekly report, portfolio page, fund platform, or finance artifact and the primary mode could be internal operation or reader-facing explanation.
---

# Frontend Page Router

Use this before creating structure for finance, research, portfolio, risk, fund,
score, industry, macro, weekly-report, or attribution pages.

## Decision Goal

Choose one primary mode:

- internal operations platform
- external or reader-facing report page
- unclear and requires one routing question

After classification, use the selected mode to build the preview HTML. Do not
let an early visual mockup decide the mode.

## Classification Questions

Answer in order:

1. Who uses it most: internal operators or readers?
2. What is the main verb: maintain, filter, edit, construct, monitor, triage;
   or explain, compare, conclude, review, distribute?
3. What proves success: actions completed faster, or conclusions understood
   faster?
4. For quant model work, is this historical backtest or model review, or
   finalized model tracking and daily use?
5. If it is monitoring, does the user only inspect state and changes, or must
   they edit, approve, publish, or maintain objects?

If two or more answers point to one mode, use it. If split evenly, ask the
user.

## Route To Operations Platform

Choose `frontend-ops-platform` when the page is mainly for:

- daily internal use
- fund pool maintenance, tag management, status updates
- filtering, triage, selection, editing, batch action
- portfolio construction, versioning, monitoring, attribution workbench
- finalized model tracking, run-state monitoring, publish gates, alert review
- read-only monitoring of finalized models or grouped indicators
- object details, drawers, inline fields, save/delete workflows

Typical keywords:

- `工作台`
- `管理平台`
- `维护`
- `筛选`
- `编辑`
- `构建组合`
- `组合监控`
- `模型跟踪`
- `指标监控`
- `只读监控`
- `发布门禁`
- `台账`
- `内部使用`

## Route To Report Page

Choose `frontend-report-page` when the page is mainly for:

- static or semi-static HTML delivery
- historical backtest review, model candidate review, finalized-model memo
- macro score, industry score, strategy score, fund weekly report
- reading, interpretation, evidence, methodology, conclusions
- external distribution, screenshot, print, archive, review
- charts and tables whose role is to support a thesis

Typical keywords:

- `报告`
- `周报`
- `月报`
- `外发`
- `展示`
- `复盘`
- `解读`
- `观点`
- `结论`
- `HTML 报告`
- `回测评审`
- `定型评审`

## Hybrid Rule

Hybrid pages still need one primary mode:

- A report with tabs, filters, sortable tables, or selectable details remains a
  report if the interaction helps reading.
- A workbench with KPI strips or preview reports remains an operations platform
  if users edit, save, monitor, or maintain objects.
- White or gray background is not a routing signal. The task decides the mode;
  the mode then decides the canvas.

## Ask When Unclear

Ask one short question:

`这个页面主要给内部团队日常操作，还是给读者阅读结论和证据？`

Typical ambiguous prompts:

- `做一个组合分析页面`
- `做一个投后归因页面`
- `做一个组合看板`
- `做一个分析首页`

## Hard Rules

- Never start with visual style before classification.
- Never put a report hero into an internal workbench by default.
- Never turn reader-facing research into a pure CRUD console.
- Never classify by domain alone. Classify by user task.
- Never classify by palette alone. A report can have a pale shell; a workbench
  can have white work surfaces.
- Never skip routing because a preview HTML already looks plausible.

## Pressure Tests

- `做一个基金池维护平台` -> operations platform
- `做一个公募投顾模拟组合管理平台` -> operations platform
- `做一个宏观打分 HTML 报告` -> report page
- `做一个行业评分外发页` -> report page
- `做一个私募基金业绩周报` -> report page
- `做一个历史回测 HTML 文档` -> report page
- `做一个模型定型评审页` -> report page
- `做一个回测结果对比页面，给投研评审` -> report page
- `做一个组合分析页面` -> ask the user
- `做一个投后归因页面，给客户看` -> report page
- `做一个投后归因页面，投研每天用` -> operations platform
- `做一个定型后模型跟踪工作台` -> operations platform
- `做一个组合模型每日监控页面` -> operations platform
- `做一个回测批次管理和重新运行平台` -> operations platform
- `做一个宏观指标只读监控页` -> operations platform, `read_only_monitor` variant
- `做一个定型模型跟踪页，只读展示建议权重和风险` -> operations platform, `read_only_monitor` variant
