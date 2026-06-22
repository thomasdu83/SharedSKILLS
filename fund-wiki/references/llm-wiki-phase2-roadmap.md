# Fund Wiki Phase 2 Roadmap Inspired by LLM Wiki

## Positioning

`llm-wiki` is a general-purpose persistent wiki system. `fund-wiki` should not copy it wholesale. The fund-wiki target is narrower:

- keep raw diligence files read-only;
- compile manager, product, strategy, people, risk, and evidence into stable wiki docs;
- query these compiled docs and indexes from Trae chat at low cost;
- stay portable as a team-shared skill.

The right direction is to borrow lifecycle, governance, lint, and relationship-index ideas while avoiding a heavy desktop app or mandatory vector stack.

## Already Adopted

- Read-only raw source layer.
- Generated markdown wiki layer.
- `source_notes` as evidence notes.
- `product_profiles` as LLM-readable product pages.
- JSONL and SQLite indexes for query.
- Source manifest instead of default raw-file copying.
- Changed-only ingest by source hash.
- Source catalog with file priority.
- Manager-level middle-layer docs:
  - `manager_profiles`
  - `product_maps`
  - `risk_flags`
  - `timelines`
- Profile quality report for duplicate or generic product names.
- Stale lock recovery.
- Progress logs under `run_logs\runs`.
- Wiki governance docs: `fund_wiki_purpose.md`, `fund_wiki_schema.md`, `index.md`, `overview.md`, and `log.md`.
- Health check reports: `reports\health_check.json` and `reports\health_check.md`.
- Relationship index: `indexes\relations.jsonl` and `indexes\relations.sqlite`.
- Relation-assisted query scoring for product line, exposure constraint, people background, and source-note relations.
- Query context budget fields: `context_budget_chars`, `used_context_chars`, `truncated_result_count`, and per-result packed evidence fields.
- Human review queue: `review_queue\open.jsonl`, `review_queue\open.md`, and `review_queue\resolved.jsonl`.
- Source lifecycle visibility through manifest-derived health issues such as `source_missing`, `source_parse_failed`, and `source_note_missing`.
- Chinese lexical query expansion with synonyms and CJK bigrams; embeddings remain optional and off by default.

## P0: Reliability Before Expansion

Goal: every standard deposit command must either complete source notes, profiles, and indexes, or return a clear JSON partial-success status.

Tasks:

- Ensure `deposit_manager.py` drains child `stdout` and `stderr` concurrently so large ingest JSON cannot block after `ingest done`.
- Log child process return code, stdout length, stderr length, and JSON parse status.
- Require stage logs for:
  - `deposit start`
  - `ingest start`
  - `ingest subprocess returned`
  - `ingest json_parse done`
  - `build_profiles start/done`
  - `build_index start/done`
  - final status
- Keep one manager lock per docs root and manager.
- Add diagnostics when an existing same-manager process is detected.
- Treat `source_notes > 0` plus `manager_product_profiles == 0` as `partial_success_profile_missing`.

Acceptance:

- A successful manager deposit returns JSON with `manager_source_notes > 0`, `manager_product_profiles > 0`, and `manager_index_records > 0`.
- A partial run returns a JSON status and exits; it must not hang after source notes are written.
- Run log contains enough stage lines to locate the stalled phase.

## P1: Wiki Governance Files

Goal: give fund-wiki a visible, LLM-readable operating contract.

Add docs-root governance files:

- `fund_wiki_purpose.md`: what the wiki is for, target queries, evidence standards.
- `fund_wiki_schema.md`: page types, frontmatter fields, product-name rules, evidence rules.
- `index.md`: global content map for managers, product lines, indexes, and quality state.
- `overview.md`: current global summary of coverage and major strategy families.
- `log.md`: append-only operation log with parseable headings.

Recommended log heading format:

```text
## [YYYY-MM-DD HH:MM] deposit | <manager> | <status>
```

Acceptance:

- Every deposit updates `log.md`.
- `index.md` can answer which managers and product profile folders exist.
- `overview.md` can show coverage by strategy type and missing profile risks.

## P1: Domain Lint And Health Check

Goal: make quality problems explicit instead of burying them in logs.

Add a `fund_wiki_health_check.py` or equivalent command that checks:

- source notes exist but product profiles are missing;
- product profiles exist but index records are missing;
- duplicated canonical product names;
- generic product names such as strategy names being treated as real products;
- manager alias collisions;
- missing source evidence;
- empty or weak `strategy_positioning`;
- empty `key_people_summary`;
- empty `risk_points`;
- outdated profiles relative to newer source notes;
- malformed frontmatter;
- broken source note references;
- failed OCR or encrypted PDFs in high-priority source files.

Output:

- JSON report under `reports\health_check.json`;
- concise markdown report under `reports\health_check.md`;
- optional review queue entries for high-severity issues.

Acceptance:

- A query-ready manager has no high-severity health issue.
- Generic product-name warnings are grouped by manager and canonical name.
- The report distinguishes `warning` from `info`.

## P1: Relationship Index

Goal: make fund relationships first-class query assets.

Build a lightweight relation index, not a visual graph:

- manager -> product
- product -> product line
- product -> strategy type
- product -> benchmark/index exposure
- product -> industry/style exposure constraints
- manager/product -> key people
- people -> background tags
- product -> source notes
- source note -> raw source path/hash

Suggested output:

```text
indexes\relations.jsonl
indexes\relations.sqlite
```

Example relation:

```json
{"subject":"平方和","predicate":"has_product","object":"平方和中证1000指数增强","evidence":["..."],"confidence":"confirmed"}
```

Acceptance:

- Compound queries such as `1000指增 + 行业暴露3%以内 + WorldQuant背景` can be evaluated by relationship fields before free-text fallback.
- Query output can explain which condition matched which evidence.

## P2: Query Context Budget

Goal: control cost and improve answer stability as profiles grow.

Status: implemented as lightweight JSON query context packing without adding vector database dependencies.

Borrow the `llm-wiki` context budget idea:

- reserve response space;
- cap total retrieved profile text;
- cap per-profile text;
- rank profiles by hard-filter match, evidence quality, update recency, and profile quality;
- include governance files only when useful;
- include manager-level docs before raw source notes.

Suggested behavior:

1. query JSONL/SQLite;
2. apply hard filters;
3. group by manager/product line when requested;
4. pack top evidence snippets within a fixed character budget;
5. only inspect source notes for evidence drill-down or missing profile layer.

Acceptance:

- Query answers remain concise when hundreds of profiles exist.
- Hard-filter misses are reported as misses, not hallucinated matches.
- The engine can explain why top results were selected.

## P2: Review Queue

Goal: create a human-review lane for uncertain extracted knowledge.

Status: implemented through health-check-derived `review_queue\open.*` files with deterministic item IDs.

Write review items when:

- a product name is inferred rather than confirmed;
- product aliases conflict;
- a manager generates unusually many profiles;
- key fields are missing;
- source notes conflict on strategy type;
- a high-priority file failed parsing/OCR;
- the profile compiler falls back to weak heuristics.

Suggested output:

```text
review_queue\open.jsonl
review_queue\resolved.jsonl
```

Acceptance:

- Profile quality warnings create review items.
- Re-running health check does not create endless duplicates.
- Review items include manager, product, severity, reason, evidence, and suggested action.

## P2: Source Lifecycle

Goal: handle changed, deleted, and missing source files explicitly.

Status: partially implemented. Missing/failed source states are visible in health check and review queue. A destructive cleanup command remains intentionally deferred.

Tasks:

- Continue using `source_manifest.jsonl` as source truth.
- Add source-missing status when a previously seen raw file disappears.
- Mark derived source notes/profiles as stale rather than silently deleting them.
- Provide a cleanup command for intentionally removed sources.

Acceptance:

- Missing raw sources do not silently erase useful historical notes.
- Stale derived pages are visible in health check.

## P3: Optional Search Enhancement

Goal: improve recall without making embeddings mandatory.

Status: implemented for lexical synonyms, CJK bigrams, and relation-assisted matching. Embedding/hybrid search remains optional and not enabled by default.

Recommended order:

1. improve Chinese lexical search with CJK bigrams and synonyms;
2. add SQLite FTS tuning and query expansion;
3. add optional embedding/hybrid search only after lexical and relation search are stable.

Acceptance:

- Embedding is optional and off by default.
- The skill still works without extra vector database dependencies.

## Do Not Copy Wholesale

Avoid these `llm-wiki` features unless a separate product decision is made:

- full Tauri desktop UI;
- browser clipper;
- deep web research;
- mandatory LanceDB/vector DB;
- graph visualization as a core dependency;
- free-form LLM writes to arbitrary wiki paths;
- image captioning as default ingest behavior;
- multi-chat persistence inside the skill.

These would make fund-wiki heavier, slower to share, and harder to operate on network drives.

## Suggested Implementation Order

1. Finish P0 reliability.
2. Add governance files and log updates.
3. Add health check.
4. Add relation index.
5. Add query context budgeting.
6. Add review queue.
7. Add optional search enhancements.
