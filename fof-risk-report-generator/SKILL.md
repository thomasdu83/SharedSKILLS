---
name: "FOF_Risk_Report_Generator"
description: "把投后归因规范落成可执行输出（文字/HTML）。当用户要一键生成FOF投后归因报告、复盘材料或需要可复现的落盘产物时调用。"
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

# FOF Risk Report Generator

## 目标

把现有投后归因规范（FOF_Risk_Attribution_Agent）与可执行脚本结合，生成：

- 文字版分析内容（stdout，可复制到邮件/纪要）
- HTML 分析报告（落盘文件）

## 依赖与前置条件

- 需要可访问 ZMData/投后接口的网络环境
- 需要设置投后接口 Key：
  - 环境变量 `ZM_PM_API_KEY` 或 `PM_API_KEY`
- 本 Skill 目录内包含可执行脚本：
  - `run.py`（固定入口）
  - `report.py`（实际实现）

## 调用方式（推荐）

### 1) 生成 HTML（默认）

```bash
python run.py
```

### 2) 仅生成文字版（不落盘 HTML）

```bash
python run.py --output-format text
```

### 3) 同时生成文字 + HTML，并固定区间与输出路径（用于复现同一份报告）

```bash
python run.py ^
  --pm-id 10898 ^
  --begin-date 2026-02-01 ^
  --end-date 2026-05-22 ^
  --output-format both ^
  --output-html .\灵活配置1号_2026-02-01_2026-05-22_表现分析.html
```

### 4) 直接用产品简称生成（自动匹配 pm_id）

```bash
python run.py --product-name 智胜进取1号 --begin-date 2026-01-01 --output-format text
```

## 输出口径

- 母层：`pm_nav` 区间切片计算区间收益与最大回撤
- 起点净值：使用“起始日的上一交易日”作为净值基准日（用于计算起点→区间内首个交易日的首段收益），并在报告元信息中展示该基准日
- 策略层：`pm_strategy_nav(freq="D")`，贡献按 `r(NetValue)×w(prev Ratio)` 汇总
- 赛道层：`pm_strategy_track_contribution` + `pm_strategy_track_allocation`
- 子基金层：优先基于 `pm_holding_yield_decomposition`，对 `bar.Yield` 自动做“累计/增量”识别；必要时回退到 `w×r`
- 因子：`pm_risk_factor_exposure` + `risk_factor_returns`；若暴露无时序，仅展示最新暴露与区间因子收益表现，不计算历史贡献

## 总结陈述（优化点）

- 总结段会按“母层结果 → 策略层贡献 → Brinson（配置/选基）→ 赛道层 → 子基金层 → 因子暴露与风险提示”的顺序串联关键结论
- 因子部分会额外给出“组合口径”的因子暴露 Top（按策略权重加权汇总）与对应风险隐患提示（如 size/beta/volatility/momentum/liquidity/valuation、以及 if/ic 基差因子）

## 何时调用

- 用户要求“生成/更新投后归因报告（HTML）”
- 用户要求“只要文字版复盘材料/路演话术”
- 需要把同一套口径交付给他人并可复现（固定 end_date + 输出路径）
