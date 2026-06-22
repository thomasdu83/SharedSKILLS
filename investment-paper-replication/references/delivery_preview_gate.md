# Delivery Preview Gate

Use this gate before implementation for any non-trivial source replication/adaptation, report, frontend, or system build. The purpose is to confirm the final artifact before expensive coding begins.

## When Required

Require a preview when:

- the user asks for a report, HTML output, frontend, dashboard, app, or system
- the requested output has more than one screen, module, or major section
- the source's data or methodology is ambiguous
- the user-facing presentation could affect investment interpretation

You may skip the gate only when the user asks for a small direct edit, a quick answer, or explicitly says to implement immediately.

## Report Preview

Create `notes/delivery_preview.md` or an equivalent response containing:

- report title and audience
- section outline
- the question each section answers
- planned chart and table list
- expected source-versus-replication/adaptation comparison
- key assumptions and missing data
- proposed final recommendation labels

Do not draft the full polished report until the outline and analytical framing are accepted, unless the user asks to continue.

## HTML Report Preview

Include:

- report information architecture
- typography and visual tone
- table/charts to be embedded
- navigation plan
- source note and methodology placement
- mobile readability considerations

## Frontend Preview

Create some combination of:

- information architecture
- first-screen layout description
- page/component inventory
- chart inventory
- interaction flow
- sample data schema
- static web prototype

The prototype can use sample data, but it must make clear which values are placeholders.

## System Preview

Create:

- module plan
- data contract
- run sequence
- configuration plan
- acceptance test plan
- known risks and manual review points

## Freeze Before Implementation

After user confirmation, freeze:

- report sections or page structure
- chart/table list
- metrics and formulas
- data schema
- interactions and states
- output paths and file formats
- acceptance criteria

If the user changes the delivery shape later, update the preview and call out the scope change.
