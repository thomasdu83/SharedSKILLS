---
name: zmdata-data-api
description: Use when Codex needs to answer questions, explain parameters, write Python code, or directly call documented ZM internal zmdata data APIs via CLI, including stocks, funds, fund pools, fund scoring, portfolio/PM APIs, bonds, ETFs, options, futures, indexes, macro data, exchange rates, spot data, and related ID mappings such as label_id, rankconfigid, benchID, and score fields.
---
<!-- light-skill-version-check:start -->
## Version Check

Before using this Skill, run:

```bash
python3 scripts/light_skill_check_update.py --brief
```

If the command prints `UPDATE_AVAILABLE`, tell the user a newer Skill package is available and provide the download URL. If the user explicitly asks to upgrade this Skill, run:

```bash
python3 scripts/light_skill_check_update.py --force --upgrade --brief
```

For details, read `docs/light-skill-version-check.md`.
<!-- light-skill-version-check:end -->

# ZMData Data API

## Overview

Use this skill to choose ZM internal `zmdata` interfaces, explain required parameters, write Python snippets, and run documented APIs through the bundled CLI when the user asks to fetch or verify data.
Use `references/` as the source of truth. Do not invent interfaces, parameters, enum values, IDs, or response fields that are not present in the references.

## Installation

If `zmdata` is not installed in the active Python environment, install it from the internal package index:

```bash
pip install -i http://10.168.30.14:8081/repository/flare-custom/simple --trusted-host 10.168.30.14 zmdata
```

The current documented release is `20260525` / `1.4.2`.

Verify the installed version:

```python
import zmdata
print(zmdata.__version__)
```

## Upgrade

When the user asks to "升级这个skills", update both this skill and the local SDK:

1. Update this skill's docs and scripts to the latest checked-in version.
2. Check the installed SDK version:

```bash
python scripts/zmdata_cli.py doctor
```

3. If `zmdata` is missing or below `1.4.2`, install the local release wheel:

```bash
python -m pip install --upgrade /Users/lee/git/APIClientResearch/release/zmdata-1.4.2-py3-none-any.whl
```

The user should not need to ask for the SDK separately when upgrading this skill.

## Default Import

Use this import style in generated Python:

```python
import zmdata as api
```

For 投后(组合) APIs, require the caller to set `PM_API_KEY` before calling the interface:

```python
import zmdata as api

api.PM_API_KEY = '<your-api-key>'
```

Never include real API keys, tokens, passwords, or private credentials.

## Reference Selection

Start with `references/zm_howto.md` when the user asks broadly which API to use.

Load the smallest relevant reference file:

- Stocks: `references/zm_api_stock.md`
- Funds, fund pools, NAV, fund scale, holdings, fund scoring: `references/zm_api_fund.md`
- Portfolio / PM / 投后(组合) overview: `references/zm_api_portfolio_v2.md`
- PM V2 support lookups: `references/zm_api_pm_v2_support.md`
- PM V2 performance: `references/zm_api_pm_v2_performance.md`
- PM V2 allocation: `references/zm_api_pm_v2_allocation.md`
- PM V2 risk: `references/zm_api_pm_v2_risk.md`
- PM V2 holding analysis: `references/zm_api_pm_v2_holding.md`
- Bonds: `references/zm_api_bond.md`
- ETF: `references/zm_api_etf.md`
- Options: `references/zm_api_options.md`
- Futures: `references/zm_api_futures.md`
- Index price or components: `references/zm_api_index.md`
- Macro data: `references/zm_api_macro.md`
- Forex data: `references/zm_api_forex.md`
- Spot data: `references/zm_api_spot.md`
- Enums and constants: `references/zm_enums.md`
- `rankconfigid`, scoring sample groups, `get_fund_score` configuration: `references/rankconfig_id.md`
- `benchID` or index ID mappings: `references/zm_index_ids.md`
- Fund group IDs, fund pools, labels, `label_id` lists, market tracking pool labels: `references/zm_fund_group_ids.md`
- Fund score field meanings: `references/zm_fund_score_fields.md`

If uncertain, search references directly with `rg`.

## Intent Routing

- For fund label enumeration or lookup requests such as “所有标签”, “有哪些标签”, “标签ID”, “基金池”, “分组”, “赛道列表”, or “市场跟踪池”, read `references/zm_fund_group_ids.md` first and treat the requested IDs as `label_id` values.
- For scoring requests that explicitly mention “评分”, “产品评分”, `rankconfigid`, `score`, or `get_fund_score`, read `references/rankconfig_id.md` first to identify the scoring sample group.
- If a request mentions both labels and scoring, use `references/rankconfig_id.md` for the `rankconfigid` and related scoring configuration, then use the associated `label_id` with `get_fund_in_label`.

## Business Rules

- Use `get_fund_in_label` for fund pool queries.
- Do not use retired or undocumented fund-pool interfaces.
- For “市场跟踪池/私募跟踪池 + CTA + 评分” requests, follow:
  1. Use `references/rankconfig_id.md` to find the `rankconfigid` and related `label_id`.
  2. Call `api.get_fund_in_label(label_id_list=[label_id])`.
  3. Call `api.get_fund_score(fund_id_list=..., rankconfigid=..., is_day=0, is_norm=1)` unless the user asks otherwise.
- For fund score explanations, use `references/zm_fund_score_fields.md` to translate score field names.
- For 投后(组合) requests, set `api.PM_API_KEY = '<your-api-key>'` before calls. Use `references/zm_api_portfolio_v2.md` as the overview, then load the smallest PM V2 file for the requested area: support, performance, allocation, risk, or holding.
- For index requests that mention named internal indexes, use `references/zm_index_ids.md` to determine the correct `benchID` or `index_code`.
- For risk factor return series used by `pm_risk_factor_exposure` (for example stock Barra factors or CTA strategy factors), prefer `risk_factor_returns`. Use `references/zm_index_ids.md` to inspect the underlying `benchID` mapping; use `index_price` / `get_index_price` only when the user explicitly needs the generic index/benchmark/factor price endpoint.

## Workflow

1. Classify the user request: API choice, parameter explanation, ID lookup, code generation, or actual data retrieval.
2. Read the relevant reference file before answering.
3. Identify required parameters. If a required value is missing, state exactly what is missing.
4. For explanation or code-generation requests, generate minimal Python that uses documented parameters only.
5. For actual data retrieval, prefer `scripts/zmdata_cli.py call ...` over creating ad hoc Python files.
6. Mention reference-specific caveats, such as PM API Key requirements or rankconfigid lookup steps.

## CLI Data Retrieval

Use the controlled CLI when the user asks to "查一下", "跑一下", "验证接口", "取数据", or otherwise wants real data returned in the current session.

List documented APIs:

```bash
python scripts/zmdata_cli.py list
python scripts/zmdata_cli.py list --keyword 投后
```

Show the reference section for one API:

```bash
python scripts/zmdata_cli.py info get_track_revenue
```

Call an API with JSON keyword arguments:

```bash
python scripts/zmdata_cli.py call get_fund_in_label \
  --params '{"label_id_list":[12345]}' \
  --format json \
  --head 20
```

Call a 投后(组合) API only after `ZM_PM_API_KEY` is available in the environment:

```bash
python scripts/zmdata_cli.py call get_track_revenue \
  --params '{"pm_id":10001,"strategy_type":1}' \
  --format json
```

CLI rules:

- `zmdata_cli.py call` only allows interfaces documented in `references/zm_api_*.md`.
- Pass parameters as a JSON object with `--params`; use `--set key=value` only for small overrides.
- Use `--head N` to keep outputs small.
- Use `--out result.csv --format csv` when the output is too large for the conversation.
- Do not pass API keys on the command line. Use environment variables such as `ZM_PM_API_KEY`.
- If CLI import or authentication fails, explain the missing environment requirement and provide the Python call pattern instead.

## Documentation Search

Use `rg` from the skill root for fuzzy documentation search:

```bash
rg -n "get_track_revenue" references/
rg -n "市场跟踪池|get_fund_score" references/
```

Use `scripts/zmdata_cli.py info` when you already know the API name and want its section:

```bash
python scripts/zmdata_cli.py info get_track_revenue
```
