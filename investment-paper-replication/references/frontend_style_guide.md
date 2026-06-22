# Frontend Style Guide

Use this guide for HTML reports and web visualization prototypes in finance,
investment research, quant, portfolio, risk, allocation, fund analysis, or
investment committee workflows. The default aesthetic is an international
investment-bank research product, not a technology landing page.

## Page Mode Gate

Before deciding layout, first classify the page:

- **Internal operations platform**: mainly for filtering, editing, maintaining,
  monitoring, triage, or workflow execution
- **External report page**: mainly for conclusions, explanation, review,
  attribution, or distribution

Do not silently merge these two page types into one generic finance dashboard.

For internal operations platforms:

- make tables or dense structured lists the primary surface
- keep controls close to the affected object
- avoid hero sections and long narrative text
- avoid decorative repeated status cards
- let the default view serve the daily workflow

For external report pages:

- include a summary or key conclusion block
- place explanation near charts and tables
- include methodology, scope, sources, or caveats
- include risk reminder or disclaimer when relevant
- keep the reading order suitable for screenshot, print, and external reading

## Default Brand Reference

Unless the user specifies another house style, use `jpmorgan.com` as the
default visual reference for finance-facing pages. This means adopting its
institutional tone, restrained hierarchy, thin-rule layout language, and sparse
copper accents while adapting the composition to research and dashboard use
rather than copying a public marketing page verbatim.

Default to Simplified Chinese for interface copy unless the user explicitly
requests another language.

## International Investment Bank Interface Style

### Trigger Conditions

Use this style by default whenever the task involves:

- investment research
- quant strategies
- portfolio analysis
- risk management
- fund analysis
- asset allocation
- investment committee materials
- research workbenches

### Style Definition

The interface should feel like a professional research terminal, risk dashboard,
or pitchbook-grade analytical workbench: calm, restrained, professional,
high-information-density, and built for PMs, IC members, researchers, and risk
users to scan quickly. The intended tone is close to J.P. Morgan's public web
presence: premium, measured, and information-first.

### Visual Constraints

- Main colors: white, very light cool gray, charcoal, ink, muted navy
- Accent colors: copper, muted bronze, deep green, metallic gray, used sparingly
- Avoid: beige or paper-texture palettes, warm browns, retro serif display
  headlines, decorative shadows, magazine-style composition, landing-page
  heroes, gradient blobs, ornamental cards, and tech-product glow
- Typography: modern neutral sans-serif for body text; headings can be light or
  firm, but not editorial or theatrical. When available, use Amplitude or a
  close neutral substitute; otherwise conservative Helvetica/Arial-style
  fallbacks are acceptable for prototypes
- Borders: thin rules, square or compact corners, restrained spacing, and weak
  or no shadows

### J.P. Morgan Style Summary

Apply these cues consistently:

- keep the page bright, flat, and structured with white or cool-gray surfaces
- use charcoal copy, not pure black headlines plus colorful secondary text
- use copper accents for links, small highlights, and selective CTA emphasis
- favor utility navigation, section dividers, and disciplined spacing
- keep cards flat and structural, not ornamental
- use promotional imagery only when it adds context; do not let it replace data
- let the first screen answer what the page is, what changed, and why it matters
- keep the feature surface narrow and show only core functions by default

### Component Defaults

Prefer components that support reading and comparison:

- top run-context or summary strip
- left parameter panel or filter rail
- central chart matrix
- KPI strip
- strategy comparison table
- scenario tabs
- risk note or methodology annotation
- small multiples, scatter plots, bar charts, line charts, and distributions

### Chart Rendering Priority

Unless the user explicitly requests a different charting stack, render charts in
this order:

1. **ECharts** for interactive investment dashboards, chart matrices, tooltips,
   date-range controls, scenario tabs, time-series views, scatter plots,
   drawdown charts, heatmaps, and distribution views.
2. **Inline SVG** for small static visuals, micro charts, custom annotations,
   compact legends, or dependency-free diagrams.
3. **Python-rendered images** only when the chart requires Python-only
   computation, specialized statistical plotting, complex offline generation, or
   a static audit figure. Generate the image first, then load it into the HTML
   or app as an asset.

Do not default to Python images for web-facing charts when ECharts can render
the same view interactively and auditably in the page.

### Default Decision Rule

When uncertain, choose a layout that resembles an institutional research portal
or investment committee dashboard, not an editorial page or SaaS landing page.

## Preferred Palette

Use a light base with institutional accents:

- background: white or very light cool gray such as `#f5f7f8`
- text: charcoal or near-black such as `#31373d`
- primary accent: muted navy or steel blue such as `#2f5e88`
- secondary accent: copper or bronze such as `#936846`
- chart neutrals: slate, gray, light gridlines

Avoid one-note palettes. Avoid dominant purple gradients, neon blues,
glassmorphism, tech glow, decorative gradient blobs, and warm beige or brown
dominance.

## Layout

- Lead with a compact executive panel, topic strip, or decision summary, not a
  marketing hero.
- Show only the minimum number of sections and controls needed for the core
  workflow.
- Use dense but readable grids.
- Use full-width report sections or tool surfaces, not nested decorative cards.
- Use tables for definitions, assumptions, and comparison matrices.
- Use chart titles that state conclusions, not merely metric names.
- Keep source notes, date ranges, and methodology caveats visible.
- Ensure every major visual answers an investment question.
- Do not default to editorial or consumer SaaS framing when the page is for
  finance or research.
- For navigation, prefer slim utility bars, section anchors, or segmented
  controls over oversized chrome.

## Feature Scope

- Default to core functionality only.
- Do not add search, sharing, favorites, export centers, watchlists, onboarding
  tours, or assistant widgets unless the user explicitly needs them.
- Treat filters as optional, not mandatory. If one chart and one table answer
  the question, stop there.
- Every visible control should map to a clear investment or research task.

## Components

Expected components may include:

- section navigation
- KPI strip
- methodology table
- source-versus-replication comparison table
- time-series chart
- drawdown or risk chart
- factor/asset heatmap
- robustness matrix
- scenario tabs or segmented controls
- export buttons when useful

Use icons sparingly and only for clear commands or status markers. Avoid decorative icons.

## Interaction

- Provide filters that match investment workflows: period, region, asset class, universe, rebalance frequency, transaction cost, signal definition, and benchmark.
- Keep interactions explainable; avoid playful animations.
- Make hover states and tooltips informative, especially for charts and assumptions.
- Keep CTA copy concise and professional: `Explore`, `View methodology`,
  `Request access`, `Open detail`, `Download`.
- When a control is not essential to the main task, omit it rather than hiding
  it behind secondary menus.

## Typography

- Prefer compact professional typography.
- For Chinese pages, default to Simplified Chinese copy and keep labels short,
  direct, and information-bearing.
- Use restrained heading sizes in research products, even if the reference site
  sometimes uses large light-weight marketing headings.
- Do not use viewport-scaled font sizes.
- Keep letter spacing at 0 unless matching an existing design system.
- Ensure text never overflows buttons, table cells, tabs, or cards.
- For finance interfaces, prefer a modern neutral sans-serif body face and
  weight-based hierarchy over decorative editorial styling.

## Prohibited Patterns

- SaaS landing-page hero sections
- oversized inspirational headlines
- blue-purple gradient backgrounds
- glass cards
- nested cards
- decorative orbs, blobs, or bokeh
- cartoon illustrations
- empty dashboard cards that do not support investment judgment
- excessive rounded corners
- oversized serif headlines
- magazine-style composition
- beige or paper-texture dominance
- copper overuse that turns the page into a luxury brochure
- public-brand slogans without immediate analytical substance
- English-first placeholder copy when the user has not asked for English
- auxiliary controls that distract from the main analytical task

## Prototype QA

Before delivering, inspect the page in desktop and mobile widths. Verify:

- charts render and are not blank
- tables remain readable or scroll cleanly
- text does not overlap
- controls are usable
- visual hierarchy still feels institutional
- the first viewport communicates the source, result, and investment question
