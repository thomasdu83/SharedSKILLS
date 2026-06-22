# Fund-Wiki Research SOP

Use this SOP for fund-wiki based investment research topics such as market-neutral manager comparable pools, CTA strategy mapping, index-enhancement sub-strategy comparisons, or reviews of prior research outputs.

## 1. Project Card

For complex research, draft this card and wait for confirmation:

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

Default reader is internal investment research staff. Default use case is strategy comparability and screening support, not investment action, unless the user says otherwise.

If the user asks for `外发版`, `内部流通版`, `给其他投研团队看`, `可分发报告`, or `给同事看的版本`, treat the reader as `internal_investment_teams` and the output as an internal circulation version. Do not treat that as external client distribution unless the user explicitly says so.

## 2. Universe Recall

Start from fund-wiki, not from handpicked samples.

Minimum recall record:

```text
Docs root:
Manager profile count:
Product profile count:
Query command:
Intent mode:
Recognized manager/product:
Hard filters:
Returned manager candidates:
Returned product candidates:
Known truncation or context limits:
```

For manager discovery, prefer `manager_results`. Treat `mixed_strategy_tags`, `tag_conflict_review_needed`, weak entity types, and missing product-level evidence as review flags.

For taxonomy, full-universe, comparable-pool, or other broad research, use `--intent-mode research_recall` when available. Research recall mode is an evidence-discovery pass: it should suppress manager/product-name hard filters and keep strategy terms broad. If the normal query reports a `recognized_product` or product hard filter for broad strategy words such as `alpha`, `套利`, `ETF套利`, `量化对冲`, or `高频alpha`, rerun in research recall mode before drawing universe conclusions.

If research recall is still noisy or narrow, aggregate directly from `indexes/product_profiles.jsonl`. Use structured fields before free text:

```text
primary_strategy_tags
secondary_strategy_tags
direct_strategy_tags
product_line
strategy_facets
entity_type / entity_confidence
profile_quality_status / review_reasons
evidence_summary / strategy_evidence
path
```

Label this output as structured index aggregation, not standard query hits.

## 2A. Research-Layer Recall

For recall-first research, refresh the research index before relying on historical research artifacts:

```powershell
python scripts\build_research_index.py --json
python scripts\query_fund_wiki.py "<topic + research terms>" --limit 100 --context-budget 40000 --json --research-only
```

Use topic terms plus research terms such as `可比池`, `核心池`, `观察池`, `边界池`, `策略细分`, `全库覆盖`, `正式报告`, or `研究结论`.

Record:

```text
Research note count after refresh:
Research-only query:
Returned research artifacts:
Top relevant reports:
Research-layer gaps:
```

If the fact-layer query output has `research_context_budget_chars: 0`, historical research was not included in that query response.

## 3. Sample Funnel

Always distinguish these levels:

```text
Full fund-wiki coverage
-> query hits
-> strong candidates
-> pending-review candidates
-> formal comparable pool
-> observation pool
-> boundary / excluded / data-governance cases
```

Never describe a reviewed subset as the whole-library conclusion.

For full-universe, taxonomy, or comparable-pool research, write a reusable universe artifact under `research/universes/`. It should include:

```text
Recall queries and intent modes
Structured aggregation fields and rules
Full coverage counts
Broad candidates
Strict candidates
Pending-review candidates
Formal / observation / boundary counts
Top review flags
Representative evidence paths
```

The formal report may summarize this funnel, but the universe artifact should preserve enough detail to reproduce the counts.

## 4. Evidence Grading

Use the strongest available evidence:

| Grade | Meaning | Typical evidence |
|---|---|---|
| A | Product-level direct evidence | Product profile explicitly states the strategy or hedging construction |
| B | Manager due-diligence evidence | Manager profile or source note clearly describes the strategy line |
| C | Weak structured evidence | Product name, strategy tag, strategy_line, or related profile fields imply the strategy |
| D | Research lead only | Prior report, broad keyword hit, or related mention without fact-layer confirmation |

Formal comparable-pool membership should normally require Grade A or B. Grade C can enter observation or review. Grade D is only a lead.

## 5. Strategy Taxonomy

Create sub-strategy categories only when they improve comparability. For each category, define:

```text
Category name:
Inclusion rule:
Exclusion rule:
Comparable dimensions:
Typical evidence:
Known ambiguity:
```

Avoid categories that merely restate noisy tags. The taxonomy should help an investment researcher compare strategy construction, not just search labels.

## 6. Research Judgment

Each manager or product row should include:

```text
Name:
Representative product:
Strategy subtype:
Pool level:
Evidence grade:
Fact-layer evidence path or query fields:
Research-layer reference, if any:
One-sentence research judgment:
Review issue:
```

The one-sentence judgment should answer "why this belongs or does not belong in the comparable set" rather than propose an investment action.

## 7. QA Before Completion

Check these before saying the report is complete:

- Reader and use case are explicit.
- Full universe and recall query are documented.
- Intent mode, recognized product/manager, and hard filters are documented for recall queries.
- Research recall or structured index aggregation was used when ordinary query hard filters narrowed broad strategy terms.
- Research index refresh and research-only recall are documented when prior research may matter.
- Query hits are separated from formal comparable-pool conclusions.
- Full-universe or taxonomy work has a `research/universes/` sample-funnel artifact, or explains why it was unnecessary.
- Fact layer and research layer are labeled separately.
- Each formal-pool entry has evidence grade A or B, or the exception is explained.
- Boundary and excluded cases have reasons.
- Research artifacts are written under `research/`.
- Suggested profile/tag changes are placed in review outputs, not silently applied.

## 8. Internal Circulation Version

Create an internal circulation version only when the user explicitly asks for one. It is a derived artifact, not a replacement for the research working paper.

Use `references/internal-circulation-template.md`.

Required transformations:

```text
Keep conclusions, taxonomy, research judgment, risk boundaries.
Rewrite fund-wiki mechanics into plain-language methodology.
Remove internal paths, command lines, index filenames, hard-filter debugging, and raw query logs.
Compress sample funnels into high-level scope disclosures.
Move named manager/product examples out of the main text unless explicitly requested.
Add internal-use disclaimer.
```

Quality checks:

- The source working paper or research artifact is cited in frontmatter `derived_from`.
- The file name uses `_内部流通版_YYYYMMDD.md`.
- The body does not expose raw UNC/local paths, shell commands, index filenames, or debug fields such as `recognized_product` / `hard_filters`.
- Any named manager/product examples are in an appendix, are evidence grade A/B, and are explicitly marked as examples rather than recommendations.
