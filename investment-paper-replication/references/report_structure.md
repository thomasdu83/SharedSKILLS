# Report Structure

Use this structure for Markdown or HTML reports. Keep language professional, evidence-led, and investment-oriented.

## Executive Summary

- One-paragraph answer: what the source claims, what replication/adaptation found, and whether it matters for investment practice.
- Include confidence level and the largest caveat.

## Source Claim

- Research question.
- Economic intuition.
- Claimed edge or risk insight.
- Original sample, market, frequency, and benchmark.

## Replication Design

- Target figures/tables.
- Data sources and substitutions.
- Variable definitions.
- Portfolio construction or model estimation rules.
- Transaction costs and constraints.
- Known ambiguities.

## Results

- Core replicated metrics.
- Comparison with source findings.
- Directional match or mismatch.
- Explanation of differences.

## Robustness

- Subperiods.
- Parameter sensitivity.
- Alternative universe or benchmark.
- Cost sensitivity.
- Out-of-sample or recent-period decay.

## Investment Interpretation

- Is this an alpha signal, allocation input, risk monitor, manager selection lens, or research-only insight?
- Where it fits in the user's investment workflow.
- Recommended usage frequency and decision owner.

## Risks and Limitations

- Data quality.
- Look-ahead and survivorship bias.
- Capacity and turnover.
- Crowding and regime dependence.
- Implementation cost and maintenance burden.

## Next Steps

- What to validate next.
- Whether to build an HTML report, web prototype, or production system.
- What must be confirmed before using it in live investment decisions.

## Writing Rules

- Use conclusion-led section titles when possible.
- Label each key statement as source claim, replication/adaptation evidence, or investment interpretation.
- Prefer tables for assumptions, variable definitions, and source-versus-replication comparisons.
- Do not overstate causality if the source or replication only supports correlation.
- When the user needs polished research prose, apply `research-report-writer` after this evidence structure is stable. Do not polish away caveats, uncertainty, or implementation limits.
