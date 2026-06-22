# Strategy Taxonomy

`fund-wiki` uses a two-layer strategy tagging model.

## Evidence Layer

The evidence layer preserves source wording from due-diligence materials:

- `strategy_raw_terms`: raw matched strategy expressions.
- `strategy_evidence`: source sentences or fragments supporting the tag.
- `candidate_strategy_tags`: plausible but not yet standardized tags that need review.
- `mentioned_strategy_tags`: strategy words that appeared in the same source material but are not direct product tags.
- `rejected_strategy_tags`: tags removed by product-scope guardrails, such as CTA terms appearing in a pure index-enhancement product note.

This layer is intentionally not forced into one rigid vocabulary. It keeps manager-specific wording available for review and future taxonomy expansion.

## Normalized Tag Layer

The normalized layer is a stable, query-friendly vocabulary:

- `primary_strategy_codes` / `primary_strategy_tags`: broad strategy families.
- `secondary_strategy_codes` / `secondary_strategy_tags`: more specific strategy variants.
- `strategy_facets`: orthogonal attributes such as benchmark, instrument, horizon, return engine, and risk shape.
- `strategy_tag_confidence`: `high`, `medium`, or `low`.
- `strategy_tag_review_status`: `confirmed` or `needs_review`.
- `direct_strategy_tags`: query-facing labels directly supported by product-level evidence.

Primary tags should remain relatively stable. Secondary tags and facets can evolve as new fund strategy language appears.

## Current Primary Tags

- `EQ_LONG`: 股票多头
- `EQ_INDEX_ENH`: 指数增强
- `EQ_NEUTRAL`: 市场中性
- `CTA`: 管理期货
- `ARB`: 相对价值
- `VOL`: 期权波动率
- `FI`: 债券信用
- `MACRO_MULTI`: 宏观多资产
- `FOF_MOM`: 组合基金
- `EVENT`: 事件驱动
- `OTHER_REVIEW`: 待确认

## Query Behavior

Natural-language queries are expanded through the taxonomy before scoring. For example:

- `管理期货` expands toward `CTA` and CTA aliases.
- `1000指增` expands toward `指数增强`, `中证1000指增`, and benchmark facets.
- `商品CTA` expands toward `管理期货` and commodity/futures facets.

Query responses should expose both evidence and normalized tags. The normalized layer improves recall and grouping; the evidence layer remains the basis for final wording.

When a product has both index-enhancement and CTA language in the same source note, use product-scope evidence first. Terms that are only manager-level or same-document mentions should stay in `mentioned_strategy_tags` or `rejected_strategy_tags`, not in primary product tags.
