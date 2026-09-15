---
name: frontend-page-router
description: Use when creating or changing a finance/research page, workbench, dashboard or HTML report, including formatting existing results; frontend-design is a compatibility alias.
---

# Frontend Page Router

Choose one mode before layout. Reuse a mode already established by the user.
For an ongoing research/engineering task, this is a delivery support; for a
page-only task it is the primary entry. Existing results stay unchanged.

| Main user task | Apply |
|---|---|
| Maintain, edit, batch, construct, triage or monitor objects | `frontend-ops-platform` |
| Read, explain, compare, review or distribute conclusions | `frontend-report-page` |
| Historical backtest or candidate review without rerun controls | `frontend-report-page` |
| Finalized model or indicator monitoring, inspect only | `frontend-ops-platform`, `read_only_monitor` |
| Backtest batch management and rerun controls | `frontend-ops-platform` |

Charts, filters, tabs and colors do not decide the mode. A sortable report remains
a report if it helps reading. Do not add write actions to a read-only monitor.
If context cannot establish the main user task, ask one short routing question.

## After selecting the mode

1. Load the selected mode Skill and [shared finance design](references/finance-design.md).
2. For QuantSystem dense interactive pages, read its `docs/templates/frontend-interaction/README.md`;
   indicator shells also use `docs/templates/indicator-monitor/README.md`. Resolve the external
   template dependency before use; do not invent missing files.
3. Make a preview when layout is unsettled, then inspect desktop/mobile state.
4. Record `page_mode`, selected specialist, input artifact and verification status.
   For existing frozen results, use `shared-contracts/delivery-input.yaml` from the shared library.

`frontend-design` normalizes to this Skill. Never count both names as two skills.
A route decision contains one primary and at most two supports for the current phase.
