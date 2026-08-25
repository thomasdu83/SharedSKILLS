---
name: macro-strategy-learning
description: Use when the user asks to create, update, guide, or review weekly global multi-asset macro judgments, scenario probabilities, prediction snapshots, maturity reviews, or durable macro mechanism frameworks in MyNotes; includes 周度宏观策略、资产配置复盘、黄金、宏观流动性、政策传导、中国权益风格、海外国家权益、债券、商品和汇率专题。
---

# Macro Strategy Learning

## Core contract

Maintain two linked but separate loops:

- **Forecast loop:** facts → macro state/policy response → market pricing → scenarios → asset mapping → stance → maturity review.
- **Research loop:** daily material → mechanism/evidence/counterexample → framework module → weekly use → review feedback → versioned update.

The objective is not a persuasive weekly essay. It is an auditable set of time-stamped, falsifiable, probabilistic judgments that can be compared with simple baselines.

## Route the request

1. **Weekly judgment/update** → read `references/workflows.md` section “Weekly forecast” and `references/analysis-contract.md`.
2. **4–6 week or 3-month maturity review** → read `references/workflows.md` section “Maturity review” and `references/quality-rubric.md`.
3. **Build or improve a topic framework** → read `references/workflows.md` section “Framework module” and the relevant part of `references/analysis-contract.md`.
4. **Accumulate an indicator, claim, source, or historical episode** → read `references/workflows.md` section “Evidence and case” and use the corresponding MyNotes template.
5. **Audit the system or change a template/skill** → inspect existing notes first, then read `references/note-contracts.md` and preserve version history.

## Non-negotiable rules

- Freeze the information cutoff, forecast horizons, currency, universe, and benchmark before reasoning.
- Separate fact, inference, scenario, asset conditional response, and action. Never use an asset result to prove a macro premise.
- Keep at most three mutually intelligible scenarios whose probabilities sum to 100%; record why probabilities changed.
- Do not replace a missing historical snapshot with hindsight. Mark the review retrospective.
- Do not overwrite a frozen weekly snapshot. Append a dated correction or create the next snapshot.
- Treat China cycle, dividend, value, and prosperity-growth as overlapping investable baskets with distinct risk exposures, not mutually exclusive sectors.
- For overseas equities, separate local-currency equity performance from the investor's RMB unhedged return; distinguish country effect from global beta and sector composition.
- Do not turn a checklist into an equal-weight score. Explain evidence roles, regime dependence, and alternative explanations.
- Review process quality separately from outcome quality; classify luck and bad luck explicitly.
- Framework revisions are versioned. A single failed forecast creates a change candidate, not an immediate rewrite.
- Do not mark investment-sensitive notes `stage: validated` without the MyNotes human review gate.

## Required output

For a forecast, produce or update a MyNotes weekly snapshot with: one-sentence view, change from prior week, macro state, dominant causal chain, pricing, three scenarios, multi-asset map, stance, falsifiers, and frozen metadata.

For a maturity review, preserve the original judgment, score the forecast against the stated window and baselines, locate the broken causal link, and create transferable lessons plus framework-change candidates.

For a framework module, define the object and boundary, mechanism chain, state dependence, observable indicators, pricing, scenarios, asset mapping, counterexamples, evidence maturity, open questions, and version log.

## MyNotes locations

- Durable method and MOC: `200 Areas/210 资产配置/218 框架研究/宏观策略判断体系/`
- Framework modules: `.../框架库/`
- Evidence cards: `.../指标与证据/`
- Historical cases: `.../历史案例/`
- Weekly snapshots and maturity reviews: `500 Journal/530 Weekly/宏观策略/`
- Canonical templates: `900 Assets/910 Templates/TPL-Macro-*.md`

Read only the references needed for the selected route. Use `references/note-contracts.md` for exact filenames, frontmatter, and review status.

**Required companion for MyNotes operations:** use `mynotes-knowledge-manager` for vault routing, source-file safety, Obsidian schema, and the human review gate. Use `assets-score` only when the user explicitly requests the automated report-scoring/archive path.
