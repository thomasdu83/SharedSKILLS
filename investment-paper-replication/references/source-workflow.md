# Source replication workflow

This method is subordinate to the selected task primary. Source-based new model development uses ai-quant-development-router as primary. Reference documents named below live in this directory. Skill assets live under the skill root; project output examples are relative to the current project.

## Standard Workflow

1. **Task classification**
   - Determine whether this is new project creation, existing project audit, report production, frontend prototype, or system implementation.
   - For existing projects, read `project_audit_checklist.md` and audit before making changes unless the user explicitly asks for immediate fixes.

2. **Source intake**
   - Identify source type: academic paper, research report, strategy memo, algorithm document, white paper, product note, or idea document.
   - Identify research type: factor, asset pricing, macro allocation, portfolio construction, risk, machine learning, execution, or qualitative framework.
   - Extract research question, investment hypothesis, model, required data, sample period, frequency, variables, portfolio construction rules, transaction cost assumptions, and headline findings.
   - Flag missing details that affect reproducibility.

3. **Replication spec**
   - Create `replication_spec.md` before implementation when the task is non-trivial.
   - Include target tables/figures, formulas, data requirements, field mappings, assumptions, and validation thresholds.
   - Use `replication_checklist.md` for technical checks.

4. **Data feasibility mapping**
   - Map each source variable to available local data, possible substitutes, and residual risk.
   - Distinguish exact replication, approximate replication, and conceptual adaptation.

5. **Delivery Preview Gate**
   - Before project implementation, produce a preview that matches the delivery type.
   - Report preview: report outline, chart/table plan, expected findings, and review questions.
   - Frontend preview: information architecture, first-screen layout, component list, interaction plan, sample data schema, and static prototype when useful.
   - System preview: module plan, data contracts, run commands, acceptance tests, and known risks.
   - Read `delivery_preview_gate.md` for required preview artifacts.
   - Reuse approval already present in the task. Ask only for unresolved choices that change the delivery scope; user-authorized implementation may proceed.

6. **Minimal replication**
   - Build the smallest runnable analysis that tests the core idea.
   - Prefer clear scripts or notebooks over premature framework code.
   - Produce core tables, figures, and diagnostics before writing a polished report.

7. **Research report**
   - Write a Markdown report first when the user needs analytical judgment.
   - Use conclusion-led headings and distinguish evidence from interpretation.
   - Read `report_structure.md` for the standard structure.
   - When prose quality, narrative flow, or thesis clarity is central, apply `research-report-writer` standards after the evidence structure is fixed.

8. **HTML report or web prototype**
   - Use HTML for polished reading and web prototype for interactive review.
   - If a web prototype is requested, use sample or exported results first. Confirm layout, narrative, colors, chart hierarchy, and interactions before connecting full production logic.
   - Use `frontend-page-router` for page mode and shared visual standards. Read the legacy `frontend_style_guide.md` only when maintaining an existing artifact that explicitly uses it.
   - Read `frontend_interaction_checklist.md` and `frontend_data_contract.md` before implementing interactive screens.
   - Reuse `assets/frontend-template/` when a lightweight prototype is appropriate.

9. **Investment validation**
   - Evaluate whether the result is a tradeable signal, explanatory lens, risk monitor, allocation input, or research-only insight.
   - Read `investment_validation.md` for the validation frame.

10. **Code landing**
   - Implement production code only after research logic and presentation direction are accepted, unless the user explicitly asks for direct implementation.
   - Create modular files for data loading, feature construction, model logic, backtest/evaluation, chart data export, and report generation.
   - Add tests around date alignment, lagging, portfolio formation, and output schema when risk warrants it.
   - Use `acceptance_testing.md` to define and run verification, especially for frontend interactions.
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
