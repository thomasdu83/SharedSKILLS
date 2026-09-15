---
name: investment-paper-replication
description: Use when auditing investment papers/reports, assessing reproducibility gaps or applying source-replication methodology. For building a new quant model it is a support to ai-quant-development-router; it is primary for source-only review.
---

# Investment Research Source Replication

Keep source claims, replication/adaptation results and investment implications separate.

| Intent | Responsibility |
|---|---|
| Read a source, list assumptions or reproducibility gaps, audit an existing replication | This Skill is primary |
| Build or materially extend a strategy/model from a paper or report | `ai-quant-development-router` is primary; this Skill supplies the source method |
| Operationalize an accepted model | `quant-develop` owns engineering |
| Format existing verified results only | `frontend-page-router`; do not repeat research |

## Minimal method

1. Identify the source, hypothesis, formulas, data, sample, frequency, costs and target results.
2. Map variables to available data; label exact replication, approximate replication or adaptation.
3. Freeze a replication specification for non-trivial work. Record missing definitions and substitutes.
4. Read [source workflow](references/source-workflow.md) before executing replication or review.
   Use [replication checks](references/replication_checklist.md) for technical evidence and
   [investment validation](references/investment_validation.md) for decision usefulness.
5. For unsettled delivery structure, prepare a preview using [delivery modes](references/deliverables.md)
   and [preview guidance](references/delivery_preview_gate.md). Reuse approval already given;
   do not impose a second approval gate on authorized work.
6. Finish with exact/approximate claims, look-ahead/survivorship/overfitting risks, costs/capacity,
   sample decay, remaining gaps and verification evidence. Research-only is a valid outcome.

Page mode and shared visual rules belong to `frontend-page-router`, not this source method.
For source-specific interaction semantics use `references/frontend_data_contract.md` and
`references/frontend_interaction_checklist.md`; prose uses `research-report-writer`.
Only load references needed by the selected task. Never add this Skill as a second orchestrator.
