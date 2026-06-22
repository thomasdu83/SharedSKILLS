# PM API Expansion Discussion Summary

日期：2026-05-14

本文汇总本轮关于 PM 组合管理接口扩展的讨论、接口采集结论、review 决策和后续实施边界。目标项目为 `/Users/lee/git/zm_skills/zmdata-data-api`。

## 背景

当前 skills 中已有一部分组合管理（PM）相关接口，底层调用 `zm_pm_svr`，Client API 代码位于：

- `/Users/lee/git/APIClientResearch/zmdata/apis/portfolio_v2.py`

本轮需求是补齐前端页面 `http://10.168.40.65:2001/PMInfo/10287` 中四个 tab 的接口，并最终沉淀到：

- APIClientResearch 的 `portfolio_v2.py`
- 当前 skills 项目 `/Users/lee/git/zm_skills/zmdata-data-api`

四个 tab 为：

- 组合表现
- 资产配置
- 风险配置
- 持仓分析

## 已完成的调研

前端浏览器控制台无法直接稳定读取接口列表，因此改为分析 PMInfo 前端静态资源和服务端代码。

前端资源采集来源：

- PMInfo 页面 HTML
- `/static/js/app.d43b02cf91361865d07e.js`
- `/PMInfo/:pmID` 路由加载的 chunk：`44.28ec0ba6513324f223b7.js`

四个 tab 对应的主要 chunk：

- 组合表现：`367`，以及子 chunk `235/267/314/218`
- 资产配置：`419`，以及子 chunk `257/384/278/172/411/169/403/168/237/215/486/171`
- 风险配置：`336`，以及子 chunk `304/313/320/408/293/73/77/78/224/225`
- 持仓分析：`404`，以及子 chunk `426/340/274/173/216/214/144/193/217/222/223/228/258/348/443`

服务端语义校验来源：

- `/Users/lee/git/zm_pm_svr/app/allocation/views.py`
- `/Users/lee/git/zm_pm_svr/app/allocation/service.py`
- `/Users/lee/git/zm_pm_svr/app/advistor/views.py`
- `/Users/lee/git/zm_pm_svr/app/advistor/service.py`
- `/Users/lee/git/zm_pm_svr/app/factor/views.py`
- `/Users/lee/git/zm_pm_svr/app/factor/service.py`
- `/Users/lee/git/zm_pm_svr/app/risk_control/views.py`
- `/Users/lee/git/zm_pm_svr/app/risk_control/service.py`

## 项目归属修正

本轮一开始误在 `/Users/lee/idea-lab/portfolio-intelligence` 下创建过规划文档。后续确认该项目不是本次目标项目，已清理误放文件和相关 memory 记录。

已删除误放文件：

- `/Users/lee/idea-lab/portfolio-intelligence/docs/plans/2026-05-14-pm-api-inventory-review.md`
- `/Users/lee/idea-lab/portfolio-intelligence/docs/superpowers/plans/2026-05-14-pm-api-expansion-implementation-plan.md`

已从误放项目 memory 中移除 PM 接口扩展相关记录：

- `/Users/lee/idea-lab/portfolio-intelligence/memory/2026-05-14.md`

后续只应在正确项目继续：

- `/Users/lee/git/zm_skills/zmdata-data-api`

当前已保留的接口清单文档：

- `/Users/lee/git/zm_skills/zmdata-data-api/docs/plans/2026-05-14-pm-api-inventory-review.md`
- `/Users/lee/git/zm_skills/zmdata-data-api/docs/plans/2026-05-14-pm-api-business-review.html`

## Review 决策

1. 保留 `pm_*` 命名规范。
2. 如果接口本身有 `strategy_type` 参数，则 SDK/skills 中继续暴露并使用该参数。
3. `strategy_type` 取值沿用现有前端/服务端约定：
   - `1`：股票多头
   - `3`：市场中性
   - `4`：债券
   - `5`：CTA
   - `9`：ETF
4. `pm_strategy_period_performance` 和 `pm_strategy_full_period_performance` 保留两个显式函数，不合并为一个 `period_scope` 参数；实现时可以共享内部 helper。
5. `pm_track_allocation` / `pm_track_revenue` 增加更语义化 alias，同时保留旧接口兼容：
   - `pm_strategy_track_allocation`
   - `pm_strategy_track_cumulative_pnl`
6. 首批进入范围为 P0 和 P1。
7. P1 不包括：
   - `pm_trading_days`
   - `pm_hold_fund_map`
8. 忽略以下前端引用但本轮不接入的接口：
   - `zmpmapi/fund_similar/fund_exposure`
   - `zmpmapi/fund_similar/fund_exposure_industry`

## 现有 portfolio_v2 接口

`portfolio_v2.py` 中已有的 PM 相关接口包括：

- `pm_info_list` -> `POST /api/zmpmapi/fof/get_pm_info_list`
- `pm_nav` -> `POST /api/zmpmapi/fof/get_performance_trend_list`
- `pm_asset_allocation` -> `POST /api/zmpmapi/allocation/get_strategy_allocations`
- `pm_strategy_nav` -> `POST /api/zmpmapi/fof/get_pm_strategy_yield_contri`
- `pm_track_allocation` -> `POST /api/zmpmapi/allocation/get_strategy_race_allocation`
- `pm_track_revenue` -> `POST /api/zmpmapi/allocation/get_strategy_revenue`
- `pm_subfunds` -> `POST /api/zmpmapi/fund/sub_fund_list`
- `pm_subfund_nav` -> `/api/zmpmapi/fund/sub_fund_nav`

## 首批进入范围

### P0

P0 是四个 tab 中直接支撑核心分析链路的接口，优先进入 APIClientResearch 和 skills 文档。

- `pm_base_info`
- `pm_performance_trend`
- `pm_nav`
- `pm_performance_stats`
- `pm_subfunds`
- `pm_strategy_nav`
- `pm_strategy_period_performance`
- `pm_strategy_full_period_performance`
- `pm_asset_allocation`
- `pm_strategy_cumulative_pnl`
- `pm_strategy_cumulative_return`
- `pm_strategy_correlation`
- `pm_strategy_tracks`
- `pm_strategy_benchmark`
- `pm_strategy_performance_list`
- `pm_strategy_track_allocation`
- `pm_strategy_track_cumulative_pnl`
- `pm_strategy_track_cumulative_return`
- `pm_strategy_track_contribution`
- `pm_risk_asset_exposure_trend`
- `pm_risk_asset_exposure_by_fund`
- `pm_risk_asset_exposure_by_track`
- `pm_risk_style_exposure_trend`
- `pm_risk_style_exposure_by_fund`
- `pm_risk_style_exposure_by_track`
- `pm_risk_industry_exposure_trend`
- `pm_risk_industry_exposure_by_fund`
- `pm_risk_industry_exposure_by_track`
- `pm_risk_credit_exposure_trend`
- `pm_risk_credit_exposure_by_fund`
- `pm_risk_credit_exposure_by_track`
- `pm_risk_factor_exposure`
- `pm_holding_fund_navs`
- `pm_holding_fund_performance`
- `pm_holding_current_fund_stats`
- `pm_holding_historical_fund_stats`
- `pm_holding_yield_decomposition`
- `pm_holding_fund_correlation`
- `pm_holding_track_correlation`

### P1

P1 是有分析价值、但需要更明确语义说明或可作为增强能力补充的接口。

- `pm_brinson_attribution`
- `pm_strategy_pnl_by_period`
- `pm_strategy_benchmark_comparison`
- `pm_adviser_factor_sensitivity`
- `pm_adviser_track_correlation`
- `pm_adviser_track_correlation_trend`
- `pm_adviser_correlation`
- `pm_holding_asset_exposure_by_fund`
- `pm_holding_style_exposure_by_fund`

### P2 或暂不接入

以下接口本轮不进入首批 SDK/skills 封装。

- `webservice/pm/data/combine/queryPrivilege`
- `webservice/pm/fof/fundList`
- `zmpmapi/fof/get_global_params`
- `zmpmapi/allocation/get_pm_trading_day`
- `/zmpmapi/allocation/get_pm_hold_all`
- `zmpmapi/allocation/get_strategy_fund_net_value_download`
- `zmpmapi/fund_similar/fund_exposure`
- `zmpmapi/fund_similar/fund_exposure_industry`

## P1 服务端语义确认

`pm_brinson_attribution`

- 对应 Brinson 归因。
- `brinson_type` 语义：
  - `1`：交互收益
  - `2`：资产配置收益
  - `3`：选基收益
  - `4`：总超额
- skills 默认建议使用 `brinson_type=4`。

`pm_strategy_pnl_by_period`

- 服务端实际使用 `pm_id`、`end_date`、`freq`。
- 前端可能发送 `begin_date`，但服务端 route 不接收或不使用。
- `freq` 是 pandas resample 频率，建议暴露 `W/M/Q/Y`，默认 `Y`。

`pm_strategy_benchmark_comparison`

- 对应服务端 `get_strategy_allocations_contr`。
- 实际语义不是“配置贡献”，而是策略净值与 benchmark 归一化净值、以及周度收益差异对比。

`pm_adviser_factor_sensitivity`

- 服务端实际使用 `pm_id`、`end_date`。
- route 不接收 `strategy_type`，`begin_date` 也未被使用。
- 输出顾问/公司横截面的市场敏感性指标，包括仓位超低配、大小盘、成长价值、基差。

`pm_adviser_track_correlation`

- 同策略赛道内顾问/公司相关性。
- 股票多头使用 benchmark excess return，其他策略使用原始收益。
- `compare_end_date` 在 route 层必填，但下游大多不使用，SDK 可默认等于 `end_date`。

`pm_adviser_track_correlation_trend`

- 13 周滚动相关性，用于比较不同策略赛道平均收益的相关性趋势。
- 股票多头会扣 benchmark。
- 没有 `compare_begin_date`，`compare_end_date` 大多不参与实际计算。

`pm_adviser_correlation`

- 顾问/公司组合净值相关性。
- 股票多头使用超额收益。
- `compare_begin_date` 可限制起始日期，`compare_end_date` 可默认等于 `end_date`。

`pm_holding_asset_exposure_by_fund` / `pm_holding_style_exposure_by_fund`

- 与风险配置中的按基金维度暴露能力一致，只是在持仓分析 tab 使用。
- 服务端需要 `strategy_type`。
- style 暴露还需要 `bench_id`。
- 前端的 `frequency` 参数服务端不接收，不建议在 skills 中暴露为重点参数。

## 后续实施顺序

建议后续按以下顺序继续：

1. 依据 `2026-05-14-pm-api-inventory-review.md` 修改 `/Users/lee/git/APIClientResearch/zmdata/apis/portfolio_v2.py`。
2. 先实现 P0 和确认后的 P1，不实现 P2/排除项。
3. 对现有接口保留兼容命名，同时增加语义化 alias。
4. 更新 `zmdata-data-api` skills 文档，重点说明必填参数、重要参数、默认值和业务语义。
5. 发布 APIClientResearch 新版本后，再在 skills 文档中引用新的 Client API 能力。

