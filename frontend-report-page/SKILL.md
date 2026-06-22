---
name: frontend-report-page
description: Use when a page is mainly for reading, review, explanation, or external distribution, where conclusions, evidence, methodology, and narrative clarity matter more than operational interaction.
---

# Frontend Report Page

This mode is for reader-facing HTML reports, review pages, attribution pages,
strategy pages, and research delivery artifacts.

## Core Principle

Heavy on explanation. Light on operation.

## Mandatory Structure

Report pages must include a readable narrative frame. Default to:

- title area with topic and context
- summary or key conclusions
- charts and tables that support the thesis
- sectioned body with clear rhythm
- methodology, scope, sources, or caveat area
- risk reminder, disclaimer, or distribution note when relevant

If the page is long, make section order readable in screenshot, print, and
scroll order.

## Hard Constraints

Report pages must:

- include a summary, conclusion block, or equivalent first-screen takeaway
- explain charts after or beside the visual instead of showing raw figures only
- include methodology, scope, data source, or interpretation basis
- include risk reminder, disclaimer, or usage note when the context calls for it
- maintain section rhythm with clear headings and whitespace
- remain suitable for screenshot, print, export, or external reading

Report pages must not:

- look like a CRUD console or maintenance dashboard
- begin with dense operational controls unless filters are central to reading
- dump raw tables without interpretation
- rely on hover-only interactions to express key findings
- require the reader to infer the thesis from undifferentiated widgets

## Component Defaults

Prefer:

- title and subtitle block
- key conclusion cards
- chart plus explanation block
- methodology note
- evidence table
- timeline or attribution section
- appendix or data-caliber section
- source and caveat strip

Use interaction sparingly. Add only what supports reading:

- anchor navigation
- chart hover details
- section switchers
- lightweight filters tied to interpretation

## Writing Style

- lead with conclusion
- keep section titles informative
- explain what changed, why it matters, and what constrains the conclusion
- write chart notes as interpretation, not axis restatement

## Visual Tone

Keep an institutional research-report language:

- restrained hierarchy
- clear chapter rhythm
- white or light gray base
- charcoal text with muted secondary copy
- thin rules and flat surfaces
- accent colors used as analytical markers, not decoration

If the user asks for J.P. Morgan Asset Management handbook style, bias toward a
flatter, print-like report layout and a cyan/graphite-led chart palette.

## Delivery Check

Before delivery, verify:

- the first screen states what the page is and the main conclusion
- every major chart has explanation nearby
- methodology and caveats are visible somewhere in the page
- the reading order remains clear in a static screenshot or PDF export

## Anti-Patterns

- dashboard-looking widget grids with no thesis
- operations-platform tables presented without narrative framing
- giant hero slogans with little evidence
- chart walls with no interpretation
- method and caveat details hidden entirely behind interaction
