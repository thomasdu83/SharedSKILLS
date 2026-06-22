---
name: wisdom-manager-product-research
description: Call fofresearchsvr/ai business APIs for private-fund manager and product facts: 私募管理人、机构详情、管理人旗下产品、私募产品查询、产品要素、合同文件下载、产品净值, or manager/product disambiguation. For Obsidian-note-based investment synthesis or judging strategy/team/performance with quantitative scripts, use quant-research after needed facts are retrieved.
triggers: ["私募尽调", "私募研究", "管理人分析"]
---
<!-- light-skill-version-check:start -->
## Version Check

Before using this Skill, run:

```bash
python3 scripts/light_skill_check_update.py --brief
```

If the command prints `UPDATE_AVAILABLE`, tell the user a newer Skill package is available and provide the download URL. For details, read `docs/light-skill-version-check.md`. Do not update files automatically unless the user explicitly asks.
<!-- light-skill-version-check:end -->

# Manager And Product Research Workflow

Use this skill as the unified entry for private-fund manager and product lookup.

The service boundary is `fofresearchsvr/ai`. Do not call Knowledge OS retrieval APIs directly from this skill. Product terms and contract queries must go through the business APIs exposed by `fofresearchsvr/ai`.
When users say 产品编码, map it to API param `fund_code`.

## Boundary With quant-research

Use this skill for factual manager/product retrieval through business APIs. Do not use it to synthesize Obsidian notes, update research notes, or make broader FOHF investment judgments. When the user needs both factual retrieval and research interpretation, complete the API lookup here first, then hand the retrieved facts to `quant-research`.

## Workflow Decision Tree

1. Identify whether the user is asking about a manager or a product.
2. Call exactly one API tool per step and wait for the result before the next call.
3. Resolve manager/product identity first, then call detail/list/terms/contract/nav actions.
4. Produce the final response only after the necessary data is retrieved.

## Flow A: Manager Query

Use this when the request is about a private-fund manager, institution, core personnel, strategy, race, manager-owned products, or manager fulltext/keyword lookup.

1. Call `search_managers` first.
2. Prefer structured params when the user gives exact constraints:
   - `manager_name`
   - `personnel_name`
   - `product_name`
3. Prefer `query` when the user gives natural-language intent, keyword, English institution name,履历条件, or strategy description.
4. If manager detail is requested, call `get_manager_detail`.
5. If managed products are requested, call `list_manager_products`.
6. If manager materials or research files are requested, call `list_manager_materials`.
7. If the user asks for a specific material file, call `download_manager_material`.
8. Summarize using returned data only.

Recommended `search_managers` usage:

- Exact institution/person match: use hard filters such as `manager_name` / `personnel_name`
- Keyword/fulltext lookup: use `query`
- Natural-language recall: use `query`

## Flow B: Product Query

Use this when the request is about a product, product terms, contract, NAV, or product candidate filtering.

1. If the user already provides 产品编码 (`fund_code`), use it directly for `get_product_terms` / `get_product_contract`.
2. If the user provides only product name or product filtering conditions, call `search_products` first.
3. `search_products` now supports richer filtering. Prefer these params when available:
   - `product_name`
   - `manager_name`
   - `strategy_name`
   - `race_name`
   - `performance_fee`
4. `search_products` no longer needs to be driven only by `product_name`. It can be used for condition-based candidate search as long as at least one effective condition is provided.
5. For product basic info or NAV, use `product_id`:
   - call `get_product_detail` for product basic info
   - call `get_product_nav` for 产品净值
6. For product terms and contract:
   - call `get_product_terms`
   - call `get_product_contract`
   - for `get_product_contract`, always save the downloaded file to a local temp directory:
     - base dir: `/tmp/openclaw_downloads/wisdom-manager-product-research/`
     - filename must use the original response filename (from `Content-Disposition`) whenever available
   - after saving contract locally, return a concise handling result including:
     - `local_file_path`
     - `filename`
     - `content_type` (if available)
     - `file_size_bytes` (if available)
   - both APIs support `product_id` and `fund_code`; if both are available, prefer `fund_code`
7. Summarize using returned data only.

## Flow C: Fallback Query

Use this only when manager/product lookup is empty or insufficient.

1. Retry with `search_managers(query=<keyword or natural-language intent>)`.
2. If the data is still insufficient, ask the user once for the missing manager name, product name, strategy, race, fee condition, or other disambiguating details.

## Output Rules

1. Never fabricate data. Every statement must be grounded in API responses.
2. Include the data cutoff date when describing NAV or time-series results.
3. Treat product terms and contract as different outputs:
   - `get_product_terms` returns structured product terms data
   - `get_product_contract` returns downloadable contract file stream (`pdf/doc/docx`)
   - when contract download succeeds, include the local temp file path so downstream actions can reuse it without re-downloading
   - `filename` in output should be the original filename from the download response
4. Keep the answer objective and concise.

## API Reference

- Read [references/api.md](references/api.md) for endpoint paths, params, and response fields.
