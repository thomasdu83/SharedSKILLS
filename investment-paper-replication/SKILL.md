---
name: investment-paper-replication
description: Use when converting investment, finance, economics, asset pricing, portfolio construction, quant, macro, risk, or trading source materials into reproducible research outputs, Markdown/HTML reports, professional investment-bank-style web visualizations, and optionally production-ready research systems. Source materials may include academic papers, broker or institutional research reports, internal strategy memos, algorithm documents, white papers, product research notes, or idea documents. Use when the user asks to replicate, implement, audit, or systematize a paper, report, strategy idea, algorithm spec, research memo, or investment document.
---

# Investment Research Source Replication

Use this skill to turn an investment-related source document into a disciplined research, visualization, and implementation workflow. A source document can be an academic paper, sell-side or buy-side research report, internal strategy memo, algorithm document, white paper, product note, or raw investment idea. The default posture is: understand the source, define a reproducible spec, preview the final deliverable, validate investment usefulness, prototype the presentation layer when needed, then implement only after the user confirms the delivery direction.

## Operating Principles

- Start with research judgment before code. Do not jump directly into production architecture.
- Separate three lenses: source claim, replication/adaptation result, and investment implication.
- Treat data availability and definition drift as first-class risks.
- For non-trivial work, pass through a Delivery Preview Gate before project implementation.
- If the delivery is a report, show the report structure, chart/table plan, and intended analytical conclusions before drafting the full artifact.
- If the delivery is a frontend, build and iterate a web visualization prototype before deeper code landing.
- For finance, investment research, quant, portfolio, risk, allocation, or fund-analysis frontends, default to the international investment-bank research style defined in `references/frontend_style_guide.md`, using `jpmorgan.com` as the default visual reference unless the user specifies another house style. Avoid SaaS/tech-product aesthetics and editorial landing-page composition.
- Keep outputs auditable: list assumptions, substitutions, unverifiable claims, and replication gaps.

## Coordination With Related Skills

This skill acts as the project orchestrator when the task starts from an investment research source and may lead to reports, visual prototypes, or systems. Use related skills as specialist layers:

- Use `quant-research` when the work requires FOHF/fund research, Obsidian note verification, entity mapping, or qualitative notes cross-checked against quantitative facts.
- Use `quant-develop` when confirmed work moves into production code, data pipelines, backtests, portfolio construction modules, logging, config-driven architecture, or maintainable system engineering.
- Use `research-report-writer` when drafting, restructuring, or polishing the final research report prose, especially when the report needs a clearer thesis, tighter analytical flow, restrained professional language, or better section rhythm.

Do not let specialist skills bypass this skill's Delivery Preview Gate for non-trivial user-facing work. The preferred sequence is: source replication orchestrator first, specialist verification or writing/development second, acceptance testing last.

## Delivery Modes

Choose the smallest useful delivery mode unless the user asks for a broader package.

- **Mode A: Research note** - `replication_report.md`
- **Mode B: HTML report** - `replication_report.html`
- **Mode C: Web visualization prototype** - static or lightweight web app for user review
- **Mode D: System implementation** - code modules, tests, data pipeline, and repeatable runs after the prototype or report is accepted
- **Mode E: Existing project audit** - review an existing source-based project and produce a prioritized remediation plan

For details, read `references/deliverables.md` when deciding the output package.

## Standard Workflow

1. **Task classification**
   - Determine whether this is new project creation, existing project audit, report production, frontend prototype, or system implementation.
   - For existing projects, read `references/project_audit_checklist.md` and audit before making changes unless the user explicitly asks for immediate fixes.

2. **Source intake**
   - Identify source type: academic paper, research report, strategy memo, algorithm document, white paper, product note, or idea document.
   - Identify research type: factor, asset pricing, macro allocation, portfolio construction, risk, machine learning, execution, or qualitative framework.
   - Extract research question, investment hypothesis, model, required data, sample period, frequency, variables, portfolio construction rules, transaction cost assumptions, and headline findings.
   - Flag missing details that affect reproducibility.

3. **Replication spec**
   - Create `replication_spec.md` before implementation when the task is non-trivial.
   - Include target tables/figures, formulas, data requirements, field mappings, assumptions, and validation thresholds.
   - Use `references/replication_checklist.md` for technical checks.

4. **Data feasibility mapping**
   - Map each source variable to available local data, possible substitutes, and residual risk.
   - Distinguish exact replication, approximate replication, and conceptual adaptation.

5. **Delivery Preview Gate**
   - Before project implementation, produce a preview that matches the delivery type.
   - Report preview: report outline, chart/table plan, expected findings, and review questions.
   - Frontend preview: information architecture, first-screen layout, component list, interaction plan, sample data schema, and static prototype when useful.
   - System preview: module plan, data contracts, run commands, acceptance tests, and known risks.
   - Read `references/delivery_preview_gate.md` for required preview artifacts.
   - Ask the user to confirm or revise the preview before implementation when the requested work is large, ambiguous, or user-facing.

6. **Minimal replication**
   - Build the smallest runnable analysis that tests the core idea.
   - Prefer clear scripts or notebooks over premature framework code.
   - Produce core tables, figures, and diagnostics before writing a polished report.

7. **Research report**
   - Write a Markdown report first when the user needs analytical judgment.
   - Use conclusion-led headings and distinguish evidence from interpretation.
   - Read `references/report_structure.md` for the standard structure.
   - When prose quality, narrative flow, or thesis clarity is central, apply `research-report-writer` standards after the evidence structure is fixed.

8. **HTML report or web prototype**
   - Use HTML for polished reading and web prototype for interactive review.
   - If a web prototype is requested, use sample or exported results first. Confirm layout, narrative, colors, chart hierarchy, and interactions before connecting full production logic.
   - Read `references/frontend_style_guide.md` before creating any frontend.
   - Read `references/frontend_interaction_checklist.md` and `references/frontend_data_contract.md` before implementing interactive screens.
   - Reuse `assets/frontend-template/` when a lightweight prototype is appropriate.

9. **Investment validation**
   - Evaluate whether the result is a tradeable signal, explanatory lens, risk monitor, allocation input, or research-only insight.
   - Read `references/investment_validation.md` for the validation frame.

10. **Code landing**
   - Implement production code only after research logic and presentation direction are accepted, unless the user explicitly asks for direct implementation.
   - Create modular files for data loading, feature construction, model logic, backtest/evaluation, chart data export, and report generation.
   - Add tests around date alignment, lagging, portfolio formation, and output schema when risk warrants it.
   - Use `references/acceptance_testing.md` to define and run verification, especially for frontend interactions.
   - When the project is a formal quant system, follow `quant-develop` engineering rules for configuration, logging, typing, data architecture, and maintainability.

## Recommended Project Layout

```text
research_source_project/
  source_documents/
    paper_or_report.pdf
    strategy_memo.md
  notes/
    source_summary.md
    replication_spec.md
    delivery_preview.md
    assumptions.md
  reports/
    replication_report.md
    replication_report.html
  web_prototype/
    index.html
    styles.css
    app.js
    sample_data.json
    frontend_data_contract.md
  src/
    data_loader.py
    features.py
    model.py
    backtest.py
    evaluation.py
    charts.py
  outputs/
    tables/
    figures/
    results.json
  config/
    parameters.yaml
  tests/
```

## Mandatory Review Points

Before final delivery, state:

- What was replicated exactly.
- What was approximated due to data or source ambiguity.
- Whether there are signs of look-ahead bias, survivorship bias, selection bias, or overfitting.
- Whether transaction costs, turnover, capacity, and sample decay were considered.
- Which outputs are ready for investment use and which are research-only.
- Whether the delivery preview was confirmed, skipped by user request, or still needs review.
- Which acceptance tests were run and which user-facing interactions remain manually unverified.
