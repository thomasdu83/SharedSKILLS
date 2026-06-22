# Stress Tests

Use these scenarios when updating this skill or checking whether an agent is following it.

## Scenario 1: Narrow Reviewed Pool Mistaken For Full Universe

User asks for a market-neutral comparable-pool report. The agent finds 14 reviewed managers and starts writing a final report.

Expected behavior:

- Stop and document fund-wiki coverage.
- Run or request a full-universe recall query.
- Label the 14 managers as reviewed formal pool only if justified.
- Keep all other hits as candidates, boundary cases, or review items.

## Scenario 2: Research Report Used As Primary Evidence

User asks which managers have market-neutral products. A prior research report lists manager A as observation-pool.

Expected behavior:

- Query fact-layer profiles/indexes first.
- Report manager A as a research-layer historical conclusion unless product or manager profile evidence confirms it.
- If fact-layer evidence is missing, label A as pending review.

## Scenario 3: Ordinary Query With Research Layer Available

User asks "fund-wiki 里有哪些市场中性管理人？"

Expected behavior:

- Recall broadly from fact and research layers if available.
- Present fact-layer matches first.
- Present research-layer historical matches separately.
- Do not merge research pool levels into the fact-layer list.

## Scenario 4: Complex Research Without Project Card

User asks for a full CTA strategy taxonomy and core/observation/boundary pools.

Expected behavior:

- Draft the project card.
- Ask for confirmation before formal research.
- Do not write a final report before confirmation unless the user has already confirmed scope in the current thread.

## Scenario 5: Research Suggests Tag Fixes

Research finds a product tagged as index enhancement but materials show market neutral hedging.

Expected behavior:

- Write a review output with evidence and suggested change.
- Do not directly edit `product_profiles`.
- Distinguish confirmed fact, inference, and proposed governance action.

## Scenario 6: Research Index Is Stale

User asks to test a market-neutral research workflow. New research reports exist under `research/reports/`, but `query_fund_wiki.py` returns only older research artifacts or `research_context_budget_chars` is `0`.

Expected behavior:

- Run `build_research_index.py --json`.
- Re-run `query_fund_wiki.py ... --research-only`.
- Compare research note count and returned artifacts before/after refresh when possible.
- Report stale research index as a process/tooling gap, not as an absence of research work.

## Scenario 7: Broad Strategy Term Misread As Product Name

User asks for a strategy taxonomy with query terms such as `alpha`, `套利`, `ETF套利`, `量化对冲`, or `高频alpha`. The standard query returns `recognized_product` or a product-name `hard_filters` value and a narrow result set.

Expected behavior:

- Treat the first query as an ordinary query diagnostic, not a full-universe recall.
- Re-run the fact-layer recall with `--intent-mode research_recall` when available.
- If still noisy, aggregate from `indexes/product_profiles.jsonl` using structured strategy fields and evidence snippets.
- Record `intent_mode`, `recognized_product`, `recognized_manager`, `hard_filters`, and the structured aggregation rule.

## Scenario 8: Taxonomy Report Without Universe Artifact

User asks for a fine-grained strategy taxonomy or full comparable-pool study. The agent writes a formal report but only embeds sample-funnel counts in prose.

Expected behavior:

- Write a separate `research/universes/` artifact with `profile_type: ResearchUniverse` when the installed indexer supports it.
- Preserve recall commands, intent modes, hard filters, aggregation fields, broad/strict counts, review flags, and representative evidence paths.
- Cite the universe artifact from the formal report.
- Refresh the research index and confirm whether the universe artifact is indexed; if not supported, cite it from an indexed report or methodology note.

## Scenario 9: User Asks For 外发版 But Reader Is Internal Research Teams

User says the report is for other internal investment research teams and asks for an `外发版` or `内部流通版`.

Expected behavior:

- Treat it as `internal_circulation_report`, not an external client-ready report.
- Keep or create the internal working paper as the evidence layer.
- Derive a separate file named `<topic>_内部流通版_YYYYMMDD.md` under `research/reports/`.
- Remove raw UNC/local paths, command lines, index filenames, hard-filter diagnostics, and raw query logs from the body.
- Preserve the strategy framework, conclusions, risk boundaries, and plain-language methodology.
- Add an internal-use disclaimer.
- Do not put named managers/products in the main text by default.

## Scenario 10: Internal Circulation Version Names Products Too Freely

User asks for a version that can be shared with other teams. The working paper contains a formal pool with named managers and products.

Expected behavior:

- Default to no named managers/products in the main text.
- Use anonymous or category examples unless the user explicitly asks for names.
- If names are included, place them in an appendix, require evidence grade A/B, exclude material review flags, and mark them as examples rather than recommendations.
- Do not imply investment advice, product recommendation, performance promise, or allocation instruction.
