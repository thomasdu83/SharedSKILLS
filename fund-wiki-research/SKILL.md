---
name: fund-wiki-research
description: Use when the user asks for a fund-wiki based investment research topic or report, including manager/product comparable pools, strategy taxonomy, sample funnels, evidence grading, core/observation/boundary pools, research SOP, review of prior fund-wiki research outputs, internal circulation versions for other investment teams, or research artifacts under fund_profile_wiki_docs/research.
---

# Fund Wiki Research

## Purpose

Use this skill to run standardized investment research workflows on top of `fund-wiki`. It turns fund-wiki facts, profiles, and prior research artifacts into reproducible research outputs without letting derived research judgments overwrite the underlying evidence layer.

This skill depends on `fund-wiki` for data retrieval, profile evidence, and docs-root conventions. Use `fund-wiki` directly for raw material deposit, profile generation, index refresh, ordinary product/manager lookup, and health or review-queue maintenance.

Default output is an internal research working paper. When the user explicitly asks for `外发版`, `内部流通版`, `给其他投研团队看`, `可分发报告`, or `给同事看的版本`, create an internal circulation version derived from the research working paper. In this skill, `外发版` means internal cross-team circulation unless the user clearly says external client distribution.

## Core Rule

Prefer broad recall and strict attribution:

```text
Recall-first: query both fact and research layers when useful.
Evidence-layered: always separate fact-layer evidence from research-layer conclusions.
Fact-grounded: formal conclusions must be grounded back to product_profiles, manager_profiles, indexes, or source_notes.
```

Research artifacts are derived knowledge. They can provide history, hypotheses, sample pools, prior classifications, and review leads, but they must not be treated as primary evidence for product strategy facts or silently written back into `product_profiles` / `manager_profiles`.

## Use Fund-Wiki First

For every research task that depends on fund-wiki coverage, first run or request the standard fund-wiki query path:

```powershell
python scripts\query_fund_wiki.py "<research recall query>" --limit 100 --json
```

Use `manager_results` for manager-level discovery and `results` for product-level evidence. If the user asks for a full-universe study, document the full fund-wiki coverage and the recall query before writing conclusions.

For taxonomy, full-universe, comparable-pool, or other recall-heavy research, prefer the explicit research recall mode when available:

```powershell
python scripts\query_fund_wiki.py "<broad recall terms>" --limit 100 --context-budget 40000 --json --intent-mode research_recall
```

Research recall mode is for evidence discovery, not formal membership. If the normal query returns a surprising `recognized_product`, product-name `hard_filters`, or obviously narrow results for a broad strategy term such as `alpha`, `套利`, `ETF套利`, `量化对冲`, or `高频alpha`, rerun with `--intent-mode research_recall` and/or aggregate directly from `indexes/product_profiles.jsonl` using normalized fields (`primary_strategy_tags`, `secondary_strategy_tags`, `direct_strategy_tags`, `product_line`, `strategy_facets`, evidence snippets). Label this as structured index aggregation.

For recall-first research, also refresh and query the research layer:

```powershell
python scripts\build_research_index.py --json
python scripts\query_fund_wiki.py "<research topic + comparable pool terms>" --limit 100 --context-budget 40000 --json --research-only
```

If the normal fact-layer query returns a `research_index_jsonl` path but `research_context_budget_chars` is `0`, do not assume prior research was searched. Run the explicit `--research-only` query above and report the number of research artifacts returned.

Record these two layers separately:

```text
Fact-layer query hits:
Research-layer artifacts:
Stale or refreshed research index:
Intent mode and hard filters:
Structured index aggregation, if used:
```

For full-universe, strategy taxonomy, or comparable-pool work, write the sample funnel or universe snapshot as a separate artifact under `research/universes/` in addition to any formal report. It should preserve query commands, structured filter rules, counts, and review flags so the research can be reproduced.

## Complex Research Gate

For complex topics, stop after drafting the project card and wait for user confirmation before formal research. Complex topics include:

- comparable pools
- strategy taxonomy or fine-grained strategy classification
- core pool / observation pool / boundary pool
- formal research reports
- all-library or full-universe coverage
- research SOP design or research process review

Project card fields:

```text
Research title:
Reader:
Use case:
Research object:
Fund-wiki coverage scope:
Recall query:
Expected deliverables:
Out of scope:
Acceptance criteria:
```

If the user has already confirmed these fields in the current thread, proceed and restate the assumptions.

## Evidence Layers

When querying, it is acceptable to inspect more than one layer. When answering, keep them separate:

```text
Fact layer:
  source_notes, product_profiles, manager_profiles, indexes

Research layer:
  research/reports, research/universes, research/evidence_packets, research/methodology

Governance layer:
  research/review_outputs, review_queue, overrides
```

If a name appears in research artifacts but not in fact-layer results, label it as a research-layer lead or pending review. If a name appears in fact-layer results but not in prior research, label it as a new fact-layer candidate not covered by historical research.

## Standard Outputs

For research reports aimed at internal investment research readers, include:

1. One-page conclusion
2. Research scope and reader use case
3. Fund-wiki universe and recall result
4. Sample funnel
5. Evidence grading rules
6. Strategy taxonomy or segmentation
7. Formal pool, observation pool, boundary or excluded pool
8. One-sentence research judgment per manager or product
9. Key uncertainties and data-quality issues
10. Appendix with evidence and artifact paths

For an internal circulation version aimed at other investment research teams, preserve conclusions and research usefulness while removing database workflow traces:

1. Executive conclusion
2. Research scope in plain language
3. Strategy taxonomy or framework
4. Why the framework matters for comparison or allocation
5. Main risks, boundary conditions, and uncertainty
6. Optional anonymous or strictly qualified examples
7. Internal-use disclaimer

Do not include raw internal paths, command lines, index filenames, verbose query diagnostics, or unreviewed sample-funnel mechanics in the circulation version. Keep the internal working paper and universe artifact as the reproducible evidence layer.

For detailed procedures and templates, read only the needed references:

- `references/research-sop.md` for the step-by-step SOP
- `references/report-template.md` for report structure and wording standards
- `references/internal-circulation-template.md` for internal cross-team circulation versions
- `references/artifact-spec.md` for file locations, frontmatter, and evidence-layer rules
- `references/stress-tests.md` for scenario tests before updating this skill

When writing research artifacts that must be searchable by the fund-wiki research index, include both the research artifact fields and the indexer-compatible `profile_type` field:

```yaml
profile_type: ResearchReport      # reports/
profile_type: Methodology         # methodology/
profile_type: InsightCard         # insight_cards/
profile_type: ResearchUniverse    # universes/ when supported by the installed indexer
```

If the installed indexer does not yet support `ResearchUniverse`, still write the universe artifact under `research/universes/` and cite it from the report's `source_profile_paths` or `derived_from`.

## Red Lines

- Do not present `research/` conclusions as confirmed product strategy facts.
- Do not use a prior research report to prove the same report's conclusion.
- Do not call a reviewed sample pool a full-library conclusion unless the universe was actually recalled and documented.
- Do not merge fact-layer hits and research-layer classifications in one list without labels.
- Do not modify raw due-diligence materials.
- Do not directly rewrite `product_profiles` or `manager_profiles` from a research conclusion; produce a review output instead.
- Do not call an internal circulation version a client-ready external report unless the user explicitly asks for external distribution and required compliance wording/scope has been confirmed.
