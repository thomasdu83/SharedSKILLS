---
name: frontend-report-page
description: Use when a frontend is mainly a report, weekly report, score report, research delivery, attribution review, strategy page, or reader-facing HTML artifact where conclusions, evidence, methodology, and narrative clarity matter more than editing workflows.
---

# Frontend Report Page

Report pages help readers understand a conclusion quickly, then inspect the
evidence without losing the thread.

## Core Principle

Lead with the thesis on a white research canvas, then make the evidence
navigable.

## Default Structure

For finance research reports, start with:

- compact title area with date, scope, sample count, and method chips
- first-screen conclusion cards, not generic KPI tiles
- narrative mainline or summary paragraph beside the conclusion cards
- primary comparison table or chart within the first two sections
- detail area for one selected object, asset, industry, strategy, or fund
- methodology, data scope, source, caveat, or usage note

Long reports may add fixed or sticky navigation, section tabs, a left strategy
list, or iframe/detail loading, but the interaction must support reading.

## Preview-First Delivery

When the report layout is still uncertain:

- build one or more static preview HTML pages first
- use real sample data or realistic placeholders, not decorative filler
- test the page as a screenshot and as a scrolling reading experience before
  wiring it into the final app flow
- keep the preview minimal enough that the thesis, evidence, and caveat order
  are immediately visible

## Publication Discipline

Use international investment-bank research polish:

- treat the report as a white sheet on a very pale page shell
- make section order read like a chartbook: conclusion, evidence, interpretation,
  method/source
- keep chart title, subtitle, unit, date range, and source/caveat close to each
  major chart
- keep tables and charts on white surfaces; use gray only as environment,
  dividers, or secondary rails
- use footnotes and source strips as visible trust signals, not hidden appendix
  material
- avoid turning every section into a floating card; section rhythm can come from
  headings, rules, spacing, and aligned chart blocks

## Proven Report Patterns

Use the pattern that matches the content:

| Content | Structure |
| --- | --- |
| macro or asset score report | conclusion cards + score matrix + mainline + object selector + timeline/radar + rationale + scenarios |
| industry score report | sector strip + conclusion cards + sortable total table + sector/industry filters + selected-industry detail + rationale |
| fund weekly report | report header + period metadata + summary notes + chart blocks + sortable leaderboard/evidence tables + footnotes |
| multi-strategy weekly report | fixed top nav + dashboard overview + strategy sidebar + one active strategy report + market environment + manager stats |
| single-object fact sheet | compact title/meta + positioning + benchmark/performance/attribution/holding tables + notes |

## Hard Constraints

Report pages must:

- state the topic and main conclusion on the first screen
- show both summary and inspectable evidence
- keep charts near interpretation or labels that explain what matters
- make sortable/filterable tables support comparison, not operations
- include data date, scope, sample count, method, or caveat when relevant
- remain readable in screenshots, print, export, and static HTML
- prefer the smallest section set that still explains the conclusion well

Report pages must not:

- open with an oversized marketing hero
- look like a CRUD console unless the reader task requires table-first review
- dump raw tables without conclusion, rank, trend, or explanation
- hide key conclusions behind hover-only interaction
- use decorative cards that duplicate row-level data without insight

## Component Defaults

Prefer:

- title/subtitle plus meta chips
- conclusion cards with labels such as strongest, weakest, fastest warming
- narrative mainline with a left accent rule
- score matrix, sortable evidence table, heatmap, timeline, radar, or line chart
- selector/filter that changes the reading scope
- selected-object detail panel with score, trend, rank, strengths, weaknesses
- rationale sections by dimension
- footnote, source, method, and caveat strip

For evidence tables:

- right-align numeric columns and left-align names/descriptions
- use tabular numerals for scores, weights, returns, ranks, and changes
- freeze or visually anchor the identity column when tables are wide
- show active sort direction and rank/change markers explicitly
- format nulls, unavailable data, and outliers deliberately instead of leaving
  visual gaps

Use interaction sparingly:

- tabs for major reading sections
- sortable columns for ranking and comparison
- filters/selects for sector, asset, strategy, or fund scope
- hover tooltips for chart detail
- one active detail object at a time

## Visual Defaults

- page width around 1400-1480px
- page shell `#f7f8fa` or `#f5f5f2`; report sheet and evidence panels `#fff`
- use white as the dominant report canvas; gray should not make the page feel
  like an admin console
- 1px borders, little or no shadow, radius 0-6px
- headings 15-30px, chart titles 13-15px, table text 12-13px
- more breathing room than a workbench: 24-32px between major sections
- navy/cyan/copper as analytical accents
- heatmaps and score bands use semantic color, not decoration
- table headers are sticky when tables are long
- chart containers have stable heights, usually 320-420px
- chart legends are compact and stable; avoid color changes between sections

## Writing Style

- lead with what changed and why it matters
- title sections by analytical role: `本期结论卡`, `评分总表`, `评分依据`
- write chart titles as findings when possible, not neutral widget labels
- write chart notes as interpretation, not axis restatement
- use brief Chinese UI labels; avoid paragraphs inside buttons or tabs

## Delivery Check

Before delivery, verify:

- first screen contains conclusion plus evidence
- every major chart or table has nearby interpretation or context
- chart title, unit, date range, and source/caveat are visible where relevant
- filters and tabs visibly change the reading state
- long tables have stable headers and column widths
- caveats, sample scope, or methodology are visible
- mobile layout stacks without text overlap

## Anti-Patterns

- dashboard-looking widget grids with no thesis
- operations-platform maintenance controls on an external report
- giant slogans without evidence
- chart walls with no interpretation
- multiple nested cards around every section
- full-page gray backgrounds that make external reports feel like back-office
  tools
- method and caveat details hidden entirely behind interaction
- add sections that do not change the reader's understanding of the thesis
