---
name: frontend-ops-platform
description: Use when a page is mainly for internal daily work such as maintenance, filtering, editing, monitoring, triage, or portfolio construction, where efficient operation matters more than narrative explanation.
---

# Frontend Operations Platform

This mode is for internal tools used repeatedly over time. The goal is fast
action with low cognitive noise.

## Core Principle

Heavy on operation. Light on explanation.

## Mandatory Structure

Default to a workbench layout such as:

- top utility bar or segmented navigation
- left filter rail, tree, or scope selector
- central table or main work surface
- right detail panel, drawer, or side editor

When the task does not need all four areas, remove the unnecessary one. Do not
replace the main work surface with decorative summary cards.

## Hard Constraints

Operations platforms must:

- make tables or dense structured lists the primary surface
- keep controls close to the object being acted on
- keep default views aligned with the daily workflow
- derive status from data whenever possible instead of manual duplicated labels
- support real interactions such as filtering, switching, expanding, editing,
  drawer detail, batch action, and state feedback
- keep information dense but with clear hierarchy

Operations platforms must not:

- use a hero section by default
- open with long narrative text
- repeat the same status in decorative cards without action value
- place critical controls far away from the affected object
- spend the first screen on explanation instead of working context
- imitate a report cover, brochure, or landing page

## Component Defaults

Prefer:

- table
- toolbar
- filter buttons
- segmented tabs
- left tree or tag rail
- right detail panel
- drawer editor
- inline edit area
- status badge with action feedback

Use cards only when they carry operational value such as alert queues, pending
review counts, or compact object summaries.

## Writing Style

- keep labels short
- keep notes brief and task-oriented
- avoid paragraph-style explanation unless it changes an action
- make button copy direct and operational

## Visual Tone

Keep an institutional, quiet, dense interface:

- white or cool-gray base
- charcoal text
- sparse copper, navy, or muted accent
- thin borders
- little or no shadow
- strong table headers and grid discipline

## Interaction Reality Check

Before delivery, verify that the preview contains real usable interaction
surfaces, not only visual placeholders:

- filters can visibly change scope
- tabs or segmented controls switch views
- drawers or details open around a selected object
- editable fields look editable
- action buttons map to clear object-level tasks

## Anti-Patterns

- KPI cards replacing the actual workbench
- report-style longform explanation above the table
- decorative dashboard chrome without actionable state
- repeated summary cards that duplicate row-level data
- controls separated from the rows, objects, or panels they affect
