# MyNotes Note Contracts

## Canonical paths

- MOC and method: `200 Areas/210 资产配置/218 框架研究/宏观策略判断体系/`
- Modules: `.../框架库/`
- Evidence: `.../指标与证据/`
- Cases: `.../历史案例/`
- Weekly prediction and review: `500 Journal/530 Weekly/宏观策略/`
- Templates: `900 Assets/910 Templates/TPL-Macro-*.md`

## Templates

- `TPL-Macro-Strategy-Weekly.md` → `YYYY-Www_宏观策略判断.md`
- `TPL-Macro-Strategy-Maturity-Review.md` → `YYYY-Www_宏观策略判断_到期复盘.md`
- `TPL-Macro-Framework-Module.md` → `框架库/<主题>.md`
- `TPL-Macro-Evidence-Card.md` → `指标与证据/<指标或主张>.md`
- `TPL-Macro-Historical-Case.md` → `历史案例/<时期>_<主题>.md`

## Required fields

Every note uses Obsidian-compatible YAML with `type`, `status`, `stage`, `confidence`, `source_files`, `related_notes`, `human_review_required`, and review dates. Weekly notes additionally require `information_cutoff`, `forecast_horizon_primary`, `forecast_horizon_secondary`, `framework_version`, `previous_note`, `anchor_forecast`, and `maturity_review`.

## Stage and review

- New or incomplete notes: `stage: raw` or `synthesized`, `human_review_required: true`.
- Do not set `stage: validated` for investment conclusions, MOC conclusions, or framework claims until the user confirms accuracy, caveats, destination, and intended use.
- Do not move/delete original sources unless explicitly approved.

## Immutability and versions

- Frozen weekly fields are append-only. Corrections carry a timestamp and reason.
- Framework modules use `framework_version` and a version table. A later version must not alter the text or interpretation of old forecasts.
- Use wikilinks to connect method, module, evidence, case, forecast, and review; do not duplicate long summaries.

