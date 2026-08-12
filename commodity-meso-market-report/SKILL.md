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
- User confirmation is state-specific. Any text/table generation or change after confirmation invalidates the prior render approval.
- Formal Word generation requires successful monitor charts under `artifacts/charts/<run_date>/<freq>/`.
- Missing manual charts or reports may produce a skeleton with pending markers, but never hide missing materials.
- Do not read a prior Word document as the source of previous advice. Read prior standardized Excel from `artifacts/report_runs/<prior_date>/tables/`.
- Existing files under `artifacts/report_runs/<run_date>/texts/` are not evidence that the current run text is fresh. Regenerate and overwrite every required text file for the run after reading the current materials, prompts, monitor snapshots, and standardized tables.
- For manual charts, separate `fact extraction` from `report wording`: first auto-draft observable facts, rankings, confidence, and uncertainty into `artifacts/report_runs/<run_date>/chart_facts/`, then write report text from those facts plus local reports. Human edits are optional and only needed for low-confidence or conflicting cases.
- The first creation of run texts is also a text change. After initial generation, regeneration, or any edit, run the text review gate, show the full generated text content and review summary in the conversation, and pause for user review before running `render`.
- Never run `render` based on a confirmation that happened before the latest text/table generation or edit. The latest assistant message before `render` must have displayed the full current text contents and explicitly asked for render confirmation, and the user must confirm after that message.

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
- `artifacts/report_runs/<run_date>/chart_facts/`
- `artifacts/report_runs/<run_date>/text_review.json`
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

Initialize manual-chart fact sheets without overwriting existing fact notes:

```powershell
python src\report_workflow.py init-facts --run-date <YYYY-MM-DD> --freq W
```

`init-facts` only initializes or upgrades `chart_facts` files. The actual first-draft content for `chart_facts` should be produced by the current assistant conversation after reading charts and local materials, not by an extra API key or a project-side LLM client.

Run static text review before asking for render confirmation:

```powershell
python src\report_workflow.py review --run-date <YYYY-MM-DD> --freq W
```

Generate a skeleton Word after monitor charts exist, allowing pending manual/report sections:

```powershell
python src\report_workflow.py skeleton --run-date <YYYY-MM-DD> --freq W
```

Generate final Word after user confirms texts and tables:

```powershell
python src\report_workflow.py render --run-date <YYYY-MM-DD> --freq W
```

## Linked Fund Weekly Report CLI

Product-performance manual charts may come from:

`F:\Thomas\QuantSystem\domains\fund\tracked-fund-weekly-report`

When the user asks to refresh product performance labels, weekly performance heatmaps, CTA category labels, or integrated CTA display from that source project, run this command from `F:\Thomas\QuantSystem`:

```powershell
.venv\Scripts\python.exe domains\fund\tracked-fund-weekly-report\src\run_report.py
```

After running, check the latest files under:

`domains\fund\tracked-fund-weekly-report\output\`

Do not introduce a separate cross-project workflow unless the user explicitly asks to modify the fund weekly report project itself.

## Workflow

1. Ask for `run_date` if absent.
2. Run `check` and summarize blockers, warnings, previous run directory, material directories, missing charts, and deprecated-directory leftovers.
3. If auto charts are missing, ask permission to run `charts`. After running, run `check` again.
4. Pause and ask the user to place reports and manual charts in the per-run input directories.
5. After user confirms materials are ready, run `check` again.
6. Initialize or refresh manual-chart fact sheets under `artifacts/report_runs/<run_date>/chart_facts/` without overwriting existing notes, then auto-draft chart facts from charts and local reports in the conversation using fixed prompts. Treat `chart_facts` plus local reports as explicit body-text inputs, and overwrite outputs in:
   - `artifacts/report_runs/<run_date>/texts/`
   - `artifacts/report_runs/<run_date>/tables/`
   - Prefer the explicit section-level input artifact `artifacts/report_runs/<run_date>/text_generation_inputs.json` when drafting body text. It is the prompt-ready version of `chart_facts.section_inputs`.
7. Run `context` to refresh machine-readable context and standardized tables.
8. Run `review` plus the text review gate before asking for user confirmation after initial generation and after every subsequent edit. If the user requests text changes, apply the changes and run the text review gate again.
9. Display the full generated contents of all text files plus a concise review summary in the conversation, then stop and ask the user to review the generated texts and Excel tables. File paths, links, or summaries are not a substitute for the full text display.
10. Treat this display as the render approval checkpoint. This checkpoint is required after the first generated text set as well as after later revisions. General confirmations such as “continue” or material-readiness approvals before the latest full-text display do not authorize Word rendering.
11. If any text or table is generated, regenerated, or edited after this display, go back to step 8; older confirmations are void.
12. Only after the user confirms the latest displayed full text set, run `render`.

## Text Review Gate

Before asking the user to confirm rendering, review all files under `artifacts/report_runs/<run_date>/texts/` against these checks:

- Initial generation gate: the first generated text set must pass the same full-display -> user-confirmation -> render loop as any later revision.
- Full-text display gate: a summary, file path list, or “texts are ready” status is not a substitute for displaying the full current contents of all required text files in chat.
- Manual-chart fact gate: for hand-drawn charts, first separate observable facts from interpretation. Prefer a fact sheet under `artifacts/report_runs/<run_date>/chart_facts/` before writing final prose.
- Manual-chart completeness gate: before render, every configured manual chart should have a matching fact sheet under `artifacts/report_runs/<run_date>/chart_facts/`, and placeholder content such as `待填写`, `自动草稿占位`, or old default confidence markers must be removed. A human reviewer is optional; what matters is that the fact sheet contains substantive auto-drafted facts and report judgments.
- Source wording: do not write `手动行情图显示`, `自动图显示`, `图中可以看到`, or similar chart-provenance narration in report body text. State the conclusion directly.
- Reasoning exposure: do not narrate the research or synthesis process in body text. Avoid phrases such as `结合某周报`, `从图上看`, `说明我们可以理解为`, or other wording that exposes intermediate reasoning steps when the final judgment can be stated directly.
- Unsupported concepts: do not introduce broad concepts that are not supported by the chart, table, or materials, such as `相对价值` or `单一商品总指数对整体机会的代表性下降`.
- Legend fidelity: use chart legend labels exactly when describing chart categories. Use `升水品种` and `贴水品种` instead of internally inferred labels such as `低曲线 RSI 品种` or `高曲线 RSI 品种`.
- Term-structure color mapping: for the futures curve structure chart, map bar colors strictly by the chart legend. Treat green bars as `贴水品种` and blue bars as `升水品种`. Do not infer or reverse the mapping from visual intuition alone.
- Factor names: use standard factor wording from the chart or prompt, such as `商品动量因子`; do not shorten or mistype it as `商品动因`.
- Term structure: combine the futures curve structure with its performance to state whether it is a positive or negative contribution to the roll/term-structure factor. If the term-structure factor weakens, explain the source of the drag.
- Term-structure paragraph shape: prefer a concise signed conclusion for the term-structure paragraph: relative performance of `贴水品种` versus `升水品种` -> contribution direction to the term-structure factor. Add a second sentence only when there is explicit evidence for persistence, reversal, or a clear transmission path to related basis signals.
- Product labels: when describing product performance, strictly follow the category labels shown in the product-performance legend.
- Weekly heatmap: treat the rightmost column of the weekly performance heatmap as the latest week.
- Weekly heatmap scope: in report body text, describe only `CTA中长周期趋势`, `CTA短周期趋势`, `期货主观趋势`, and `股指CTA`; write them as `中长周期趋势CTA`, `短周期趋势CTA`, `期货主观`, and `股指CTA`. Do not describe other product strategies from the weekly heatmap.
- Integrated CTA wording: describe the aggregate `CTA` line naturally as `综合 CTA` when needed; do not add a stiff definition of what CTA aggregates.
- Summary discipline: do not force a final `综合来看` paragraph if it only repeats later strategy advice or adds no new judgment.
- Avoid generic wrap-up formulas at the end of `market_overview.md`, especially stock summary sentences such as `当前CTA环境较前期有所修复，但仍以结构性机会为主。中长周期趋势的把握难度依然不低，短线与截面交易的可用度相对更高，商品期限结构因子和局部板块轮动线索值得继续跟踪。` If the ending paragraph does not introduce a new, evidence-backed conclusion that is not already stated above or deferred to later strategy/table sections, remove it instead of polishing it.
- Concision mode: if the user asks to simplify, compress, reduce text, or says the client thinks the text is too long, verify `客户精简模式` was applied: no mechanical chart-by-chart expansion, no table-intro over-explanation, and paragraph counts stay within the prompt limits.
- Institutional tone: prefer restrained weekly-report wording such as `修复`, `分化`, `偏强`, `偏弱`, `中性偏谨慎`, `尚未回到`, and `相对占优`. Avoid promotional or allocation-heavy wording in body text such as `大涨`, `显著提升`, `积极配置`, `超配`, `重点聚焦`, or `配置价值显著提升`.
- Readability: run a slow read-through for stiff or overloaded wording. Fix sentences that stack three or more judgments, overuse abstract words such as `变量`, `约束`, `识别`, or read like chart-summary stitching rather than weekly-report prose. Use the style and rewrite examples in `runtime_assets/report_prompts/chart_interpretation.md`.
- Single-claim paragraphs: each paragraph should carry one primary judgment only. If a paragraph mixes macro narrative, market state, factor interpretation, and allocation advice at the same time, split or compress it so the main conclusion remains singular and easy to sign.
- Prefer signed conclusions over explanatory chains: when the direction is already clear, prefer short judgment-led sentences such as `中期动量走弱，长期动量和截面动量走势平稳` over long reasoning chains that restate evidence before arriving at the same conclusion.
- Inference discipline: for phrases such as `开始走强`, `恢复明显`, `形态更完整`, `风险偏好回暖`, or `主线确认`, confirm there is direct chart or report support; otherwise rewrite to lower-confidence wording.
- Revision loop: after initial text generation or any text edit, including minor wording polish, rerun the text review gate, display the full contents of all text files again with a short review summary, and wait for user confirmation before `render`.
- Confirmation validity: prior user confirmations do not carry across text/table generation or edits. If the current text set has not been fully displayed in the conversation after the latest generation or edit, `render` is forbidden.
- Review output: report a short checklist summary to the user together with the full text. If any item fails, fix the text before asking for confirmation. The project CLI `review` handles static checks, including `chart_facts` substantive-content checks and weak section coverage, but it does not replace the conversational full-text display and user confirmation gates.

## Prompt Sources

Fixed prompts live in:

- `runtime_assets/report_prompts/chart_interpretation.md`
- `runtime_assets/report_prompts/strategy_table.md`
- `runtime_assets/report_prompts/commodity_table.md`
- `runtime_assets/report_prompts/manual_chart_fact_schema.md`

Do not improvise table schemas unless the user explicitly changes the project contract.

When generating `strategy_advice` or `commodity_advice`, read the corresponding prompt file before drafting the table. The prompt contract is:

- Read all files in `inputs/report_runs/<run_date>/report_reports/`; do not filter local files by publication date.
- Use web search only as supplemental evidence when local materials are insufficient or need cross-checking.
- Web-sourced supplemental evidence must be from authoritative materials published in the past 7 days.
- `strategy_advice` may only use `增持`, `减持`, or `中性`.
- `commodity_advice` may only use `看多`, `看空`, or `中性`.
- Do not generate `上期建议`; the project code merges it from prior standardized Excel.

When generating report text, read `runtime_assets/report_prompts/chart_interpretation.md` first. Treat it as the authoritative source for report-body wording. Keep `SKILL.md` focused on workflow and review gates; place detailed reusable wording rules in the prompt file. If the user says the client thinks the text is too long or asks to simplify, compress, or reduce the body text, enable the prompt file's `客户精简模式`. The text style contract applies to chart interpretation text and table intro text:

- Keep the language professional, compressed, and weekly-report-like.
- Do not use bold, bullet lists, or instruction-like prose in report body text.
- Follow chart order when ordering paragraphs.
- Default to qualitative positioning; include at most one core number only for anomalies or important turning points.
- Use light strategy implications, such as `对中短周期趋势更友好` or `可保持中性偏积极`, but avoid strong allocation commands.
- Table intro files `strategy_advice_intro.md` and `commodity_advice_intro.md` must follow the same style.
- In `客户精简模式`, keep `market_overview.md` to 4-5 paragraphs, `factor_performance.md` to 3 paragraphs, `product_strategy.md` to 3 paragraphs, and each table intro to one concise paragraph.

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
