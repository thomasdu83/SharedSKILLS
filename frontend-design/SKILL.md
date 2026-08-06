---
name: frontend-design
description: Use when building a finance, research, portfolio, risk, fund, score, weekly-report, dashboard, workbench, or HTML frontend and the primary page mode is not yet classified.
license: Complete terms in LICENSE.txt
---

# Frontend Design Router

This skill is the compatibility entry for QuantSystem-style finance frontends.
It does not define one universal page. It first routes the task, then applies a
shared institutional design language.

## Mandatory First Step

Before layout, components, or visual styling, classify the page:

1. Is the primary user operating on objects, or reading conclusions?
2. Is success faster action, or faster understanding?
3. Is the page used repeatedly by an internal team, or distributed as a report?

Use `frontend-page-router` for the decision. If the result is internal work,
apply `frontend-ops-platform`. If the result is reader-facing delivery, apply
`frontend-report-page`.

If the prompt is ambiguous, ask one short question. Do not silently blend a
workbench and a report cover.

## Shared Finance Language

After routing, both modes should feel like a quiet institutional tool, but the
canvas should follow the mode:

| Mode | Page base | Working surface | Reading feel |
| --- | --- | --- | --- |
| report page | `#f7f8fa` or `#f5f5f2` | white sheet, white charts, white tables | published, print-like, editorial |
| workbench | `#f4f6f8` | white table/detail/form surfaces | operational, low-glare, repeat-use |

- text: charcoal `#20262d` / `#111`; muted copy `#61656b` / `#68727d`
- lines: `#d8dee5`, `#d0d0cb`, `#b9c3cd`
- accents: navy `#1f4e79`, cyan `#11a7d9`, copper `#936846`
- semantic colors: green for constructive state, red/orange for risk or heat
- typography: compact Chinese UI, 12-13px table text, 15px panel headings,
  24-30px page titles, tabular numerals for scores and weights
- surfaces: thin borders, radius 0-6px, minimal shadow, no decorative gradients
- mode rule: report pages are white-canvas first; workbenches are gray-shell
  with white work surfaces

## Common Layout Rules

- Use a constrained page width around 1400-1540px for research reports and
  dense workbenches.
- Keep first-screen content functional: conclusion plus evidence for reports;
  scope plus table/work surface for operations.
- Start with one or more preview HTML pages when the visual structure is still
  unsettled or the page has multiple viable layouts.
- Treat the preview HTML as a contract for spacing, hierarchy, and data shape
  before wiring the page into the app.
- Keep the preview simple enough that the core function is obvious without
  explanation.
- Give reports more vertical breathing room between sections than workbenches.
- Treat cards as information units, not page-section wrappers.
- Put controls beside the object they affect.
- Prefer real data tables, charts, selectors, drawers, and editable fields over
  placeholder widgets.
- Do not let a background color decide the page mode. Task first, palette later.
- Remove anything that does not help the first useful task on the page.

## Quality Gate

Before delivery, inspect the page at desktop and mobile widths:

- text fits buttons, tabs, tables, and cards without overlap
- the first screen shows the primary task immediately
- colors are not one-note blue/purple/beige
- interactions visibly change state
- report pages remain readable as screenshots or exports
- workbench pages remain usable for repeated daily actions
