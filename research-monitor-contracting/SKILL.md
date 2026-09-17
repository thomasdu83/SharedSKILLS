---
name: research-monitor-contracting
description: Use when research reports, papers, or notes must be converted into a source-traceable monitoring specification before implementation.
---

# Research Monitor Contracting

> EXPERIMENTAL — release candidate for internal use. The contract is stable and
> passed targeted regression, but an independent no-skill baseline and
> cross-domain real-world validation are not yet complete. Not a production
> skill.

## When to Use

Use this skill only when the intent is to turn research content into a
monitoring-ready contract, such as:

- converting research views into monitorable logic
- turning research materials into rules, evidence indicators, or data requirements
- preparing a handoff package for a future QuantSystem monitoring project
- defining what must be implemented before `quant-develop`, `public-data-collector`,
  or `frontend-report-page` starts work

Mentions alone are not enough to trigger this skill. A report, a set of indicators,
monitoring, or HTML output by itself does not imply contracting.

## When Not to Use

- ordinary summaries of reports or papers
- source replication or reproducibility audits
- one-off research calculations or factor code
- data source implementation or crawler work
- HTML beautification or report layout polishing
- direct QuantSystem project implementation
- situations where the user explicitly wants to skip contracting and go straight to
  code or project buildout

## Routing

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

For a new QuantSystem factor-monitoring project, a confirmed contract hands off to
`ai-quant-development-router`. That router decides whether the next implementation
stage is lightweight research or formal `quant-develop` engineering. This skill does
not create the project, collect data, implement factor code, or build the frontend.

## Core Method

1. Extract verifiable claims first (`source_claim`).
2. Form `logic_card` from those claims; logic is the first-class object, and factors
   are evidence, not the core object.
3. Classify each logic as `rule_based`, `observation_framework`, or
   `narrative_background`.
4. Specify evidence requirements (`evidence_spec`) and data gaps (`data_gap`).
5. Produce a structured `handoff_contract`.

Rules:

- a background narrative must not be silently upgraded into a monitoring rule
- an observation framework may describe what to watch without forcing thresholds
- a rule requires explicit source support for its decision method

### Thresholds and composites

- preserve source thresholds when clearly provided
- if a threshold is adapted, mark it explicitly as non-source; provenance must always be visible
- do not invent thresholds merely to make the plan feel complete; downgrade to observation instead
- composite indicator: reproduce the source construction if defined; if named but
  undefined, mark it incomplete
- engineering equal-weight defaults are allowed only as explicit proxy treatment,
  never as disguised source truth
- `formula_source` records where a formula or derivation method comes from, not
  where the indicator name comes from: a metric named by the source does not imply
  the source provided its formula. `none` covers both "no method given" and "raw
  series with no derived formula"; judge a definition gap with
  `normalized_definition` and `implemented_formula_note`, not `formula_source`
  alone (see `references/object-model.md`).

### Stages

`stage_taxonomy` is a top-level map of unique `stage_id -> { label }`. Stages are
configurable lifecycle dimensions, not fixed universal classes. Every logic
declares `primary_stage` and `covered_stages`; both must reference stage ids
already defined in `stage_taxonomy`, and `primary_stage` must be a member of
`covered_stages`. An uncovered stage is treated as undefined, not untriggered.
Stage labels are always project-configured, never hardcoded in the core skill.

## Objects to Produce

```text
source_claim
logic_card
monitoring_rule
evidence_spec
data_gap
logic_evidence_snapshot
handoff_contract
```

Key constraints (full field contract in `references/object-model.md`):

- `logic_card` is a stable research definition; the current evidence state is a
  runtime reading, kept in `logic_evidence_snapshots` and derived through
  `evidence_evaluation`. During contracting, do not infer a live reading — the
  snapshot defaults to `not_evaluated` with empty supporting/falsifying id lists.
- data state uses three orthogonal dimensions — `definition_status`,
  `availability_status`, `verification_status`; never collapse `proxy`, `missing`,
  and `unknown` into one kind of gap.
- `unresolved_items` and `user_decisions_required` are top-level output fields, not
  nested inside `handoff_contract`.

## Data Governance

- never silently replace exact series with proxy series
- never present a proxy as if it were the original source definition
- never hide latest-only or unverified limitations
- every missing source attempt must record result and reason
- every fallback must record interpretation loss
- user approval is required when a fallback materially changes interpretation

Do not hardcode a universal mandatory fetch order across all domains.

## HTML Information Contract

This skill defines the information contract only; it never implements the page.

Define what the eventual HTML must express, not its final visual implementation:

- logic is the first-class object
- each logic must expose proposition, state, and evidence
- each indicator must attach to a support, falsify, or context role
- date, unit, source status, and proxy status must be visible where relevant
- a factor viewable only through a web page must show its source link, its
  manual-view state, and its not-auto-ingested state; it must not be rendered as
  ingested structured data, and it must not default to participating in automatic
  rule judgment
- manual-review items must be distinguishable from evidence-insufficient items
- only actually covered stages may appear in a logic detail section
- static HTML must remain readable without a server
- keyboard navigation and print-safe degradation must be possible

The following belong to project-level profiles or reference implementations, not
the core skill contract: fixed column counts or names, fixed navigation layout,
specific interaction patterns, project-specific color semantics, and domain-specific
stage labels.

## Output Contract

The output must be structurally inspectable. At minimum it must contain:

```yaml
stage_taxonomy:
source_claims:
logic_cards:
monitoring_rules:
evidence_specs:
data_gaps:
logic_evidence_snapshots:   # runtime slot; static contract stage defaults to not_evaluated
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

The preferred deliverable shape is structured output. Free-form prose may explain
the contract, but must not replace the contract fields above.

## Runtime Red Lines

The skill must fail validation if any of the following behaviors are allowed:

- proxy series are presented as exact source series
- thresholds are invented without provenance
- narrative-only claims are upgraded into rules without basis
- project-specific HTML or navigation details are promoted into universal rules
- downstream implementation guidance is expressed only as loose prose
- unresolved source conflicts are silently decided inside this skill

## References

- `references/object-model.md` — full field-level contract for each object
