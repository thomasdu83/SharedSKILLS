# Deliverables

Select the delivery mode based on the user's objective and the maturity of the source idea. A source may be an academic paper, investment research report, internal strategy memo, algorithm document, white paper, product note, or informal idea document.

## Mode A: Markdown Research Note

Use when the user wants fast research judgment or an internal analytical memo.

Expected files:

- `notes/replication_spec.md`
- `reports/replication_report.md`
- optional `outputs/results.json`

The report should answer whether the source insight is useful, reproducible or adaptable, investable, and worth further system work.

When the report is for decision-makers or external-style presentation, apply `research-report-writer` standards after the evidence and structure are confirmed.

## Mode B: HTML Report

Use when the user needs a polished, shareable report without a full application.

Expected files:

- `reports/replication_report.html`
- supporting chart images or embedded chart data

The HTML report should have strong typography, persistent section navigation when useful, high-quality tables, and conclusion-led chart captions.

## Mode C: Web Visualization Prototype

Use when the user needs to review layout, narrative, chart choices, and investment-bank-style visual design before production implementation.

Expected files:

- `web_prototype/index.html`
- `web_prototype/styles.css`
- `web_prototype/app.js`
- `web_prototype/sample_data.json`
- `web_prototype/frontend_data_contract.md`

Prototype rules:

- It may use static or sample data, but label the data source and assumptions.
- It should prioritize visual confirmation and investment narrative.
- It should include expected interactions such as scenario tabs, date/range filters, metric toggles, and drill-down tables when relevant.
- It should not hide weak or approximate replication results behind polished design.
- It should pass the frontend interaction checklist before being treated as confirmed.

## Mode D: System Implementation

Use after the research and/or web prototype is accepted, or when the user explicitly asks for a working system.

Expected files:

- `src/data_loader.py`
- `src/features.py`
- `src/model.py`
- `src/backtest.py`
- `src/evaluation.py`
- `src/charts.py`
- `config/parameters.yaml`
- focused tests

Implementation rules:

- Preserve source assumptions as configuration where reasonable.
- Keep date alignment, lagging, and rebalance logic testable.
- Export chart-ready data separately from presentation code.
- Produce repeatable outputs for reports and dashboards.
- Implement against a confirmed data contract when a frontend or HTML report consumes generated data.
- For formal quant-system code, apply `quant-develop` engineering standards after this skill freezes the scope and acceptance criteria.

## Mode E: Existing Project Audit

Use when the user already has a project with source documents, algorithm documents, research papers/reports, code, reports, or a frontend.

Expected files or response sections:

- project completeness score
- source-algorithm-code-display consistency matrix
- prioritized remediation list
- missing tests and validation gaps
- recommended next delivery preview or implementation plan

Audit rules:

- Do not assume the existing code correctly implements the source.
- Compare source claims, algorithm documents, code behavior, and displayed results.
- Prioritize issues that can change investment conclusions or break core user workflows.
- Use `P0/P1/P2/P3` priority labels.

## Delivery Preview Requirement

For Modes A-D, produce or describe a Delivery Preview before implementation when scope is non-trivial. For Mode E, use the audit output as the preview for remediation work.

See `related_skills.md` when the task also involves FOHF fact verification, production engineering, or report-prose rewriting.
