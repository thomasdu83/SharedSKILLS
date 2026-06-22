# Research Artifact Specification

Research artifacts must live under the resolved `fund_profile_wiki_docs/research/` root.

## Directory Layout

```text
research/
  reports/              # Human-readable formal reports
  universes/            # Query universes, sample funnels, pool tables
  evidence_packets/     # Manager/product evidence packets
  methodology/          # SOPs, taxonomies, grading rules
  review_outputs/       # Suggested profile/tag/review-queue changes
```

Do not write research artifacts into `product_profiles`, `manager_profiles`, `source_notes`, or `indexes`.

## Artifact Types

| Type | Location | Purpose |
|---|---|---|
| `research_report` | `research/reports/` | Final or draft narrative report |
| `internal_circulation_report` | `research/reports/` | Derived report for internal cross-team research sharing |
| `research_universe` | `research/universes/` | Full recall result, sample funnel, pool table |
| `evidence_packet` | `research/evidence_packets/` | Evidence bundle for one manager, product, or strategy |
| `methodology_note` | `research/methodology/` | Taxonomy, grading, SOP, scope definition |
| `review_output` | `research/review_outputs/` | Suggested fixes to tags, aliases, profile quality, or review queue |

Indexer-compatible profile types:

| Location | `profile_type` |
|---|---|
| `research/reports/` | `ResearchReport` |
| `research/universes/` | `ResearchUniverse` |
| `research/evidence_packets/` | `EvidencePacket` |
| `research/methodology/` | `Methodology` |
| `research/insight_cards/` | `InsightCard` |
| `research/review_outputs/` | `ReviewOutput` |

Older installed indexers may only support `ResearchReport`, `InsightCard`, and `Methodology`. In that case, still write `ResearchUniverse` / `EvidencePacket` / `ReviewOutput` artifacts in the right folder and cite them from an indexed report or methodology note.

## Required Frontmatter

```yaml
---
artifact_type: research_report
profile_type: ResearchReport
research_type: strategy_taxonomy
research_topic: <topic_id>
topic: <Chinese topic>
title: <title>
status: draft
review_status: draft
conclusion_status: draft_research_classification
as_of_date: YYYY-MM-DD
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
docs_root: <path>
evidence_policy: fact_layer_primary_research_layer_derived
not_primary_evidence: true
---
```

For universe or evidence packet artifacts, add:

```yaml
profile_type: ResearchUniverse
research_type: universe_recall
recall_query: <query>
intent_mode: research_recall
recognized_product: <value or none>
recognized_manager: <value or none>
hard_filters: []
structured_aggregation: true
aggregation_fields:
  - primary_strategy_tags
  - secondary_strategy_tags
  - direct_strategy_tags
  - product_line
  - strategy_facets
fact_layer_count: <number or unknown>
research_layer_count: <number or unknown>
review_required: true
```

For a universe artifact, include a sample funnel table and enough filter rules to reproduce each count. If a formal report quotes a universe count, cite the universe artifact path in `source_profile_paths` or `derived_from`.

For internal circulation artifacts, add:

```yaml
artifact_type: internal_circulation_report
profile_type: ResearchReport
research_type: internal_circulation
reader: internal_investment_teams
use_case: cross_team_research_sharing
distribution_scope: internal_research_teams_only
derived_from:
  - research/reports/<working-paper>.md
evidence_policy: working_paper_primary_circulation_derived
not_primary_evidence: true
```

Internal circulation artifacts must not include raw internal paths, command lines, index filenames, or query-debug fields in the body. Keep those in the working paper or universe artifact.

## Evidence Layer Labels

Use these labels in reports and tables:

```text
Fact-layer confirmed
Fact-layer candidate
Research-layer lead
Research-layer historical conclusion
Governance/review item
Excluded or out of scope
```

If a research-layer lead has no fact-layer support, never promote it above `Research-layer lead`.

## Review Outputs

When research suggests profile or tag changes, write a review output with:

```text
Subject:
Suggested change:
Current fact-layer evidence:
Research-layer source:
Reason:
Risk if applied automatically:
Recommended human review:
```

The research skill can propose corrections. The fund-wiki governance workflow decides whether to apply them.
