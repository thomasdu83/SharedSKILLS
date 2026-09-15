---
name: quant-research-coding
description: Use when writing lightweight quant research code for data pulls, calculations, factor/signal checks, quick backtests or research helpers (Level 1/2). Exclude page-only formatting of existing results; escalate investment-process or shared recurring outputs to quant-develop.
---

# Quant Research Coding

Use the smallest runnable script and leave auditable evidence. This Skill owns
research computation; formatting already verified results belongs to `frontend-page-router`.
New model/strategy development begins with `ai-quant-development-router`.

| Risk | Default |
|---|---|
| Level 1: one-off pull, calculation or chart | Run once; inspect a sample, dates, row counts and units |
| Level 2: repeatable research or exploratory backtest | Clear entrypoint, parameters, sanity checks and saved outputs |
| Level 3: shared recurring or investment-process consumption | Handoff to `quant-develop` |
| Level 4: live/irreversible/high-impact action | External controls and applicable approval; not this lightweight workflow |

## Before computing

Read [research workflow](references/research-workflow.md) for execution checks,
backtest evidence, retention, coding and escalation rules. Use existing data skills
and resolve necessary repository templates; don't invent missing dependencies.

Check time alignment/PIT, missingness, duplicates, survivorship, benchmark,
frequency, costs/turnover/capacity and fallback conditions where relevant.
Do not use `latest_only` to justify a historical backtest. Measure bottlenecks
before optimizing. Run fresh verification before claiming completion.

## Output

Record `research_only: true`, data status (`exact/proxy/latest_only/missing/unverified`),
universe/date range/missingness, PIT visibility, cost assumptions, reproducible command,
outputs and limitations, using `../shared-contracts/data-freshness.yaml` and `evidence.yaml`.
A successful script is not `portfolio_ready`. Research cannot overwrite fund facts
or production configuration. Promotion generates a new engineering route decision.
