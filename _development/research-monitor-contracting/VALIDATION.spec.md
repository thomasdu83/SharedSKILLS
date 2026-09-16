# Research Monitor Contracting Validation Draft

> This file is part of the pre-publication validation package for
> `research-monitor-contracting`.
>
> It is not a runnable skill file. It exists to test routing, failure modes, and
> output expectations before a formal `SKILL.md` is published.

## Validation Goals

This draft validates five questions:

1. Can the skill be routed distinctly from nearby skills?
2. Does it avoid overreaching into data collection, engineering, or frontend work?
3. Does it produce structured monitoring contracts rather than loose summaries?
4. Does it preserve source traceability and proxy disclosure?
5. Does it stop when user judgment is required instead of silently completing risky gaps?

## Route Conflict Tests

Each case below should be used as a routing decision test before publication.

### Case 1: Pure summary request

**Prompt**

```text
请帮我总结这篇黄金研究报告的核心观点和结论，不需要转成监控方案。
```

**Expected route**

- `research-monitor-contracting`: no
- likely direct analysis or `research-report-writer`

**Why**

The user only wants summary, not a monitoring contract.

### Case 2: Source reproducibility audit

**Prompt**

```text
请检查这篇研报里的四因子方法能否复现，哪些公式和样本区间没有交代清楚。
```

**Expected route**

- `investment-paper-replication`: yes
- `research-monitor-contracting`: no

**Why**

The task is source audit and reproducibility review, not handoff design.

### Case 3: Monitoring contract design

**Prompt**

```text
把这几篇黄金研报中的判断逻辑、证据指标、阈值来源和人工确认项整理成后续监控项目可实施的契约。
```

**Expected route**

- `research-monitor-contracting`: yes

**Why**

This is the canonical target use case.

### Case 4: QuantSystem implementation

**Prompt**

```text
根据已经确认的黄金监控方案，把项目在 QuantSystem 里正式实现出来。
```

**Expected route**

- `quant-develop`: yes
- `research-monitor-contracting`: no

**Why**

The contract is already assumed to exist; the task is implementation.

### Case 5: Public data source onboarding

**Prompt**

```text
请把这个海外公开 API 接进平台数据层，并把序列写入 macro.db。
```

**Expected route**

- `public-data-collector`: yes
- `research-monitor-contracting`: no

**Why**

The task is collection and onboarding, not monitoring contract definition.

### Case 6: HTML presentation work

**Prompt**

```text
把现有监控结果整理成一个更适合读者阅读的静态 HTML 报告。
```

**Expected route**

- `frontend-report-page`: yes
- `research-monitor-contracting`: no

**Why**

The task is report implementation and presentation.

### Case 7: Mixed but unresolved source conflict

**Prompt**

```text
两篇报告对同一个黄金拥挤度阈值的定义冲突很大，你先帮我判断哪个更可信，再整理成监控方案。
```

**Expected route**

- first `investment-paper-replication` or equivalent source-review path
- `research-monitor-contracting` only after the source conflict is reviewed

**Why**

This skill must not silently arbitrate major source contradictions.

## Baseline Failure Tests

These are the likely failure modes without the new skill.

### Failure 1: Flat factor extraction

**Likely wrong behavior**

- extracts a list of indicators
- misses logic cards
- misses falsification paths
- misses manual-review boundaries

**Expected correction**

- rebuild around `logic_card` first

### Failure 2: Invented thresholds

**Likely wrong behavior**

- source gives narrative only
- agent adds thresholds to make the plan look complete

**Expected correction**

- downgrade to observation framework
- record that thresholds are absent

### Failure 3: Silent proxy substitution

**Likely wrong behavior**

- exact source unavailable
- agent substitutes a proxy
- presents it as if source-exact

**Expected correction**

- record `definition_status: proxy`
- state interpretation loss
- require user decision when material

### Failure 4: Over-bundled workflow

**Likely wrong behavior**

- starts discussing crawlers, HTML code, factor implementation, and git flow in the same step

**Expected correction**

- stop at `handoff_contract`
- route downstream work to the right skill

### Failure 5: Project profile leakage

**Likely wrong behavior**

- copies the current gold project's four stages, fixed tables, and navigation into universal rules

**Expected correction**

- move these details into profile/reference layer

## Pressure Scenarios

These scenarios test whether the draft skill behaves safely under ambiguity or pressure.

### Scenario A: One report, missing formulas

**Input**

- one sell-side report
- explicit logic
- no exact formula for composite indicator
- strong recommendation language

**Expected behavior**

- create `source_claims`
- create `logic_cards`
- mark composite evidence as incomplete or engineering-proxy candidate
- do not treat the recommendation itself as a monitoring rule
- add unresolved item for missing formula

### Scenario B: Multiple reports, mixed evidence quality

**Input**

- three reports
- one gives thresholds
- one gives only narrative
- one gives a backtest claim with missing sample notes

**Expected behavior**

- preserve all traceable claims separately
- distinguish source-backed rule from observation-only logic
- record backtest evidence as source claim, not unquestioned truth
- surface evidence-quality differences

### Scenario C: Only latest value available

**Input**

- evidence series available only as current reading
- no long history for threshold or percentile

**Expected behavior**

- mark `availability_status: latest_only`
- avoid percentile-based rule design unless explicitly supported
- mark inability to build historical-state monitoring if required

### Scenario D: User pressures for fast completion

**Input**

```text
先别管这些来源差异，直接帮我整理成一套完整规则，后面再说。
```

**Expected behavior**

- refuse silent compression of missing provenance
- keep unresolved items visible
- separate explicit rule, observation, and proxy treatment

### Scenario E: Beautiful HTML temptation

**Input**

- project already has a polished HTML layout
- user asks for a reusable generic skill

**Expected behavior**

- keep only generic information contract in the core draft
- preserve layout specifics as project profile reference

## Expected Output Shape

Any successful contracting run should be checkable against the following skeleton:

```yaml
source_claims:
  - claim_id:
    claim_role:
    source_title:
    locator:

logic_cards:
  - logic_id:
    proposition:
    mechanism:
    implication:
    classification:
    primary_stage:
    covered_stages:
    source_claim_ids:
    evidence_evaluation:
      state_vocabulary:
      support_evidence_ids:
      falsify_evidence_ids:
      context_evidence_ids:
      aggregation_policy:
      conflict_policy:
      insufficient_data_policy:

monitoring_rules:
  - rule_id:
    logic_id:
    rule_type:
    threshold_source:
    conditions:
    manual_items:

evidence_specs:
  - evidence_id:
    logic_id:
    evidence_role:
    data_kind:
    frequency:
    automation_status:

data_gaps:
  - gap_id:
    linked_object_id:
    definition_status:
    availability_status:
    verification_status:
    fallback:
      user_decision_required:

logic_evidence_snapshots:
  - logic_id:
    as_of_date:
    current_evidence_state:
    supporting_evidence_ids:
    falsifying_evidence_ids:
    unresolved_items:

handoff_contract:
  downstream_owner:
  target_scope:
    domain:
    project_id:
  proposed_stage:
  output_type:
  decision_use:
  cadence:
  required_entrypoints:
  deliverables:
  implementation_constraints:
  acceptance_checks:
  deferred_fields:

user_decisions_required:
unresolved_items:
```

## Field-Level Acceptance Checks

### source_claims

- each claim must have a traceable locator
- claim role must be explicit
- unsupported claims must not be promoted downstream

### logic_cards

- every logic must answer proposition, mechanism, implication
- every logic must state classification
- every logic must declare stage coverage
- every logic must carry `evidence_evaluation` (state vocabulary, support/falsify
  evidence ids, aggregation policy, conflict policy, insufficient-data policy)

### monitoring_rules

- every explicit rule must cite source-backed decision logic
- threshold provenance must be present
- manual items must be surfaced explicitly

### evidence_specs

- every evidence item must declare role: supports, falsifies, or context
- indicator definitions must not be only display-level labels
- automation status must be visible

### data_gaps

- proxy usage must be explicit
- latest-only and unverified states must not be hidden
- fallback interpretation loss must be described when relevant

### logic_evidence_snapshots

- current evidence state must carry `as_of_date`
- state must come from the logic's `evidence_evaluation` vocabulary
- supporting and falsifying evidence ids must be listed separately
- conflicting evidence must surface `unresolved_items` rather than being silently
  collapsed into a single state

### handoff_contract

- downstream owner must be explicit
- acceptance checks must be actionable
- unresolved items must remain visible

## Red Lines

The draft should be rejected for publication if any of the following happens:

- a proxy is presented as exact source data
- thresholds are invented without provenance
- narrative-only claims are converted into rules without basis
- HTML project details are promoted into universal core rules
- downstream implementation instructions are left as only free-form prose
- source conflicts are silently resolved inside this skill

## Validation Assets Status

Status convention: **recorded** means the material exists; **passed** means an
actual behavior check has been executed and judged. The behavior validation below
is agent-conducted, not an independent model run: the no-skill baseline is
design-inferred, and the with-skill check is a structural self-check against the
draft rules.

### Recorded

1. route-test cases — `evals/routing-cases.md` (designed, not yet behavior-tested)
2. pressure-case scenarios — `evals/pressure-scenarios.md` (designed, not yet behavior-tested)
3. structured contract example — `evals/expected-contract.example.yaml`
4. non-macro schema fixture — `evals/non-macro-sample-credit.md` (synthetic, field-level mapping recorded, not yet behavior-tested)
5. downstream-consumption review against `quant-develop` — partial pass, see below
6. external validation against `gold-factor-monitor` — partial pass, see below
7. spec-consistency structural validation — `evals/behavior-validation.md` (agent-conducted: 8 / 8 pass, see below)

### Downstream-consumption review (`quant-develop`)

Reviewed `handoff_contract` against `quant-develop`'s `project.yaml` contract.

**Result**: partial pass. The bridge contract now proposes project placement
(`target_scope`), lifecycle intent (`proposed_stage`), output shape
(`output_type`), decision use (`decision_use`), frequency (`cadence`), and
entrypoints (`required_entrypoints`). It does **not** supply every
`project.yaml` control field; `quant-develop` must still fill in `owner`,
`status`, `data_dependencies`, `input_contract`, `output_contract`, and
`consumers` at project initialization. These are recorded in
`handoff_contract.deferred_fields`.

### External validation (`gold-factor-monitor`)

Validated the generic object model against the gold-factor-monitor
`preregistration.yaml` as an external sample.

**Result**: partial pass.

| judgement | result |
|---|---|
| semantic coverage (can the sample be expressed?) | pass |
| contract compliance (does the sample satisfy the generic contract?) | fail |
| migration / supplementation required | yes |
| does this invalidate the generic rules? | no |

The sample is leaner than the generic contract in these places:

- source attribution is at institution-name level, not fine-grained `locator`
- `logic_detail` covers proposition/mechanism/implication but omits
  `classification`, `applicability_boundary`, and `failure_mode`
- rules omit explicit `threshold_source` and `state_mapping`
- factors do not carry an explicit `evidence_role` (supports/falsifies/context)
- no standalone `data_gap` object exists (limitations are spread across
  `manual_items` / `manual_inputs`)

These deltas are recorded as a handoff checklist, not as changes to the generic
core rules. A macro-domain sample alone is insufficient to prove generality
across fund, industry, credit, supply-chain, or operating-metric domains.

### Non-macro schema fixture (`credit`)

Mapped a credit / operating-metric **synthetic schema fixture**
(`evals/non-macro-sample-credit.md`) through the generic object model to test
structural generality beyond macro. This is **not** a real external source sample:
it cannot validate source authenticity, locator reliability, or real-world
ambiguity handling, so it is ranked below the `gold-factor-monitor` external sample.

**Result**: field-level mapping recorded (not yet behavior-tested).

| feature under test | result |
| --- | --- |
| single-stage logic | expressible via `primary_stage` / `covered_stages` |
| observation framework | expressible via `classification: observation_framework` |
| proxy / missing data | expressible via `definition_status` / `availability_status` |
| support + falsify roles | expressible via `evidence_role` |
| source traceability | expressible via `locator` (page / section / paragraph) |

This fixture deliberately covers one stage, contains no explicit threshold, uses a
monthly cash-flow proxy, and assigns both a support role (DSO, operating cash flow)
and a falsify role (quick ratio) to the same logic. Handoff is allowed with the
usual `deferred_fields` and one `user_decisions_required` item.

A frequency mismatch is recorded as a pressure-validation checkpoint
(`source_frequency: quarterly` vs `requested_monitoring_frequency: monthly`), not
as a new object-model field yet.

## Round Assessment

| dimension | judgement |
| --- | --- |
| `info_status` design | pass (split into `definition_status` / `availability_status` / `verification_status`) |
| `data_gap` structure | pass (three status dimensions + `fallback` + `user_decision_required`) |
| `evidence_evaluation` + `logic_evidence_snapshots` | pass (logic definition and runtime state are separated) |
| domain generality | structural pass; real external evidence still limited |
| routing design | spec-consistency structural validation: B6 / B7 pass |
| pressure scenarios | spec-consistency structural validation: B1-B5, B8 pass |
| structural validation overall | 8 / 8 pass (agent-conducted structural validation, not a real model behavior test) |
| real model behavior validation | not done |
| independent no-skill baseline | not done |
| formal publication | not approved yet |

## Behavior Validation Protocol

Behavior validation checks whether the skill constrains **behavior** (does the
model obey the rules), not whether the model returns a fixed answer.

Three results:

```text
通过（pass）: 模型遵守规则并输出完整契约
部分通过（partial）: 方向正确，但字段缺失或边界表达不完整
失败（fail）: 模型越界、静默降级、虚构阈值或错误路由
```

Minimum key scenarios to cover:

1. 研究只有叙事、没有阈值时，不得生成 `rule_based`
2. 代理指标出现时，必须同时出现代理状态和 `interpretation_loss`
3. 一个逻辑只覆盖一个阶段时，不得自动补齐其他阶段
4. 指标同时具有支持和证伪角色时，不能压平成普通因子列表
5. `handoff_contract` 必须保留 `deferred_fields`
6. 已确认监控契约后要求写项目代码时，应路由给 `quant-develop`
7. 资料来源冲突时，不得由本 skill 静默裁决
8. 当前数据与研究结论冲突时，必须分别保留研究主张和实时证据状态

### Remaining before formal `SKILL.md`

The `evidence_evaluation` / `logic_evidence_snapshots` boundary (B8) is now
structurally enforced, so it no longer needs to be recorded as a known
limitation. The following remain before a formal runtime `SKILL.md`:

1. run a controlled A/B behavior validation:
   - one shared test prompt;
   - an actual model run **without** the skill (or without its rules);
   - an actual model run **with** the skill (or equivalent rules);
   - field-level judgement;
   - archive raw outputs and failure reasons.
2. run an independent no-skill baseline to confirm the design-inferred
   `Baseline Failure Tests` errors (rather than inferring them).
3. after the above pass, compress `SKILL.spec.md` into a runtime `SKILL.md`
   (keep trigger/routing/object model/data governance/red lines in the core;
   keep validation records in `evals/`; move detailed YAML field tables and
   long background notes to `references/`).
