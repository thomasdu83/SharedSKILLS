---
name: commodity-meso-market-report
description: Use when working in the commodity-meso-market-monitor project and the user wants a staged workflow for CTA market environment report preparation, material checks, chart generation, interpretation text, advice tables, or Word output.
---

# Commodity Meso Market Report

## Scope

This skill is project-specific. Use it only inside:

`F:\Thomas\QuantSystem\domains\cta\commodity-meso-market-monitor`

The skill is a staged report-preparation guide. All executable logic lives in this project. Do not place chart-generation or report-rendering code inside the skill.

## Config Contract

- The default report structure config is `configs/report.yaml`, wired by `src/project_paths.py` as `DEFAULT_REPORT_CONFIG_FILE`.
- Prompt files live under `runtime_assets/report_prompts/`.
- Do not guess or search for `runtime_assets/report_config.yaml`; that file is not part of this project contract.
- If the report structure, section order, chart refs, table source patterns, or Word filename are needed, read `configs/report.yaml`.

## Hard Rules

- The user must provide `run_date` each time. Do not guess today's date or the latest directory.
- Default `freq` is `W` only when the user does not specify frequency.
- Use staged progression. After each key check or generated interpretation, pause and wait for user confirmation.
- Formal Word generation requires successful monitor charts under `artifacts/charts/<run_date>/<freq>/`.
- Missing manual charts or reports may produce a skeleton with pending markers, but never hide missing materials.
- Do not read a prior Word document as the source of previous advice. Read prior standardized Excel from `artifacts/report_runs/<prior_date>/tables/`.
- Existing files under `artifacts/report_runs/<run_date>/texts/` are not evidence that the current run text is fresh. Regenerate and overwrite every required text file for the run after reading the current materials, prompts, monitor snapshots, and standardized tables.
- After regenerating texts, show the full generated text content in the conversation and pause for user review before running `render`.

## Directory Contract

Per-run manual inputs:

- `inputs/report_runs/<run_date>/report_reports/`
- `inputs/report_runs/<run_date>/manual_charts/`

Deprecated global inputs are not read by default:

- `inputs/report_reports/`
- `inputs/manual_charts/`

If files remain in deprecated directories, tell the user to move them into the per-run input directory.

Auto-generated project outputs:

- `artifacts/charts/<run_date>/<freq>/`
- `artifacts/monitor_snapshots/<run_date>/<freq>/run_manifest.json`

Report outputs:

- `artifacts/report_runs/<run_date>/workflow_status.json`
- `artifacts/report_runs/<run_date>/report_context.json`
- `artifacts/report_runs/<run_date>/source_manifest.json`
- `artifacts/report_runs/<run_date>/texts/`
- `artifacts/report_runs/<run_date>/tables/strategy_advice.xlsx`
- `artifacts/report_runs/<run_date>/tables/commodity_advice.xlsx`
- `artifacts/report_runs/<run_date>/CTA市场环境跟踪-<run_date>.docx`

Manual chart names must use `number_semantic-label` prefixes:

- `010_commodity_index_weekly_returns.png`
- `011_sector_short_cycle_market.png`
- `012_sector_long_cycle_market.png`
- `020_factor_overall.png`
- `030_factor_momentum.png`
- `040_factor_fundamental.png`
- `050_factor_basis.png`
- `060_factor_crowding.png`
- `070_product_status.png`
- `071_product_forecast.png`
- `072_product_performance_tags.png`
- `073_product_weekly_performance.png`

Auto charts are never renamed. Resolve them from `run_manifest.json` and verify the actual image files exist under `artifacts/charts/<run_date>/<freq>/`.

## Staged CLI

Use `src\report_workflow.py` as the main project entrypoint.

Self-check:

```powershell
python src\report_workflow.py check --run-date <YYYY-MM-DD> --freq W
```

Generate monitor charts:

```powershell
python src\report_workflow.py charts --run-date <YYYY-MM-DD> --freq W
```

Generate context and standardized Excel tables without Word:

```powershell
python src\report_workflow.py context --run-date <YYYY-MM-DD> --freq W
```

Generate a skeleton Word after monitor charts exist, allowing pending manual/report sections:

```powershell
python src\report_workflow.py skeleton --run-date <YYYY-MM-DD> --freq W
```

Generate final Word after user confirms texts and tables:

```powershell
python src\report_workflow.py render --run-date <YYYY-MM-DD> --freq W
```

## Workflow

1. Ask for `run_date` if absent.
2. Run `check` and summarize blockers, warnings, previous run directory, material directories, missing charts, and deprecated-directory leftovers.
3. If auto charts are missing, ask permission to run `charts`. After running, run `check` again.
4. Pause and ask the user to place reports and manual charts in the per-run input directories.
5. After user confirms materials are ready, run `check` again.
6. Interpret charts and reports in the conversation using fixed prompts, then overwrite outputs in:
   - `artifacts/report_runs/<run_date>/texts/`
   - `artifacts/report_runs/<run_date>/tables/`
7. Run `context` to refresh machine-readable context and standardized tables.
8. Display the full generated contents of all text files in the conversation, then stop and ask the user to review the generated texts and Excel tables.
9. Only after the user confirms, run `render`.

## Prompt Sources

Fixed prompts live in:

- `runtime_assets/report_prompts/chart_interpretation.md`
- `runtime_assets/report_prompts/strategy_table.md`
- `runtime_assets/report_prompts/commodity_table.md`

Do not improvise table schemas unless the user explicitly changes the project contract.

When generating `strategy_advice` or `commodity_advice`, read the corresponding prompt file before drafting the table. The prompt contract is:

- Read all files in `inputs/report_runs/<run_date>/report_reports/`; do not filter local files by publication date.
- Use web search only as supplemental evidence when local materials are insufficient or need cross-checking.
- Web-sourced supplemental evidence must be from authoritative materials published in the past 7 days.
- `strategy_advice` may only use `增持`, `减持`, or `中性`.
- `commodity_advice` may only use `看多`, `看空`, or `中性`.
- Do not generate `上期建议`; the project code merges it from prior standardized Excel.

When generating report text, read `runtime_assets/report_prompts/chart_interpretation.md` first. The text style contract applies to chart interpretation text and table intro text:

- Keep the language professional, compressed, and weekly-report-like.
- Do not use bold, bullet lists, or instruction-like prose in report body text.
- Follow chart order when ordering paragraphs.
- Default to qualitative positioning; include at most one core number only for anomalies or important turning points.
- Use light strategy implications, such as `对中短周期趋势更友好` or `可保持中性偏积极`, but avoid strong allocation commands.
- Table intro files `strategy_advice_intro.md` and `commodity_advice_intro.md` must follow the same style.

## Table Rules

There are exactly two advice tables:

- `CTA策略配置表`: standardized as `strategy_advice.xlsx`
- `期货品种配置表`: standardized as `commodity_advice.xlsx`

Previous-period advice is read from the latest prior standardized Excel in `artifacts/report_runs/<date>/tables/`.

Merge keys:

- Strategy table: `策略类别`
- Commodity table: `板块` + `品种`

If no previous row matches, leave `上期建议` blank.

## Word Table Layout Rules

The project renderer owns Word table formatting so every future report uses the same layout.

- `strategy_advice` uses compact 7 pt body text and 7.5 pt header text.
- `strategy_advice` makes `宏观中观因素` and `市场微观因素` the dominant wide columns; `策略类别`, `投资建议`, and `上期建议` remain narrow.
- `commodity_advice` uses compact 7 pt body text and 7.5 pt header text.
- `commodity_advice` makes `关键驱动逻辑` the dominant wide column; `板块`, `品种`, `投资建议`, and `上期建议` remain narrow.
- Do not manually resize these tables in a one-off Word file; update `src/commodity_meso_market_monitor/reports/renderer.py` so later `render` runs inherit the change.
