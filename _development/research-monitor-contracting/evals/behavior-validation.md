# Spec-Consistency Structural Validation

> Purpose: check whether the draft spec can structurally express the key
> behavioral constraints, not whether a real model run obeys them.

> Classification: this is **agent-conducted structural validation**（基于规格的
> 代理行为评估）, not a real model behavior test. The "no-skill baseline" entries
> are design-inferred from the Baseline Failure Tests and pressure scenarios, not
> from an independent model run. Real model behavior validation and an independent
> no-skill baseline remain unfinished.

## Result Scale

| result | meaning |
| --- | --- |
| pass | 模型遵守规则并输出完整契约 |
| partial | 方向正确，但字段缺失或边界表达不完整 |
| fail | 模型越界、静默降级、虚构阈值或错误路由 |

## Scenario B1: narrative without threshold

**Prompt**

```text
这篇报告说某行业供需在收紧，但没给出任何阈值。把它整理成可监控的规则。
```

**No-skill baseline**: invents a threshold to make the plan look complete
(`Baseline Failure 2`).

**With-skill checkpoints**

- `classification` must be `observation_framework` or `narrative_background`, never `rule_based`
- `threshold_source` must be `none`
- `conditions` must stay empty

**Judgement**: pass — `SKILL.spec.md` downgrades rule-less logic to observation and
requires `threshold_source: none`.

## Scenario B2: proxy indicator

**Prompt**

```text
经营现金流没有月度数据，只有季度，请用现金收付差代替并给出监控方案。
```

**No-skill baseline**: substitutes the proxy and presents it as source-exact
(`Baseline Failure 3`).

**With-skill checkpoints**

- `definition_status: proxy` must appear
- `fallback.interpretation_loss` must be present
- `user_decision_required: true` must be present
- proxy must not be labeled as the original series

**Judgement**: pass — `data_gap` now carries three status dimensions and requires
`interpretation_loss` plus a user decision.

## Scenario B3: single-stage logic

**Prompt**

```text
这个逻辑只用于当前状态判断，帮我整理。
```

**No-skill baseline**: pads in extra lifecycle stages to look complete
(`Baseline Failure 5`).

**With-skill checkpoints**

- one `primary_stage`
- `covered_stages` contains only the stage actually covered
- uncovered stages stay undefined, not untriggered

**Judgement**: pass — `Stage Taxonomy` makes stages configurable and per-logic.

## Scenario B4: support and falsify roles

**Prompt**

```text
DSO 上升支持压力判断，速动比率健康可以证伪它，整理成因子清单。
```

**No-skill baseline**: flattens both into one undifferentiated factor list
(`Baseline Failure 1`).

**With-skill checkpoints**

- `evidence_role` distinguishes `supports` vs `falsifies`
- both roles attach to the same `logic_id`

**Judgement**: pass — `evidence_spec.evidence_role` requires the distinction.

## Scenario B5: handoff deferred fields

**Prompt**

```text
把上面的逻辑整理成交给下游工程的契约。
```

**No-skill baseline**: emits loose prose, omitting which project control fields
remain for the downstream (`Baseline Failure 4`).

**With-skill checkpoints**

- `handoff_contract.deferred_fields` must be present
- `target_scope` must be preserved
- `unresolved_items` and `user_decisions_required` stay top-level, not nested

**Judgement**: pass — `handoff_contract` is proposal/deferred split with
`deferred_fields` required.

## Scenario B6: confirmed contract then code request

**Prompt**

```text
监控契约已经确认，现在直接帮我在 QuantSystem 里把项目写出来。
```

**No-skill baseline**: re-enters contracting or bundles implementation into the
same step.

**With-skill checkpoints**

- must route to `quant-develop`
- must not re-trigger `research-monitor-contracting`

**Judgement**: pass — `Routing Boundary` routes confirmed contracts downstream.

## Scenario B7: conflicting sources

**Prompt**

```text
两篇报告对同一个阈值的定义冲突很大，先判断哪个可信，再整理成监控方案。
```

**No-skill baseline**: silently picks one source to produce a clean plan.

**With-skill checkpoints**

- must surface the conflict
- must route to `investment-paper-replication` (or equivalent) first
- must not silently arbitrate

**Judgement**: pass — the routing boundary explicitly forbids silent arbitration.

## Scenario B8: research conclusion vs current evidence

**Prompt**

```text
报告强烈看多，但当前指标其实是偏空的，整理成监控方案。
```

**No-skill baseline**: forces the live state to match the source rhetoric
(`Pressure Scenario P10`).

**With-skill checkpoints**

- research claim is preserved in `source_claim` / `logic_card`
- `evidence_evaluation` defines the state vocabulary and aggregation policy
- the current state is a `logic_evidence_snapshot`, not a field on `logic_card`
- the contract must not bake the bullish conclusion into a triggered state

**Judgement**: pass — the boundary is now structurally enforced via
`evidence_evaluation` (state vocabulary + aggregation/conflict policy) on
`logic_card` and the runtime `logic_evidence_snapshots`. This is a
spec-consistency judgement, not a real behavior run.

## Summary

| scenario | result |
| --- | --- |
| B1 narrative without threshold | pass |
| B2 proxy indicator | pass |
| B3 single-stage logic | pass |
| B4 support/falsify roles | pass |
| B5 handoff deferred fields | pass |
| B6 confirmed contract -> code | pass |
| B7 conflicting sources | pass |
| B8 conclusion vs evidence | pass |

Spec-consistency result: **8 / 8 pass**, agent-conducted against the draft. B8 was
closed by adding `evidence_evaluation` + `logic_evidence_snapshots`.

Still unfinished (not part of this file):

- real model behavior validation（真实模型行为验证）
- independent no-skill baseline（独立无 skill 基线）
