# Pressure Scenarios

These scenarios test whether `research-monitor-contracting` preserves its boundary
under ambiguity, missing information, conflicting sources, and user pressure.

## Scenario P1: Single source, incomplete rules

**Situation**

- one report
- clear logic
- no explicit threshold
- no exact aggregation rule

**Expected behavior**

- create `logic_card`
- classify as `observation_framework` or partial rule
- do not invent thresholds
- record unresolved items

## Scenario P2: Multiple sources, conflicting logic treatment

**Situation**

- two or more sources discuss the same monitoring logic
- one source treats it as explicit rule
- another treats it as narrative context only

**Expected behavior**

- preserve conflict through `source_claims`
- avoid silently collapsing to one interpretation
- mark conflict for review if it blocks contract stability

## Scenario P3: Proxy indicator only

**Situation**

- no exact source indicator available
- only a proxy indicator can be identified

**Expected behavior**

- create `evidence_spec`
- mark proxy treatment explicitly in `data_gaps`
- describe interpretation loss
- require user decision if material

## Scenario P4: Narrative without executable threshold

**Situation**

- source says a regime is dangerous or favorable
- no threshold, no algorithm, no decision procedure

**Expected behavior**

- classify as observation or background
- do not upgrade into formal rule

## Scenario P5: User demands direct code

**Situation**

```text
先别管这些契约，直接给我把代码写出来。
```

**Expected behavior**

- this skill should not expand itself into implementation
- downstream route should be identified instead
- unresolved contracting risk should remain visible if it affects correctness

## Scenario P6: One logic covers only one stage

**Situation**

- one logic only supports current-state assessment
- no activation or later review stage applies

**Expected behavior**

- set one `primary_stage`
- use only relevant `covered_stages`
- do not fabricate extra lifecycle stages

## Scenario P7: One logic covers multiple stages

**Situation**

- one logic supports both current-state assessment and later risk review

**Expected behavior**

- declare one `primary_stage`
- declare multiple `covered_stages`
- preserve multi-stage semantics without forcing a fixed taxonomy

## Scenario P8: Evidence can support or falsify

**Situation**

- one indicator supports a logic in one regime
- another indicator can falsify the same logic

**Expected behavior**

- preserve `supports` vs `falsifies` distinction
- avoid flattening everything into one undifferentiated factor list

## Scenario P9: Data source unavailable, user wants progress anyway

**Situation**

- exact data unavailable
- user still wants a usable monitoring contract

**Expected behavior**

- continue contracting where possible
- record source attempts and fallback governance
- stop short of pretending the contract is fully data-complete

## Scenario P10: Research conclusion and current data disagree

**Situation**

- source conclusion is strongly bullish
- current observable evidence is neutral or adverse

**Expected behavior**

- preserve the research claim
- preserve the current evidence spec separately
- do not force the live state to match source rhetoric

## Scenario P11: Web page link mistaken for ingested data

**Situation**

- a factor is viewable only through a web page (for example a FedWatch-style tool)
- the page is not downloadable as structured history and is not programmatically
  ingested

**Expected behavior**

- record `source_url` as a traceability entry
- mark `automation_status: manual`
- do not treat the link as proof of ingestion, downloadability, verification, or
  automatic judgment
- do not mark `availability_status: available` merely because the page opens

## Pressure Assertions

Before publication, the draft should satisfy all assertions below:

- incomplete rule definitions do not become invented rules
- conflicting sources remain explicit
- proxies remain explicit
- source rhetoric does not overwrite live evidence semantics
- user pressure does not collapse unresolved items
- stage coverage remains configurable and per-logic
- a source link is a traceability entry, not proof of ingestion
