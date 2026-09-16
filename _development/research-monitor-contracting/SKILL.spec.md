---
name: research-monitor-contracting
description: Use when research reports, papers, or notes must be converted into a source-traceable monitoring specification before implementation.
status: draft
stage: specification-and-validation
not_published: true
---

# Research Monitor Contracting

> Draft only. This file is a specification draft for validation and routing review.
> It is intentionally **not** published as a formal `SKILL.md` yet.

## Purpose

`research-monitor-contracting` is a bridge skill between research understanding and
engineering implementation.

It translates research materials into a **source-traceable monitoring contract**
that downstream skills can implement in QuantSystem.

It does **not** implement data collection, factor code, HTML pages, tests, or git
delivery by itself.

## Draft Layout vs Published Layout

This specification directory is for design and validation only.

Draft-stage files may include:

```text
research-monitor-contracting/
├── SKILL.spec.md
├── VALIDATION.spec.md
└── evals/
```

If this skill is later published, the runtime-facing structure should be slimmer:

```text
research-monitor-contracting/
├── SKILL.md
├── references/
└── evals/
```

Rules:

- `SKILL.spec.md` and `VALIDATION.spec.md` are review artifacts, not future runtime
  instruction files.
- `evals/` may remain for validation, but should not be written as mandatory runtime
  reading material.
- project-specific adaptations belong outside the core skill directory unless they
  become reusable cross-project references.

## Trigger Boundary

Use this skill only when the user's intent is to turn research content into a
monitoring-ready contract, such as:

- converting research views into monitorable logic
- turning research materials into rules, evidence indicators, or data requirements
- preparing a handoff package for a future QuantSystem monitoring project
- defining what must be implemented before `quant-develop`, `public-data-collector`,
  or `frontend-report-page` starts work

The following mentions alone are not sufficient to trigger this skill:

- a report or paper
- indicators or factors
- monitoring or dashboards
- HTML or report output

Do **not** use this skill for:

- ordinary summaries of reports or papers
- source replication or reproducibility audits
- one-off research calculations or factor code
- data source implementation or crawler work
- HTML beautification or report layout polishing
- direct QuantSystem project implementation
- situations where the user explicitly wants to skip contracting and go straight to
  code or project buildout

## Routing Boundary

| Scenario | Primary Skill |
| --- | --- |
| research materials to monitoring contract | `research-monitor-contracting` |
| source method review, reproducibility, replication gaps | `investment-paper-replication` |
| formal QuantSystem project implementation | `quant-develop` |
| lightweight calculations or research code | `quant-research-coding` |
| public data access or new source ingestion | `public-data-collector` |
| final report HTML implementation | `frontend-report-page` |

If the source materials contain unresolved methodological conflicts, missing core
definitions, or contradictory causal claims that block downstream contracting,
route first to `investment-paper-replication` or another source-review workflow.
This skill must not silently arbitrate major source disputes.

If a monitoring contract is already confirmed and the user asks to build the system,
route downstream instead of re-entering this skill.

## Scope

This skill is responsible for:

- extracting verifiable claims from research materials
- forming logic cards from those claims
- distinguishing rules, observation frameworks, and background narrative
- specifying evidence indicators and data requirements
- identifying automation boundaries and manual review items
- producing a structured downstream handoff contract
- defining the information contract that the eventual HTML report must express

This skill is not responsible for:

- API integration
- crawler implementation
- database writes
- factor computation code
- final HTML/CSS/JS coding
- project scaffolding, tests, or git flow

The preferred stopping point is a validated `handoff_contract`, not implementation.

## Core Object Model

The contract must be organized around the following objects:

```text
source_claim
logic_card
monitoring_rule
evidence_spec
data_gap
handoff_contract
```

### Field-level status dimensions

A single information-state enum previously mixed three orthogonal concerns. This
draft splits them into three dimensions so a gap is never misread as a single kind.

```yaml
definition_status:   exact | inferred | proxy
availability_status: available | latest_only | missing | unavailable
verification_status: verified | unverified | unknown | not_stated
```

Semantics:

- `definition_status` describes how a value relates to its source definition:
  - `exact`: the source states it explicitly
  - `inferred`: derived from context, not stated verbatim
  - `proxy`: a substitute stands in for the original definition
- `availability_status` describes whether the value can be obtained now:
  - `available`: obtainable
  - `latest_only`: only the latest value is available
  - `missing`: required but absent
  - `unavailable`: known to exist but not currently obtainable

`unavailable` refers to the target data being unobtainable; it does not mean all
related data is absent (a proxy may still exist).
- `verification_status` describes whether the value's existence or content has been confirmed:
  - `verified`: confirmed
  - `unverified`: present but not yet confirmed
  - `unknown`: the source does not mention it
  - `not_stated`: the source is silent on whether it exists

These dimensions are orthogonal: one object may be, for example,
`definition_status: proxy`, `availability_status: available`, and
`verification_status: verified` at the same time. Do not treat `proxy`, `missing`,
and `unknown` as the same kind of gap.

Rules:

- never present `unknown` / `unavailable` / `not_stated` as if the value were exact
- `definition_status: proxy` must carry `interpretation_loss` when it replaces an original metric
- `latest_only`, `missing`, `unavailable`, and `unverified` must remain visible, never hidden
- a field with `not_stated` or `unknown` must not be silently upgraded to a hard rule

### source_claim

Represents a traceable source-level statement extracted from research material.

Required fields:

```yaml
source_claims:
  - claim_id:
    title:
    source_type: report | paper | note | appendix
    source_title:
    source_author_or_org:
    source_date:
    locator:
      page:
      section:
      paragraph:
    claim_text:
    claim_role: logic | threshold | formula | backtest_result | caveat
    confidence_note:
```

### logic_card

Represents the first-class monitoring object.

Required fields:

```yaml
logic_cards:
  - logic_id:
    display_name:
    proposition:
    mechanism:
    implication:
    applicability_boundary:
    failure_mode:
    classification: rule_based | observation_framework | narrative_background
    primary_stage:
    covered_stages: []
    source_claim_ids: []
    evidence_evaluation:
      state_vocabulary: []
      support_evidence_ids: []
      falsify_evidence_ids: []
      context_evidence_ids: []
      aggregation_policy:
      conflict_policy:
      insufficient_data_policy:
```

### evidence_evaluation

Defines how a logic's current state is derived from its evidence. It lives on
`logic_card` because the aggregation rule is a stable research-definition concern,
not a runtime reading.

Required fields:

```yaml
evidence_evaluation:
  state_vocabulary: []
  support_evidence_ids: []
  falsify_evidence_ids: []
  context_evidence_ids: []
  aggregation_policy:
  conflict_policy:
  insufficient_data_policy:
```

Field notes:

- `state_vocabulary`: the allowed logic-level states, e.g. `supported`,
  `falsified`, `conflicted`, `insufficient`, `pending_manual`, `not_evaluated`.
  This is distinct from `monitoring_rule.state_mapping`, which describes whether a
  formal rule is triggered.
- `support_evidence_ids` / `falsify_evidence_ids` / `context_evidence_ids`: which
  `evidence_spec` items play each role for this logic.
- `aggregation_policy`: how multiple evidence items combine (e.g. `all_required`,
  `any_required`, `weighted`, `analyst_judgment`).
- `conflict_policy`: how a support/falsify coexistence is resolved (e.g.
  `conflicted_if_support_and_falsify_coexist`).
- `insufficient_data_policy`: the state used when evidence is missing or
  unavailable (default `insufficient`).

Rules:

- the current state must be produced by this evaluation contract, not hardcoded
  into `logic_card`
- `state_vocabulary` must be an explicit closed set, so downstream projects do not
  each invent their own "supported" / "conflicted" semantics

### logic_evidence_snapshot

Represents a runtime reading, separated from the stable logic definition.

```yaml
logic_evidence_snapshots:
  - logic_id:
    as_of_date:
    current_evidence_state:
    supporting_evidence_ids: []
    falsifying_evidence_ids: []
    unresolved_items: []
```

Rules:

- `current_evidence_state` must be one of the values in the linked
  `evidence_evaluation.state_vocabulary`
- `as_of_date` is required so the snapshot is point-in-time
- `logic_evidence_snapshots` is a runtime output, not part of the static
  `logic_card` definition

### monitoring_rule

Represents explicit monitorable judgment logic only when the source supports it.

Required fields:

```yaml
monitoring_rules:
  - rule_id:
    logic_id:
    rule_type: explicit_rule | observation_only
    decision_direction:
    aggregation_method:
    threshold_source: source | engineering_proxy | none
    threshold_note:
    conditions: []
    falsifiers: []
    manual_items: []
    state_mapping:
      triggered:
      not_triggered:
      pending_manual:
      insufficient:
```

### evidence_spec

Represents evidence requirements. It is not tied to a specific table layout.

Required fields:

```yaml
evidence_specs:
  - evidence_id:
    logic_id:
    linked_rule_ids: []
    indicator_name:
    evidence_role: supports | falsifies | context
    data_kind: series | derived_series | composite | event | observation
    source_label:
    normalized_definition:
    transform:
    unit:
    frequency:
    required_date_semantics:
    formula_source: source | engineering_proxy | none
    implemented_formula_note:
    threshold_reference:
    automation_status: automated | semi_automated | manual | unavailable
```

### data_gap

Represents data limitations and fallback governance.

The three status dimensions describe the state of the linked object's target data,
not the fallback. They are orthogonal and may all apply at once.

Required fields:

```yaml
data_gaps:
  - gap_id:
    linked_object_type: logic_card | monitoring_rule | evidence_spec
    linked_object_id:
    definition_status: exact | inferred | proxy
    availability_status: available | latest_only | missing | unavailable
    verification_status: verified | unverified | unknown | not_stated
    source_attempts:
      - source:
        result:
        reason:
    fallback:
      type:
      replacement:
      interpretation_loss:
      user_decision_required: true
    notes:
```

### handoff_contract

Represents a structured downstream implementation contract.

The contract is a **proposal**, not a final `project.yaml`. It carries the
bridge-level intent that this skill can determine, and explicitly lists which
project control fields remain for `quant-develop` or the user to fill in.

Required fields:

```yaml
handoff_contract:
  downstream_owner:
  target_scope:
    domain:
    project_id:
  proposed_stage: idea | research | candidate | production | monitor_only | retired
  output_type: status_alert | action_config | research_report
  decision_use: research | internal_decision | portfolio_input | production
  cadence:
  required_entrypoints:
    research: true | false
    publish: true | false
    monitor: true | false
  deliverables:
  implementation_constraints: []
  acceptance_checks: []
  deferred_fields: []
```

Field notes:

- `downstream_owner`: the skill expected to implement the contract (e.g., `quant-develop`).
- `target_scope`: proposed domain and project identifier for downstream placement.
- `proposed_stage`: proposed lifecycle stage; values align with the shared lifecycle contract (`idea → research → candidate → production → monitor_only → retired`), not a custom closed set.
- `output_type`: whether the project emits status/alert, action/config, or a research report.
- `decision_use`: how the output is consumed; a separate axis from `output_type`.
- `cadence`: proposed update frequency as free text (e.g., `daily`, `monthly`, `event_driven`, `ad_hoc`, `custom`); not a closed enum.
- `required_entrypoints`: which runtime entrypoints the downstream must expose.
- `deliverables`: concrete artifacts the downstream must produce.
- `implementation_constraints`: non-negotiable implementation constraints.
- `acceptance_checks`: actionable acceptance criteria.
- `deferred_fields`: project control fields this skill cannot determine and that `quant-develop` or the user must fill in (e.g., `owner`, `status`, `data_dependencies`, `input_contract`, `output_contract`, `consumers`).

`unresolved_items` and `user_decisions_required` are **not** repeated inside
`handoff_contract`; they are top-level output fields and remain the single
authoritative location.

## Logic Extraction Rules

The skill must extract logic before extracting indicators.

For every candidate logic:

1. identify the core proposition
2. explain the mechanism, not only the conclusion
3. define what supports the logic
4. define what could falsify the logic
5. identify boundaries and failure modes
6. decide whether the logic is:
   - `rule_based`
   - `observation_framework`
   - `narrative_background`

Rules:

- A logic is first-class; factors are evidence, not the core object.
- A background narrative must not be silently upgraded into a monitoring rule.
- An observation framework may describe what to watch without forcing thresholds.
- A rule requires explicit source support for its decision method.

## Rule, Threshold, and Composite Handling

### Rules

- If the source gives an explicit rule, summarize and preserve it.
- If the source does not give an explicit rule, downgrade it to observation.
- Do not invent thresholds merely to make the project feel complete.

### Thresholds

- Preserve source thresholds when clearly provided.
- If a threshold is adapted, mark it explicitly as non-source.
- Threshold provenance must always be visible.

### Composite indicators

- If the source defines the construction, reproduce that method at the contract level.
- If the source names a composite view but does not define construction, mark the
  composite as incomplete.
- Engineering equal-weight defaults are allowed only as explicit proxy treatment,
  never as disguised source truth.

### Formula provenance

- `formula_source` records where the formula or derivation method comes from, not
  where the indicator name comes from. A metric named in the source does not imply
  the source provided its formula.
  - `source`: the source states a locatable calculation or derivation.
  - `engineering_proxy`: an explicit proxy calculation is proposed to stand in for
    an undefined original.
  - `none`: only the indicator name is given with no calculation method, or the
    value is used directly as a raw series with no derived formula.
- `formula_source: none` does not by itself mean the definition is missing; judge a
  definition gap together with `normalized_definition` and
  `implemented_formula_note`, not `formula_source` alone.

## Stage Taxonomy

Stages are configurable lifecycle dimensions, not fixed universal classes.

The skill must support a configurable taxonomy. The example below is intentionally
domain-neutral:

```yaml
stage_taxonomy:
  assessment:
    label: Current State Assessment
  activation:
    label: Condition Activation
  review:
    label: Risk Review
```

Rules:

- `stage_taxonomy` is a map of unique `stage_id -> { label }`; each `label` is
  non-empty
- every logic must declare `primary_stage` and `covered_stages`
- `primary_stage` and `covered_stages` must reference ids already defined in
  `stage_taxonomy`, and `primary_stage` must be a member of `covered_stages`
- a stage not covered by a logic must be treated as undefined, not untriggered
- downstream HTML may group by `primary_stage` and tag `covered_stages`
- stage names, count, order, and display are project-configured, never hardcoded
  in the core skill

## Data Governance Rules

This skill defines required data semantics and disclosure rules, not collection order
implementation.

Mandatory rules:

- never silently replace exact series with proxy series
- never present a proxy as if it were the original source definition
- never hide latest-only or unverified limitations
- every missing source attempt must record result and reason
- every fallback must record interpretation loss
- user approval is required when a fallback materially changes interpretation

The skill may include project-level source preference examples, but must not hardcode
a universal mandatory fetch order across all domains.

## HTML Information Contract

This skill defines what the eventual HTML must express. It does not define the final
visual implementation.

### Required information

- logic is the first-class object
- each logic must expose proposition, state, and evidence
- each indicator must be attached to a support, falsify, or context role
- date, unit, source status, and proxy status must be visible where relevant
- manual-review items must be distinguishable from evidence-insufficient items
- only actually covered stages may appear in a logic detail section
- static HTML must remain readable without a server
- keyboard navigation and print-safe degradation must be possible

### Not core-skill hard rules

The following belong to project-level profiles or reference implementations, not the
core skill contract:

- fixed column counts or column names for indicator tables
- fixed navigation layout (e.g., sidebar placement, card ordering)
- specific interaction patterns (e.g., hash-based routing, click-to-jump)
- project-specific color semantics or status palettes
- domain-specific stage labels or navigation structures

## Standard Output Contract

The output must be structurally inspectable. At minimum, it must contain:

```yaml
source_claims:
logic_cards:
monitoring_rules:
evidence_specs:
data_gaps:
logic_evidence_snapshots:
handoff_contract:
user_decisions_required:
unresolved_items:
```

Each logic must be able to answer:

- what is the claim
- why the mechanism should work
- what supports it
- what can falsify it
- how the evidence is defined
- where thresholds come from
- definition, availability, and verification status of the current data
- what can be automated
- what still requires manual judgment
- what downstream implementation is required

The preferred deliverable shape is structured output. Free-form prose may explain the
contract, but must not replace the contract fields above.

## Baseline Failure Modes

Without this skill, the agent is likely to make the following mistakes:

- extract a flat factor list without rebuilding logic cards
- turn observation language into hard rules
- invent thresholds that the source never provided
- treat proxy data as equivalent to original data
- mix source review, data collection, implementation, and HTML coding into one step
- freeze one project's layout or stage semantics into universal rules
- produce handoff notes as loose prose rather than structured contract fields

The eventual published skill must explicitly guard against these errors.

## Pressure Scenarios

The draft must be validated against at least these scenarios before publication:

1. **Single report, partial rules**
   - a report provides logic and evidence but no thresholds
   - expected behavior: create logic cards and observation frameworks, do not invent rules

2. **Multiple reports, conflicting thresholds**
   - two sources disagree materially on thresholds or interpretations
   - expected behavior: surface conflict and route to source review, do not resolve silently

3. **Only proxy data available**
   - the desired evidence exists only through a proxy
   - expected behavior: record proxy status, interpretation loss, and user decision requirement

4. **Strong narrative, weak evidence**
   - a source offers persuasive macro narrative but no operational rule
   - expected behavior: classify as background or observation, not rule-based

5. **Project-specific implementation temptation**
   - a current project has polished layout, navigation, or domain-specific stage naming
   - expected behavior: keep those details outside the universal core contract

6. **User asks to skip contracting**
   - user explicitly wants direct code or project implementation
   - expected behavior: route downstream instead of expanding this skill beyond its boundary

## Acceptance Criteria

This draft is ready to become a formal `SKILL.md` only when all checks below pass:

- trigger boundary is concrete enough to avoid accidental routing
- exclusion boundary is concrete enough to avoid collision with nearby skills
- route relationship with `investment-paper-replication`, `quant-develop`,
  `public-data-collector`, and `frontend-report-page` is explicit
- every core object has a required field contract
- proxy and missing-data governance is explicit
- user decision gates are explicit
- route-in and route-out examples are covered by `evals/routing-cases.md`
- pressure behavior is covered by `evals/pressure-scenarios.md`
- a domain-neutral contract example exists in `evals/expected-contract.example.yaml`
- downstream handoff is structured rather than free-form
- project-specific HTML details are clearly separated into profile/reference layers
- pressure scenarios and baseline failure modes are covered

## Runtime Red Lines

The formal skill must fail validation if any of the following behaviors are allowed:

- proxy series are presented as exact source series
- thresholds are invented without provenance
- narrative-only claims are upgraded into rules without basis
- project-specific HTML or navigation details are promoted into universal rules
- downstream implementation guidance is expressed only as loose prose
- unresolved source conflicts are silently decided inside this skill

## Validation Assets Status

Status convention: **recorded** means the material exists; **passed** means an
actual behavior check has been executed and judged. See `VALIDATION.spec.md` for
the full record.

### Recorded

1. route-test cases — `evals/routing-cases.md` (designed, not yet behavior-tested)
2. pressure-case scenarios — `evals/pressure-scenarios.md` (designed, not yet behavior-tested)
3. structured contract example — `evals/expected-contract.example.yaml`
4. non-macro schema fixture — `evals/non-macro-sample-credit.md` (synthetic, field-level mapping recorded, not yet behavior-tested)
5. downstream-consumption review against `quant-develop` — partial pass (proposes `target_scope`, `proposed_stage`, `output_type`, `decision_use`, `cadence`, `required_entrypoints`; defers `owner`, `status`, `data_dependencies`, `input_contract`, `output_contract`, `consumers`)
6. external validation against `gold-factor-monitor` — partial pass (semantic coverage passes, contract compliance fails; deltas recorded as a handoff checklist)
7. spec-consistency structural validation — `evals/behavior-validation.md` (agent-conducted: 8 / 8 pass; real model behavior validation and independent no-skill baseline still unfinished)

## Publication Gate

`SKILL.md` is now shipped as an experimental release candidate for internal use
only (see the `EXPERIMENTAL` banner in `SKILL.md`). That internal release is
allowed.

Do **not** promote this to a production / formally shared skill until:

- a controlled A/B run is completed (same prompt, no-skill output, with-skill output, field-level judgement, raw output archived) — done
- an independent no-skill baseline is recorded — pending
- `handoff_contract` proposal/deferred split is reviewed and accepted — done
- `VALIDATION.spec.md` and `evals/expected-contract.example.yaml` are in sync with this file — done

Current status:
- spec design passed（规格设计通过）
- compressed-draft review passed（压缩稿审查通过）
- controlled A/B pilot passed（受控 A/B pilot 通过）
- contract revision passed（契约修订通过）
- targeted regression 7 / 7 passed（针对性回归 7 / 7 通过）
- independent no-skill baseline not done（独立无 skill 基线未完成）
- cross-domain real-world validation limited（跨领域真实验证有限）
- release candidate for internal use; formal verification still incomplete（内部试用 release candidate，正式验证仍不完整）
