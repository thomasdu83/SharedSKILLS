---
name: frontend-design
description: Use when building a frontend page, dashboard, or HTML artifact and the work must first be classified as an internal operations platform or an external report-oriented page.
license: Complete terms in LICENSE.txt
---

# Frontend Design Router

This skill is a compatibility entry for finance-facing frontend work. It does
not define one universal page structure. It routes the task to the correct page
mode before implementation.

## Mandatory First Step

Before deciding layout, components, or visual emphasis, classify the page:

1. Is the page mainly for internal daily work?
2. Is the page mainly for external reading, review, or distribution?
3. Is the main task operating on objects or explaining conclusions?

If the answer is unclear, ask the user. Do not silently blend both modes.

## Routing

- Use `frontend-page-router` to decide the primary page type.
- If the result is internal workbench, apply `frontend-ops-platform`.
- If the result is reader-facing report, apply `frontend-report-page`.

## Hard Rule

Do not treat finance pages as a single aesthetic category. A fund maintenance
platform, portfolio monitor, and research report may share an institutional
tone, but they must not share the same product structure.

## Shared Finance Tone

After routing, both modes still default to a restrained institutional visual
language:

- white or cool-gray base
- charcoal text
- sparse copper or muted accent color
- thin rules
- minimal shadows
- simplified Chinese unless the user asks otherwise

If the user explicitly references J.P. Morgan Asset Management PDFs such as
`Guide to the Markets`, keep the institutional tone but bias toward flatter,
handbook-style report visuals instead of website accent logic.
