---
name: frontend-ops-platform
description: Use when a frontend is mainly an internal daily workbench, management platform, maintenance tool, filter console, editing workflow, monitor, triage view, or portfolio construction platform where efficient object-level operation matters more than narrative delivery.
---

# Frontend Operations Platform

Operations platforms are for repeated internal work. The page should feel like a
quiet control surface, not a report cover.

## Core Principle

Make the object, its state, and the next action visible at the same time.

## Default Workbench Structure

Start from this layout:

- topbar with product name, date/scope chips, and high-level navigation
- segmented view tabs for major workflows
- left rail for filters, tags, tree, scope, or version selection
- central table or editable work surface
- right detail panel for the selected object, risk summary, or current draft
- drawer or modal for create/edit/batch workflows

Remove areas the task does not need, but do not replace the work surface with
decorative KPI cards.

## Preview-First Delivery

When building a new workbench or redesigning a complex page:

- build one or more static preview HTML pages before app integration
- preview the main workflow with realistic rows, filters, selected states, and
  detail/edit surfaces
- keep the first preview focused on the core operation instead of every future
  feature
- use additional preview variants only for materially different layouts or
  workflows
- promote the preview into implementation only after the core object, state, and
  next action are clear

## Workbench Canvas

Keep a low-glare shell and white work surfaces:

- use light gray for the page shell, navigation bands, gutters, and secondary
  rails
- use white for tables, editable drafts, detail panes, forms, and active charts
- use subtle gray only to separate zones; the main object area must stay visually
  dominant
- avoid pure-white full-page workbenches when the user will stare at dense
  tables for long sessions
- avoid large filled gray blocks inside the working surface

## Proven Workbench Patterns

Use these defaults for finance and fund platforms:

| Workflow | Structure |
| --- | --- |
| full-market or fund-pool review | filter rail + sortable table + selected-row detail |
| tag or pool maintenance | tag tree + status filters + table + detail actions |
| portfolio construction | rule/benchmark rail + draft table with editable weights + risk/reference side panel |
| portfolio monitoring or attribution | parameter rail + explanation panel + pivot table/detail report |
| add or edit objects | right drawer with grouped form sections and sticky actions |

## Hard Constraints

Operations platforms must:

- make tables, lists, forms, or editable drafts the primary surface
- keep controls close to the rows, object, or panel they affect
- support real filtering, sorting, selection, editing, saving, deleting, and
  state feedback
- derive badges, counts, and status from data
- show empty, loading, error, selected, active, and hidden states
- preserve column widths and stable row height in dense tables
- keep default view aligned with the daily workflow
- ship the smallest workflow that lets the user complete the core task before
  adding secondary analytics or chrome

Operations platforms must not:

- use a hero section by default
- open with long narrative text
- lead with decorative KPI cards instead of the active work area
- separate controls from affected data
- imitate a report, brochure, or landing page
- hide required editing behind unclear icons or non-obvious gestures
- add secondary panels, metrics, or tabs before the core workflow is usable

## Component Defaults

Prefer:

- segmented top navigation
- filter rows and reset rows
- multi-level tag tree or scope rail
- sortable table headers with clear active direction
- selected-row highlighting with a left accent rule
- status pills for investable, watching, holding, paused, excluded, risk
- detail key-value grids
- inline inputs for weights, limits, dates, and notes
- drawers for add/edit workflows
- toast or status message for feedback

Cards are allowed only for operational value: counts, risk checks, exposure
summary, pending queue, or selected-object facts.

For terminal-grade tables:

- right-align numeric columns and left-align names/descriptions
- use tabular numerals for weights, exposures, scores, ranks, and changes
- keep sticky headers and, when useful, a frozen identity column
- show active sort direction, selected row, hover row, and edited row states
- keep row height and column widths stable when filtering, sorting, or editing
- format nulls and unavailable data deliberately, not as accidental blanks

## Visual Defaults

- page shell `#f4f6f8`, work surfaces `#fff`, secondary rails `#f8fafb`
- charcoal text, muted secondary copy, thin gray borders
- navy for primary action and active state, copper for review/attention, green
  and red for semantic state
- radius 4-6px, little or no shadow
- 12-13px table text, 15px panel headings, 22-24px key counts
- dense grids with stable min widths; avoid layout shifts when rows update
- topbar and summary strips should be quieter than the central work surface

## Writing Style

- labels are short and operational: `应用筛选`, `添加基金`, `保存新版本`
- panel notes explain scope or consequence, not marketing value
- button text names the action and object when ambiguity is possible
- destructive actions use direct labels and confirmation context

## Interaction Reality Check

Before delivery, verify:

- view tabs switch major workflows
- filters visibly change table/list scope and can reset
- rows can be selected and details update
- sort headers expose active direction
- editable fields look editable and preserve layout
- drawer forms have grouped sections and clear actions
- save/delete actions show state feedback
- empty and loading states are not blank pages
- the gray shell supports focus instead of competing with the active table/form

## Anti-Patterns

- KPI cards replacing the workbench
- report-style longform explanation above the table
- decorative dashboard chrome with no object actions
- repeated cards duplicating table data
- controls far from the rows or draft they affect
- table columns that resize or wrap unpredictably during interaction
- gray panels nested inside gray panels until the active work area loses focus
- preview variants that explore styling while leaving the main workflow vague
