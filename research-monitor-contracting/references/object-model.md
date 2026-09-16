# Object Model Field Contract

> Reference for `SKILL.md`. Defines the full field-level contract for each object
> in the monitoring contract. This is reference material, not runtime instruction;
> `SKILL.md` points here for field details.

## Field-level status dimensions

A single information-state enum previously mixed three orthogonal concerns. This
contract splits them into three dimensions so a gap is never misread as a single kind.

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

Wording discipline:

- keep the three dimensions separate; never rewrite a `verification_status`
  observation as an `availability_status` value.
- `available + unverified` = the value is present but not yet confirmed; do not
  phrase it as `missing`.
- `missing + unknown` = required but absent, and the source does not mention it;
  this is not the same as `unavailable + not_stated`.
- `unavailable + not_stated` = the target is known to exist but currently
  unobtainable, and the source is silent; do not collapse it into "proxy data
  available but not yet confirmed".

## stage_taxonomy

Top-level map of stage ids to display labels. It is a project-configured lifecycle
dimension, not a fixed universal classification.

```yaml
stage_taxonomy:
  <stage_id>:
    label: <non-empty display label>
```

Rules:

- each `stage_id` is unique
- `label` must be non-empty
- `logic_card.primary_stage` and `logic_card.covered_stages` must reference ids
  already defined in `stage_taxonomy`
- `primary_stage` must be a member of the same logic's `covered_stages`
- the number, names, order, and display of stages are decided by the project, not
  by this skill

## source_claim

Represents a traceable source-level statement extracted from research material.

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

## logic_card

Represents the first-class monitoring object.

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

## evidence_evaluation

Defines how a logic's current state is derived from its evidence. It lives on
`logic_card` because the aggregation rule is a stable research-definition concern,
not a runtime reading.

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

## logic_evidence_snapshot

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

Contracting-stage semantics:

- this skill defines the snapshot structure and the `evidence_evaluation` rules,
  but does not infer a live reading during contracting
- when no runtime data has been evaluated yet, `current_evidence_state` must be
  `not_evaluated` and the supporting/falsifying id lists stay empty
- the actual `supported` / `falsified` / `conflicted` / `insufficient` states are
  produced downstream at monitor time, not baked into the static contract

## monitoring_rule

Represents explicit monitorable judgment logic only when the source supports it.

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

## evidence_spec

Represents evidence requirements. It is not tied to a specific table layout.

```yaml
evidence_specs:
  - evidence_id:
    logic_id:
    linked_rule_ids: []
    indicator_name:
    evidence_role: supports | falsifies | context
    data_kind: series | derived_series | composite | event | observation
    source_label:
    source_url:            # optional source link; traceability entry, not ingestion proof
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

Field notes:

- `formula_source` records where the formula or derivation method comes from, not
  where the indicator name comes from. A metric named in the source does not imply
  the source provided its formula or derivation method.
  - `source`: the source states a locatable calculation or derivation (an
    operational definition and/or formula). Keep the traceable definition.
  - `engineering_proxy`: an explicit proxy calculation is proposed to stand in
    for an undefined original; record the proxy formula, the interpretation loss,
    and approval status.
  - `none`: only the indicator name is given with no calculation method, or the
    value is used directly as a raw series with no derived formula.
- `formula_source: none` does not by itself mean the definition is missing: a raw
  series with no derived formula is also `none`. Judge a definition gap together
  with `normalized_definition` and `implemented_formula_note`, not `formula_source`
  alone.
- `source_url` is an optional source-traceability link. It records where the data
  can be inspected, not whether the data has been ingested, can be downloaded, can
  participate in automatic judgment, or has been verified. A link must never be
  presented as proof of ingestion.
- `source_url`, `availability_status`, and `automation_status` are three orthogonal
  dimensions: `source_url` = where to inspect the source; `availability_status` =
  whether the target data can be obtained; `automation_status` = whether the value
  is programmatically ingested. A web page that is viewable but not downloadable as
  structured history is not `availability_status: available` by itself; it may still
  be `latest_only`, `unavailable`, or `unverified`. `automation_status: manual`
  means the factor must be viewed by a human and cannot default to automatic rule
  judgment.

## data_gap

Represents data limitations and fallback governance.

The three status dimensions describe the state of the linked object's target data,
not the fallback. They are orthogonal and may all apply at once.

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

## handoff_contract

Represents a structured downstream implementation contract.

The contract is a **proposal**, not a final `project.yaml`. It carries the
bridge-level intent that this skill can determine, and explicitly lists which
project control fields remain for `quant-develop` or the user to fill in.

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
