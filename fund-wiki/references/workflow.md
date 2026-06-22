# Fund Wiki Workflow Examples

## Natural Language Routing

| User wording | Action |
|---|---|
| 请沉淀双隆的尽调材料 | Single-manager deposit |
| 把双隆入库 / 更新双隆 fund-wiki | Single-manager deposit |
| 重新沉淀双隆 / 强制重跑 | Single-manager deposit with `--force` |
| 请沉淀双隆、磐松、半鞅 | Run one deposit command per manager and summarize JSON results |
| 查询双隆 CTA 产品 | Query fund-wiki |
| 找 300 指增、WorldQuant 背景、行业暴露 3% 以内 | Query fund-wiki |
| 我第一次使用 fund-wiki / 初始化 fund-wiki | Run `init_fund_wiki.py --json` |
| 检查 fund-wiki 环境 | Run `init_fund_wiki.py --json` |

## Deposit Example

User:

```text
请把双隆的尽调资料沉淀到 fund-wiki。
```

Run dry-run first if the manager name may be ambiguous:

```powershell
python scripts\deposit_manager.py "双隆" --dry-run --json
```

If the selected folder is correct, run:

```powershell
python scripts\deposit_manager.py "双隆" --use-llm --provider deepseek --json
```

Default behavior skips unchanged files using `run_logs\source_manifest.jsonl` and writes manifest records instead of copying raw files. Use `--force` to reprocess, or `--snapshot none` when even manifest records should be suppressed.

Password-protected/encrypted PDFs are skipped before source catalog fingerprinting. They do not enter parse, OCR, LLM extraction, source notes, manifest, or index.

During ingest, fund-wiki reuses the source catalog fingerprint so network-drive files are not hashed again in the parse-preparation stage. Parsed text is also written to a local run-scoped cache and then used as the LLM input. This cache is not a formal wiki artifact and never participates in query/index.

To keep parsed cache for debugging or recovery:

```powershell
python scripts\deposit_manager.py "双隆" --use-llm --provider deepseek --keep-parsed-cache --json
```

Cache cleanup policy:

- `success` / `skipped`: clean this run's cache unless `--keep-parsed-cache` is set.
- `partial_success*` / `error`: keep this run's cache for recovery.
- Old cache runs are removed by `FPW_PARSED_CACHE_TTL_HOURS` (default 48).

For a fast first pass over high-signal materials only, use:

```powershell
python scripts\deposit_manager.py "双隆" --use-llm --provider deepseek --ingest-scope priority --json
```

Each run writes a source catalog to `run_logs\source_catalog\<manager>.jsonl`. The catalog records file category and priority so later diagnostics can explain why a file was processed early or deferred.

Return:

- Raw folder selected.
- Docs root used.
- Run log path from `run_log`.
- Parsed cache status from `parsed_cache`, including `run_dir`, `files_before_cleanup`, `cleaned`, and `cleanup_reason`.
- Number of product profiles after rebuild.
- Profile quality status from `profile_quality`.
- Index files generated.
- Relation index generated: `indexes\relations.jsonl` and `indexes\relations.sqlite`.
- Health check status from `health_check`, plus `reports\health_check.md`.
- Review queue status, if any high/warning issues exist: `review_queue\open.jsonl` and `review_queue\open.md`.
- Governance/navigation docs refreshed: `fund_wiki_purpose.md`, `fund_wiki_schema.md`, `index.md`, `overview.md`, and `log.md`.
- Any missing API key or dependency errors.
- OCR warnings, if any: scanned PDFs may be recorded as `Source/ParseWarning` notes when Tesseract or Chinese language data is unavailable. The batch should continue and the final status may be `partial_success`.
- Stale lock recovery, if `stale_lock_recovered` is true.

## Query Example

User:

```text
在 fund-wiki 中查询具有 300 指增的公司。
```

Run:

```powershell
python scripts\query_fund_wiki.py "具有300指增的公司" --limit 10 --json
```

Return the top candidates using `product_name`, `manager`, `evidence_snippet`, `path`, `matched_terms`, `missing_terms`, `relation_matches`, and `ranking_reasons`. If hard conditions are missing, preserve the script's "缺失" message instead of inventing a match.

For manager-discovery queries such as "哪些管理人有期货策略", "哪些公司做1000指增", "哪些私募有WorldQuant背景", or "哪些管理人行业暴露在3%以内", use `manager_results` as the primary answer. These results are grouped from the full product-profile index before the output limit is applied, so they are safer than manually grouping only the returned product Top-N.

Each manager result includes `matched_products`, `representative_products`, `matched_strategy_tags`, `evidence_snippets`, `confidence`, and `review_flags`. If a result has `mixed_strategy_tags` or `tag_conflict_review_needed`, keep it in the answer but mark it as needing review instead of treating it as a fully confirmed strategy classification.

JSON query results may also include `canonical_product_name`, `profile_quality_status`, `context_budget_chars`, `used_context_chars`, `truncated_result_count`, `packed_profile_text`, `packed_evidence`, and `context_chars`. Use these as diagnostics and answer from the packed evidence first when present.

Do not skip this query step and read `source_notes` first. For requests like "双隆的策略", "查询某管理人的产品线", or other flexible retrieval prompts, query `product_profiles` and `indexes\product_profiles.jsonl` / `indexes\product_profiles.sqlite` first, then answer from the returned JSON evidence.

For diagnostics or deeper evidence tracing, `indexes\relations.jsonl` / `indexes\relations.sqlite` can be used to inspect explicit links such as `has_product_line`, `has_people_background`, `has_exposure_constraint`, `has_risk_point`, and `has_source_note`. The query engine already uses these relation files in scoring, while the standard user-facing query entry remains `query_fund_wiki.py --json`.

If the query path fails because the index is missing, explicitly say that the standard fund-wiki profile/index layer is unavailable. Rebuild from existing `product_profiles` when possible. If only `source_notes` exist, state that clearly before offering a source-note synthesis.

## First-Run Initialization Example

User:

```text
我第一次使用 fund-wiki。
```

Run:

```powershell
python scripts\init_fund_wiki.py --json
```

If the returned `actions_requiring_user_confirmation` asks to create or update a skill-local `.env`, confirm with the user first, then run:

```powershell
python scripts\init_fund_wiki.py --json --apply-skill-env
```

Base the answer on `blocking_items`, `warnings`, `resolved_paths`, `suggested_config_writes`, and `next_actions`. Do not auto-write API keys.

## Ambiguous Manager Folder

If multiple manager folders match:

1. Show the candidate table from `deposit_manager.py`.
2. Ask the user to provide a more specific manager keyword or raw folder path.
3. Re-run with `--raw-root` or a more specific manager name.
