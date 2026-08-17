---
name: quant-research-coding
description: Use when writing lightweight quant research code for one-off data pulls, quick backtests, factor checks, label or signal prototypes, allocation analysis, chart/table generation, report-support processing, or repeatable research helpers where mistakes mainly waste research time. Prefer this for Level 1/2 work; escalate to quant-develop when recurring, shared, platformed, client-visible, or investment-process critical.
---

# Quant Research Coding

Use this skill for lightweight research code in quant investing, asset
allocation, fund research, and investment management. The goal is fast,
auditable exploration without turning every script into a formal system.

## Default Posture

Move quickly, but leave enough evidence that the result can be checked later.
Prefer simple scripts, clear inputs, deterministic outputs, and explicit sample
validation. Avoid premature architecture.

## Risk Levels

| Level | Typical work | Default bar |
|---|---|---|
| 1 | One-off data pull, chart, format conversion, quick calculation | Minimal script or command; inspect sample output |
| 2 | Daily research helper, repeatable backtest, backtest review HTML, report-support table | Clear entry point, parameters near the top or in a small config, sanity checks, saved output |
| 3 | Client/company-visible output, recurring investment-process input | Escalate to `quant-develop`; add tests, logging, contracts, review |
| 4 | Live trading, irreversible operations, regulatory/safety critical | Do not rely on this skill; require external controls and approvals |

## Research Funnel and Retention

Classify the work before deciding how much structure to create:

- A throwaway calculation only needs a checked sample result; do not create a project or registry entry.
- A repeatable research script keeps its command, parameters, coverage checks, and saved output.
- A serious backtest keeps a run manifest and static review HTML, including excluded or failed variants in the comparison batch.
- A candidate handoff carries the hypothesis, entrypoint, parameter set, PIT/data scope, validation evidence, failure conditions, and promotion reason into `quant-develop`.
- A recurring indicator that produces only state, change, or alerts can become a lightweight `monitor_only` project; it is not automatically a model or a Champion candidate.

## Workflow

1. Classify the task as exploration, repeatable research, candidate handoff, or indicator monitoring.
2. Identify the smallest useful output: CSV, chart, Markdown table, JSON,
   notebook cell result, or a static HTML backtest review document.
3. Use existing data/API skills first when relevant, especially
   `zmdata-data-api`, `wisdom-manager-product-research`, or `fund-wiki`.
4. Write the simplest maintainable Python that solves the research question.
5. Add cheap safeguards:
   - check row counts, date ranges, missing values, duplicate keys, and units
   - check the source coverage and whether each input was visible at the target date
   - normalize date precision before joins; inspect `merge_asof` and rolling direction
   - if optimizing speed, add simple timing around load/compute/export before changing code
   - avoid optimizing writes when timing shows the bottleneck is data access or compute
   - print or log a small sample of the final result
   - if the result is empty or unexpectedly large, distinguish sample reality from a rule or join error
   - when using a fallback or relaxed threshold, test that it only triggers under its stated condition
   - save outputs with clear names when the user needs artifacts
   - avoid overwriting important files without confirmation
6. Run a fresh verification before saying the work is complete.

## Backtest Review HTML

For historical backtests, do not default to a frontend application. A static
HTML document is usually the right research artifact when the user needs to
review or share results.

Include only the parts that make the backtest auditable:

- model hypothesis, asset universe, benchmark, rebalance rule, and fee/cost
  assumptions
- sample period, data vintage, point-in-time caveats, and replication command
- summary metrics, NAV/drawdown, calendar returns, turnover, risk exposure, and
  scenario or robustness checks
- parameter set, run id, output paths, failure conditions, and known limitations

If the model becomes a finalized production or monitoring input, escalate to
`quant-develop` before building interactive tracking, publish, alerting, or
frontend integration.

## Coding Style

- Prefer a single focused script for Level 1 work.
- For Level 2 work, split only when it removes real complexity:
  `load_data`, `compute`, `validate`, `export`.
- Keep research parameters visible and easy to change.
- Use `logging` for repeatable helpers; a brief `print` is acceptable for
  throwaway Level 1 inspection scripts.
- Do not create `project.yaml`, `registry/`, `workflows/`, packaging, or a full
  test suite unless the code is being promoted to `quant-develop`.
- Avoid adding dependencies for convenience; prefer pandas/numpy/scipy/sklearn
  and libraries already present in the environment.

## Research Checks

For quant work, prioritize checks that catch investment-research mistakes:

- date alignment and lagging: no look-ahead
- point-in-time visibility of every input, including cached or backfilled data
- duplicate keys before `pivot`, `merge_asof`, or aggregation
- survivorship and sample filters: state what universe was used
- benchmark and fee assumptions: make them visible
- NAV/return frequency: confirm daily, weekly, monthly, or irregular
- missing data and outliers: report counts and handling
- turnover, transaction costs, and capacity: include when relevant
- strict-rule versus fallback-rule counts when thresholds or safety nets exist
- performance timing when speed is part of the task: load, compute, write, and the slowest stage
- output schema: columns, units, and date format are clear

## Escalation

Escalate to `quant-develop` when:

- the script will run repeatedly or be used by other people
- outputs enter portfolio construction, monitoring, IC/client materials, or
  downstream systems
- failure needs logging, alerting, retries, contracts, or access control
- there is a stable data contract or a need for `project.yaml`, `registry/`, or
  `workflows/`
- the user asks for finalized model tracking, publish gates, daily monitor
  state, or an interactive operations workbench
- a recurring indicator needs a standard monitor snapshot or read-only tracking
  page, even when it is not an investment model

Escalate to `old-coder` only for high-assurance modules where the user asks for
proof/evidence or the code can directly cause high-impact harm.
