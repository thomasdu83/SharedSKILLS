---
name: fund-wiki
description: Use when the user asks to ingest/deposit/沉淀/入库/更新 fund manager due-diligence materials into fund-wiki, build LLM-readable fund/product profile wiki documents, refresh fund_profile_wiki indexes, or query/search/查询 fund-wiki by flexible natural-language criteria such as 300指增, 1000指增, CTA, WorldQuant背景, 行业暴露3%以内.
---

# Fund Wiki

## Purpose

Use this standalone skill to operate fund-wiki from Trae chat.

The skill has two main jobs:

- Deposit raw manager due-diligence materials into fund-wiki.
- Query fund-wiki for managers/products using flexible natural-language conditions.

The bundled code engine lives inside this skill:

```text
<skill_root>\engine
```

If a standalone development project exists elsewhere, it should only be used through `--project-root` or `FPW_PROJECT_ROOT`. Normal team usage should not depend on a developer-local path.

Generated wiki documents should normally live in the shared docs root:

```text
Y:\投顾管理人研究\fund_profile_wiki_docs
```

Local docs fallback for development only:

```text
%LOCALAPPDATA%\QuantSystem\fund-wiki\fund_profile_wiki_docs
```

## Common User Expressions

Map common Chinese requests to these workflows.

### Deposit One Manager

User may say:

- "请沉淀双隆的尽调材料"
- "请把双隆的尽调资料沉淀到 fund-wiki"
- "把双隆入库"
- "更新双隆的 fund-wiki"
- "重新沉淀双隆"

Use:

```powershell
python scripts\deposit_manager.py "双隆" --use-llm --provider deepseek --json
```

If the user says "重新沉淀 / 强制重跑 / 不要跳过", add `--force`.

### Deposit Multiple Managers

User may say:

- "请沉淀双隆、磐松、半鞅的尽调材料"
- "请逐个把私募1、私募2、私募3沉淀到 fund-wiki"
- "批量更新以下管理人：..."

Current behavior: run `deposit_manager.py` once per manager and summarize all JSON results. Continue to the next manager if one fails, unless the user asks to stop on failure.

Recommended per-manager command:

```powershell
python scripts\deposit_manager.py "<管理人>" --use-llm --provider deepseek --json
```

For more than five managers, tell the user this will be a batch run and summarize success / skipped / partial_success / error counts at the end.

### Query Fund-Wiki

User may say:

- "在 fund-wiki 中查询具有 300 指增的公司"
- "找 1000 指增、行业暴露 3% 以内、投资经理有 WorldQuant 背景的产品"
- "查询双隆的 CTA 产品"
- "fund-wiki 里有哪些市场中性产品"

Use:

```powershell
python scripts\query_fund_wiki.py "<查询条件>" --limit 10 --json
```

This is the default and mandatory first step for all fund-wiki query intents, including requests such as "某管理人的策略", "找某类产品", "按条件筛产品/管理人", and other natural-language retrieval tasks. Do not start by reading `source_notes` directly.

Base the chat answer on JSON fields: `product_name`, `manager`, `entity_type`, `entity_confidence`, `primary_strategy_tags`, `secondary_strategy_tags`, `direct_strategy_tags`, `mentioned_strategy_tags`, `rejected_strategy_tags`, `strategy_facets`, `matched_terms`, `missing_terms`, `hard_filter_satisfied`, `evidence_snippet`, `profile_quality_status`, `review_reasons`, and `path`.

Treat `entity_type=product` with high confidence as query-ready product evidence. Treat `product_series`, `strategy_line`, `generic_bucket`, or low-confidence entities as review-context rather than confirmed product matches.

For manager-discovery questions such as "哪些管理人有期货策略", "哪些公司做1000指增", "哪些私募有WorldQuant背景", or "哪些管理人行业暴露在3%以内", prefer the JSON `manager_results` field. Treat `results` as supporting product-level evidence. Do not manually group only the returned Top-N products, because `manager_results` is built from the full index before applying the response limit.

When `intent_mode` is `manager_filter`, answer at the manager level. Include each manager's `matched_products`, `representative_products`, `matched_strategy_tags`, `confidence`, and `review_flags` when present. If `review_flags` contains `mixed_strategy_tags` or `tag_conflict_review_needed`, describe the manager as "命中但需复核" rather than a fully confirmed match.

Strategy labels use a two-layer model. Preserve raw evidence wording through `strategy_raw_terms` / `strategy_evidence`, and use normalized `primary_strategy_tags` / `secondary_strategy_tags` / `strategy_facets` for retrieval, grouping, and routing. See `references\strategy-taxonomy.md`.

### Setup Or Check

User may say:

- "我第一次使用 fund-wiki"
- "初始化 fund-wiki"
- "检查 fund-wiki 环境"
- "为什么 fund-wiki 不能用"
- "检查 API key / 网盘 / 依赖"

Use:

```powershell
python scripts\init_fund_wiki.py --json
```

Treat this as the mandatory first step for first-run setup and migration-to-new-user scenarios. Base the chat answer on JSON fields such as `status`, `ready_for_query`, `ready_for_deposit`, `ready_for_deposit_with_llm`, `blocking_items`, `warnings`, `info_items`, `resolved_paths`, `env_candidates`, `actions_requiring_user_confirmation`, `suggested_config_writes`, and `next_actions`.

If the user confirms local setup changes, apply only low-risk skill-local defaults:

```powershell
python scripts\init_fund_wiki.py --json --apply-skill-env
```

You may also pass explicit values after the user confirms them:

```powershell
python scripts\init_fund_wiki.py --json --apply-skill-env --provider deepseek --docs-root "Y:\投顾管理人研究\fund_profile_wiki_docs" --raw-root "W:\投顾信息（PPT、尽调反馈表等）"
```

Do not auto-write API keys. Ask the user to provide or place them into the chosen `.env` file explicitly.

## Mandatory Rules

- Raw due-diligence folders are read-only evidence sources. Never edit, delete, rename, move, overwrite, or clean files under `W:\投顾信息（PPT、尽调反馈表等）`, `Z:\投顾信息（PPT、尽调反馈表等）`, or the equivalent UNC path.
- For SMB/network drives, prefer PowerShell `Test-Path` or bundled scripts over Trae `Glob`/`LS` for deep discovery. Network workspace file tools can be slow or timeout.
- Write generated artifacts only under the resolved `fund_profile_wiki_docs` root.
- Default evidence traceability is manifest-only: write `run_logs\source_manifest.jsonl`; do not copy original PDF/PPT/DOCX files into `source_snapshots`.
- Parsed text cache is local temporary state only. It must not be stored under `fund_profile_wiki_docs`, must not enter `source_manifest.jsonl`, and must not be used by query/index.
- Prefer `--json` in Trae workflows so the chat response is based on structured fields rather than free-form logs.
- For any query/search/retrieval request about fund-wiki, always run `query_fund_wiki.py --json` first. This includes "某管理人的策略", "有哪些产品", and flexible conditions such as `300指增`, `1000指增`, `CTA`, `WorldQuant背景`, or `行业暴露 3% 以内`.
- Query responses must be grounded in `product_profiles` and the actual indexes `indexes\product_profiles.jsonl` and `indexes\product_profiles.sqlite`, not guessed from raw materials.
- Product profile filenames are storage identifiers, not product identity. Different managers can have the same `product_name`, so generated files may use `<manager>__<product>.md` for disambiguation. Always read `product_name`, `manager`, `canonical_product_name`, and `path` from frontmatter/index JSON; never infer product uniqueness from the filename alone.
- Query responses should prefer normalized strategy fields when present: `primary_strategy_tags`, `secondary_strategy_tags`, `strategy_facets`, `strategy_tag_confidence`, and `strategy_tag_review_status`. Use `evidence_snippet`, `matched_terms`, `relation_matches`, and source paths to support the wording.
- Query responses must distinguish direct product strategy tags from same-material mentions. Prefer `direct_strategy_tags`; use `mentioned_strategy_tags` only as context, and call out `rejected_strategy_tags` when explaining why a candidate was downgraded.
- Do not silently downgrade a query into direct `source_notes` reading. Only inspect `source_notes` after the standard query path fails and only if one of the following is true: the index is missing, `product_profiles` do not exist yet, the user explicitly asks to inspect original diligence materials, or the user asks for deeper evidence tracing beyond profile snippets.
- If the index or `product_profiles` are missing, say so explicitly. Prefer to rebuild the index from existing `product_profiles`; if no `product_profiles` exist, explicitly tell the user that only `source_notes` exist and that a searchable fund-wiki profile layer has not been built yet.
- When answering from query results, include evidence-bearing fields such as `product_name`, `manager`, `evidence_snippet`, `path`, `matched_terms`, `missing_terms`, `relation_matches`, and `ranking_reasons`. Prefer `packed_profile_text` / `packed_evidence` for concise answers when present. Do not present a profile-style summary as if it came from the standard query path when it actually came from `source_notes`.
- Long-running deposit jobs write progress to terminal stderr and to `run_logs\runs\<run_id>.log`. Use this log to diagnose the exact file/stage if Trae reports no output for a while.
- Files whose names contain `投决会` are skipped by default because investment committee materials often mention multiple managers and products, which can pollute a single-manager profile. They should not enter the source catalog, be fingerprinted, parsed, sent to LLM extraction, or written as source notes.
- Password-protected/encrypted PDFs are skipped at source-catalog time. They should not be fingerprinted, parsed, sent to LLM extraction, or written as `Source/ParseWarning` notes.
- PDF parsing first uses layout text. OCR is used only when layout text quality is too low. OCR writes page-level progress and has a per-page timeout controlled by `FPW_OCR_PAGE_TIMEOUT_SECONDS` (default 180). If OCR is required but `pytesseract`, Tesseract, or `chi_sim` language data is missing, do not stop the whole deposit job; write a `Source/ParseWarning` note, record the file in the manifest as failed, and tell the user which OCR dependency is missing.
- If multiple manager folders match the user's manager keyword, show candidates and ask the user to choose unless one match is clearly intended.
- Do not modify `fund-track-tag-audit`; it is a separate audit skill used only as a reference pattern.

## First-Time Setup

When the user asks how to set up this skill, verify:

```powershell
python scripts\init_fund_wiki.py --json
```

At least one raw material root must be reachable. The shared docs root will be created at `Y:\投顾管理人研究\fund_profile_wiki_docs` when the Y drive parent exists.

If Python dependencies are missing, install from:

```powershell
pip install -r requirements.txt
```

OCR is optional but recommended for scanned PDFs. `check_environment.py` reports the Python package, the Tesseract executable, and Chinese/English language data separately. Missing OCR should be reported as a warning, not treated as a blocker for non-scanned materials.

The scripts auto-load `.env` files from these locations when present:

1. `--env-file <path>`
2. `FPW_ENV_FILE` or `FUND_WIKI_ENV_FILE`
3. `<skill_root>\.env`
4. `<quant_system_root>\.env`
5. `<quant_system_root>\domains\macro\external-report-macro-score\src\.env`
6. current working directory `.env`

Only variable presence is reported; secret values must never be printed.

If the LLM extraction step is requested, make sure the selected provider key exists in the environment used by Python:

- `KIMI_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY` or `CHATGPT_API_KEY`

## Deposit Workflow

Use this workflow when the user says things like:

- "请把双隆的尽调资料沉淀到 fund-wiki"
- "把某某管理人的尽调材料入库"
- "更新某管理人的 fund profile wiki"

Run:

```powershell
python scripts\deposit_manager.py "双隆" --use-llm --provider deepseek --json
```

If API keys live in a non-standard `.env`, pass it explicitly:

```powershell
python scripts\deposit_manager.py "双隆" --use-llm --provider deepseek --env-file "<path-to-env>" --json
```

For a dry run:

```powershell
python scripts\deposit_manager.py "双隆" --dry-run --json
```

Default deposit behavior:

- `--snapshot manifest`: record source path/hash in `run_logs\source_manifest.jsonl`; do not copy raw files.
- `--changed-only`: skip unchanged files by SHA-256 hash.
- `--force`: reprocess even when unchanged.
- Same-code raw folders are merged by default. If the selected folder has sibling folders with the same manager code, all same-code folders are passed into one ingest run so coverage is manager-code scoped instead of single-folder scoped.
- `--single-folder`: only ingest the selected folder and ignore same-code sibling folders. Use this only when the user explicitly asks for single-folder processing.
- `--ingest-scope all`: process all supported changed files, ordered by source catalog priority.
- `--ingest-scope priority`: process only high-value source catalog files first, such as 尽调笔记 / 尽调摘要 / 路演纪要 / 通话记录.
- `--snapshot none`: do not write manifest records.
- `--parsed-cache-root`: optional local parsed-text cache root; default resolves from `FPW_PARSED_CACHE_ROOT`, `%LOCALAPPDATA%\QuantSystem\fund-wiki\parsed_cache`, or the skill-local `.cache`.
- `--keep-parsed-cache`: keep this run's local parsed-text cache for debugging or failure recovery.
- `--run-id`: optional explicit run id; otherwise generated as `YYYYMMDD-HHMMSS_<manager>`.

The script resolves paths, finds the manager folder, merges same-code raw folders by default, sets `FPW_DOCS_ROOT`, and calls the independent project scripts in order:

1. `scripts\ingest_raw_docs.py`
2. `scripts\build_product_profiles.py`
3. `scripts\build_profile_index.py`

During ingest, fund-wiki writes a lightweight source catalog to:

```text
run_logs\source_catalog\<manager>.jsonl
```

The catalog records path, extension, date hint, hash, category, priority, and source folder so the skill can prefer high-signal materials before lower-signal raw files while preserving which raw folder each file came from.

The ingest stage reuses the catalog fingerprint during parse preparation to avoid hashing network-drive files twice. Parsed text is written to a local run-scoped cache before LLM extraction:

```text
<parsed_cache_root>\<run_id>\<manager>\*.md
```

LLM extraction reads this local parsed text first and falls back to the in-memory parse result if the cache file is unavailable. Successful or fully skipped deposits clean the run cache unless `--keep-parsed-cache` is used. Quality-only `partial_success_quality_warning` runs can also clean the run cache when there are no failed files and smoke query succeeds. Real `partial_success*` failures and `error` statuses retain the cache for recovery; old cache runs are cleaned by `FPW_PARSED_CACHE_TTL_HOURS` (default 48).

After completion, report `selected_raw_folders`, docs root, generated profile count/index path if available, `source_coverage`, and state that raw materials were not modified.

Treat `source_notes` as only the evidence-note layer. A manager deposit is fully query-ready only when the JSON output shows `manager_product_profiles > 0` and `manager_index_records > 0`. If `status` is `partial_success_profile_missing`, say clearly that raw materials/source notes were deposited but the searchable product profile layer is missing for this manager.

When `--json` is used, base the chat reply on fields such as `status`, `run_id`, `selected_raw_folders`, `raw_folder_count`, `same_code_folders_processed`, `source_coverage`, `ingest.processed`, `ingest.skipped`, `ingest.failed`, `ingest.parsed_cache_files`, `parsed_cache`, `manager_source_notes`, `manager_product_profiles`, `manager_index_records`, `manager_profile_quality`, `global_profile_quality`, `health_check`, `relation_records`, `stale_lock_recovered`, `product_profiles_total`, `manifest`, and index paths.

Quality fields are scoped. Treat `manager_profile_quality` as the current deposit task's authoritative quality signal. Treat `global_profile_quality` / `profile_quality` as whole-library diagnostics only; do not infer that the current manager has product-name or profile-quality problems from global warnings unless `manager_profile_quality.status` is `warning` and its details identify the current manager's profiles.

Profile build quality is reported in:

```text
reports\profile_quality.json
```

Index rebuilds also refresh these lightweight heuristic-enhancement artifacts:

```text
indexes\relations.jsonl
indexes\relations.sqlite
reports\health_check.json
reports\health_check.md
review_queue\open.jsonl
review_queue\open.md
review_queue\resolved.jsonl
fund_wiki_purpose.md
fund_wiki_schema.md
index.md
overview.md
log.md
```

`relations.*` stores simple subject-predicate-object links such as manager has product, product has strategy, product has risk point, product has source note, product has people background, and product has exposure constraint. Query ranking uses these relations before falling back to broad free text for compound conditions such as `1000指增 + 行业暴露3%以内 + WorldQuant背景`. `health_check.*` makes query-readiness and source-lifecycle issues visible, especially source notes without profile/index records, missing raw sources, parse/OCR failures, weak strategy positioning, missing evidence, and duplicate canonical products. `review_queue.*` is the human-review lane generated from high/warning health issues and should not contain duplicate items after repeated health checks.

Health warnings are typed. Treat `*_expected` and `*_normal` issues as informational diagnostics unless the user asks for a deep audit. Treat `*_suspicious`, `*_conflict`, and `profile_quality_short_name` as open review work. Human confirmations can be stored in `review_queue\overrides.yaml`; matching overrides with status `confirmed`, `ignored`, `resolved`, or `closed` suppress items from `review_queue\open.*` while preserving the underlying health issue in `reports\health_check.*`.

External/public web evidence is a corroboration layer, not the primary fund-wiki source of truth. Internal due-diligence materials remain the default `evidence_source_type=internal_due_diligence`. Use external evidence only for ambiguous manager aliases, short product names, ZM cross-manager suspicious candidates, people-background corroboration, duplicate product names, and other low-confidence cases. Do not search raw internal diligence snippets. Store external evidence as structured trace fields (`external_evidence`, `external_evidence_status`, `evidence_conflict_status`, `source_priority`) and never silently overwrite internal profile facts with web/search results.

External evidence governance lives in:

```text
references\external-evidence-policy.yaml
references\manager-aliases.yaml
```

Treat `external_evidence_only`, `external_evidence_low_tier`, and `external_evidence_conflict` as open review work. `third_party_public` and `search_discovery_only` evidence can support discovery, but must not be described as internally confirmed unless a due-diligence source also supports the claim.

Example override:

```yaml
overrides:
  - kind: profile_quality_short_name
    manager: 上海双隆投资有限公司
    product_name: 隆元
    status: confirmed
    note: 已人工确认该短名对应真实产品。
```

The profile build also refreshes manager-level wiki docs:

```text
manager_profiles\<manager>.md
product_maps\<manager>.md
risk_flags\<manager>.md
timelines\<manager>.md
```

These docs are generated from cleaned product profiles and are intended as fast middle-layer material for future manager overview, product map, risk, and timeline queries.

Important status meanings:

- `success`: source notes, product profiles, and index records are all present, with no profile quality warning.
- `partial_success_profile_missing`: source notes exist but the searchable profile/index layer is missing.
- `partial_success_quality_warning`: profile/index exist, but generic or duplicate product-name signals were detected.
- `partial_success`: ingest finished with file-level failures, often OCR warnings or parse warnings.

If `manager_source_notes > 0` but `manager_product_profiles == 0` or `manager_index_records == 0`, do not call the job complete. Recommend a structured rerun with LLM extraction or inspect whether the manager's source notes contain `mentioned_products_simple` / `system: mentioned_products_json`.

If the terminal appears quiet, check the `run_log` path in the JSON output or the active terminal stderr. Progress lines look like:

```text
[2026-05-31 10:55:00] [INFO] run_id=... stage=ingest file 12/42 start name=...
```

Standard deposit logs also include subprocess diagnostics such as `stage=ingest subprocess returned`, `stage=ingest json_parse done`, `stage=build_profiles start`, and `stage=build_index start/done`. `build_index done` includes both indexed product count and relation count. If source notes exist but these later stages are missing, treat the run as a broken standard-entrypoint execution rather than a completed fund-wiki deposit.

Manager lock files record `run_id`, `created_at`, `pid`, and `host`. If a lock is older than `FPW_LOCK_STALE_HOURS` (default 6), or if it belongs to the current host but the recorded PID no longer exists, fund-wiki archives it under `run_logs\locks\stale` and continues. Fresh locks from live processes still block a new run.

To force the development source project instead of the bundled engine, pass `--project-root` or set `FPW_PROJECT_ROOT`. Use this only for development.

## Query Workflow

Use this workflow when the user says things like:

- "在 fund-wiki 中查询具有 300 指增的公司"
- "找行业暴露 3% 以内且投资经理有 WorldQuant 背景的产品"
- "查询 1000 指增管理人"

Run:

```powershell
python scripts\query_fund_wiki.py "具有300指增的公司" --limit 10 --json
```

For very broad queries, use `--context-budget <chars>` or `--per-result-chars <chars>` only when you need a smaller answer context. Defaults are intentionally lightweight.

Always try this query command first, even when the user asks for a single manager's strategy overview. Do not start from `source_notes` unless the standard query path has already been attempted and found insufficient.

When `--json` is used, the payload includes `context_budget_chars`, `used_context_chars`, `truncated_result_count`, `relations_jsonl`, and per-result `relation_matches`, `ranking_reasons`, `packed_profile_text`, `packed_evidence`, and `context_chars`. Use these fields to explain why a result was selected and whether any evidence was omitted due to budget.

If the index is missing, the script attempts to rebuild it from existing product profiles. The relevant index artifacts are `indexes\product_profiles.jsonl` and `indexes\product_profiles.sqlite`. Index rebuilds write temporary JSONL/SQLite files first and then replace the target files, so a stale or damaged SQLite file should not block a normal rebuild.

If no product profiles exist, explicitly tell the user that the current docs root may contain `source_notes` only and that the searchable `product_profiles` layer has not been built yet. In that case, offer one of these next steps:

1. build or refresh the manager via deposit workflow; or
2. if the user explicitly wants raw-material tracing, switch to `source_notes` mode and clearly label the answer as a source-note synthesis rather than a standard fund-wiki query result.

## References

- `references/path-policy.md` - path resolution, network-drive policy, environment variables.
- `references/workflow.md` - examples and response patterns for deposit/query tasks.
- `references/llm-wiki-phase2-roadmap.md` - concrete fund-wiki phase-2 roadmap inspired by llm-wiki.
