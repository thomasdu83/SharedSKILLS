---
name: quant-research-coding
description: Use when writing lightweight quant research code, one-off Python scripts, exploratory data pulls, quick backtests, factor checks, allocation analysis notebooks/scripts, chart/table generation, report-support data processing, or research prototypes where mistakes mainly waste time rather than directly affect production portfolios or clients. Prefer this before quant-develop for Level 1/2 work; escalate to quant-develop when the code becomes recurring, shared, platformed, or investment-process critical.
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
| 2 | Daily research helper, repeatable backtest, report-support table | Clear entry point, parameters near the top or in a small config, sanity checks, saved output |
| 3 | Client/company-visible output, recurring investment-process input | Escalate to `quant-develop`; add tests, logging, contracts, review |
| 4 | Live trading, irreversible operations, regulatory/safety critical | Do not rely on this skill; require external controls and approvals |

## Workflow

1. Classify the task as exploration, daily helper, or candidate project.
2. Identify the smallest useful output: CSV, chart, Markdown table, JSON, or
   notebook cell result.
3. Use existing data/API skills first when relevant, especially
   `zmdata-data-api`, `wisdom-manager-product-research`, or `fund-wiki`.
4. Write the simplest maintainable Python that solves the research question.
5. Add cheap safeguards:
   - check row counts, date ranges, missing values, duplicate keys, and units
   - print or log a small sample of the final result
   - save outputs with clear names when the user needs artifacts
   - avoid overwriting important files without confirmation
6. Run a fresh verification before saying the work is complete.

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
- survivorship and sample filters: state what universe was used
- benchmark and fee assumptions: make them visible
- NAV/return frequency: confirm daily, weekly, monthly, or irregular
- missing data and outliers: report counts and handling
- turnover, transaction costs, and capacity: include when relevant
- output schema: columns, units, and date format are clear

## Escalation

Escalate to `quant-develop` when:

- the script will run repeatedly or be used by other people
- outputs enter portfolio construction, monitoring, IC/client materials, or
  downstream systems
- failure needs logging, alerting, retries, contracts, or access control
- there is a stable data contract or a need for `project.yaml`, `registry/`, or
  `workflows/`

Escalate to `old-coder` only for high-assurance modules where the user asks for
proof/evidence or the code can directly cause high-impact harm.
