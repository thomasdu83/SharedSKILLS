# PMInfo 四个 Tab 接口盘点 Review

日期：2026-05-14

来源：`http://10.168.40.65:2001/PMInfo/10287` 前端资源与懒加载 chunk。in-app browser 专用连接本轮超时，因此本文件先基于页面加载的同一批 webpack 资源反查接口；等后续能接入浏览器 Network/Console 时，再补充真实响应样例。

优先级列说明：`P0` 是四个 tab 主分析链路或 skills 首批应覆盖能力；`P1` 是有分析价值但参数语义、展示条件或长期稳定性还需要确认的能力；`P2` 是页面支持、权限、下载或旧 webservice 类接口，默认不进入 skills，必要时只作为 SDK 内部支持。

P1 参数语义补充来源：`/Users/lee/git/zm_pm_svr` 服务端代码，重点核对 `app/allocation/views.py`、`app/allocation/service.py`、`app/advistor/views.py`、`app/advistor/service.py`、`app/factor/views.py`、`app/factor/service.py`、`app/risk_control/views.py`、`app/risk_control/service.py`。

## 采集范围

- 页面容器：`/PMInfo/:pmID`，chunk `44`
- 组合表现：chunk `367` 及子组件 `235/267/314/218`
- 资产配置：chunk `419` 及子组件 `257/384/278/172/411/169/403/168/237/215/486/171`
- 风险配置：chunk `336` 及子组件 `304/313/320/408/293/73/77/78/224/225`
- 持仓分析：chunk `404` 及子组件 `426/340/274/173/216/214/144/193/217/222/223/228/258/348/443`

## 页面公共接口

| Priority | Raw endpoint | Method | UI trigger | 接口语义(功能) | Request params from frontend | Existing SDK API | Proposed SDK API | Skills parameters | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P2 | `webservice/pm/data/combine/queryPrivilege` | GET | 页面初始化权限 | 判断当前用户是否有页面/组合访问权限。 | `pmID` | no | no wrapper | no | 权限/页面可见性，不建议进 skills |
| P2 | `zmpmapi/allocation/get_pm_trading_day` | POST | 页面初始化日期区间 | 获取组合从首个净值日到最新净值日的交易日列表，并返回 1/3/6/12 个月、今年以来、成立以来等默认起点。 | `pm_id` | no | `pm_trading_days` | `pm_id` | 暂不进入 P1/skills；仅作为 SDK 支持接口时再实现。`UserID` 仅有一个硬编码特殊 case，不建议暴露 |
| P2 | `zmpmapi/fof/get_global_params` | POST | 页面初始化全局参数 | 获取前端依赖的默认区间、持有策略、比较基准等页面全局配置。 | `pm_id`, `type=1`, `begin_date`, `end_date` | no | `pm_analysis_config` | `pm_id` | 更像支持接口 |
| P0 | `zmpmapi/fof/get_pm_base_info` | POST | 页面头部基本信息 | 获取组合基本信息和头部指标，用于回答组合名称、管理人、最新统计等问题。 | `pm_id`, `end_date` | no | `pm_base_info` | `pm_id`, optional `end_date` | 建议暴露 |
| P2 | `/zmpmapi/allocation/get_pm_hold_all` | POST | 页面初始化子基金跳转映射 | 获取组合历史持有基金的名称到 `fund_id` 映射，服务端同时返回基金全称和去后缀简称两套 key。 | `pm_id` | no | `pm_hold_fund_map` | `pm_id` | 暂不进入 P1/skills；主要用于子基金跳转/名称解析 |
| P2 | `webservice/pm/fof/fundList` | GET | 左侧基金列表 | 获取旧版左侧基金列表。 | none | no | no wrapper | no | 旧 webservice，不属于 zm_pm_svr V2 主体 |

## 组合表现

| Priority | Raw endpoint | Method | UI block | 接口语义(功能) | Request params from frontend | Existing SDK API | Proposed SDK API | Skills parameters | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P0 | `zmpmapi/fof/get_performance_trend` | POST | 净值曲线 | 获取组合累计净值、基准、连续回撤、累计超额等图表序列。 | `pm_id`, `end_date`, `base_date` | no | `pm_performance_trend` | `pm_id`, optional `end_date`, optional `base_date` | 图表版 |
| P0 | `zmpmapi/fof/get_performance_trend_list` | POST | 组合净值表 | 获取组合净值明细表。 | `pm_id`, `end_date` | `pm_nav` | keep `pm_nav`; optional alias `pm_performance_trend_table` | `pm_id`, optional `end_date` | 已封装 |
| P0 | `zmpmapi/fof/get_pm_performance` | POST | 绩效统计 | 获取组合区间收益、年化、回撤、胜率、Sharpe、下行标准差等绩效指标。 | `pm_id`, `begin_date`, `end_date` | no | `pm_performance_stats` | `pm_id`, optional `begin_date`, optional `end_date` | |
| P0 | `zmpmapi/fund/sub_fund_list` | POST | 旗下基金 | 获取组合旗下基金列表及区间表现。 | `pm_id`, `begin_date`, `end_date`, `sort` | `pm_subfunds` | keep `pm_subfunds` | `pm_id`, optional `begin_date`, optional `end_date` | 已封装 |

## 资产配置

| Priority | Raw endpoint | Method | UI block | 接口语义(功能) | Request params from frontend | Existing SDK API | Proposed SDK API | Skills parameters | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P0 | `zmpmapi/fof/get_pm_strategy_yield_contri` | POST | 分策略净值曲线 / 分策略净值 | 获取分策略净值、收益和贡献序列。 | `pm_id`, `freq`, `begin_date`, `end_date` | `pm_strategy_nav` | keep `pm_strategy_nav` | `pm_id`, optional `freq`, `begin_date`, `end_date` | 已封装 |
| P0 | `zmpmapi/fof/get_pm_strategy_performance_thisperiod` | POST | 分策略当期绩效 | 获取分策略当期区间绩效，并和上一可比区间对比。 | `pm_id`, `begin_date`, `end_date`, `last_begin_date`, `last_end_date` | no | `pm_strategy_period_performance` | `pm_id`, optional `begin_date`, optional `end_date` | Review confirmed：保留独立显式函数；上期区间参数 SDK 默认，不在 skills 强调 |
| P0 | `zmpmapi/fof/get_pm_strategy_performance_allperiod` | POST | 分策略全区间绩效 | 获取分策略成立以来/全区间绩效。 | `pm_id`, `begin_date`, `end_date` | no | `pm_strategy_full_period_performance` | `pm_id`, optional `begin_date`, optional `end_date` | Review confirmed：保留独立显式函数；不合并为 `period_scope` 参数 |
| P0 | `zmpmapi/allocation/get_strategy_allocations` | POST | 策略总览-资产配置 | 获取策略资产配置总览。 | `pm_id`, `begin_date`, `end_date` | `pm_asset_allocation` | keep `pm_asset_allocation` | `pm_id`, optional `begin_date`, optional `end_date` | 已封装 |
| P0 | `zmpmapi/allocation/get_strategy_allocations_contribute_new` | POST | 分策略累计盈亏图 | 获取分策略累计盈亏序列。 | `pm_id`, `begin_date`, `end_date` | no | `pm_strategy_cumulative_pnl` | `pm_id`, optional `begin_date`, optional `end_date` | 金额口径，前端展示“万” |
| P0 | `zmpmapi/allocation/get_pm_strategy_accu_yield` | POST | 分策略累计收益图 | 获取分策略累计收益率序列。 | `pm_id`, `begin_date`, `end_date` | no | `pm_strategy_cumulative_return` | `pm_id`, optional `begin_date`, optional `end_date` | 收益率口径 |
| P1 | `zmpmapi/allocation/get_strategy_allocations_contribute_new_year` | POST | 分策略年度/区间贡献 | 按 `freq` 对分策略累计盈亏取期末值再做差分，得到每个周期内各策略盈亏增量。 | `pm_id`, `freq`, `begin_date`, `end_date` | no | `pm_strategy_pnl_by_period` | `pm_id`, optional `freq`, optional `end_date` | 服务端只使用 `pm_id`、`end_date`、`freq`；`begin_date` 被前端传入但服务端未接收。`freq` 建议限制为 `W/M/Q/Y`，默认 `Y` |
| P1 | `zmpmapi/allocation/brinson_momentums` | POST | 资产配置收益/Brinson | Brinson 归因时序，返回各策略的累计归因和单期归因变化。 | `pm_id`, `begin_date`, `end_date`, `brinson_type` | no | `pm_brinson_attribution` | `pm_id`, optional `begin_date`, optional `end_date`, optional `brinson_type=4` | `brinson_type`: `1` 交互收益，`2` 资产配置收益，`3` 选基收益，`4` 总超额 |
| P0 | `zmpmapi/fof/get_pm_performance_corr` | POST | 策略相关性统计 | 获取策略之间的相关性矩阵。 | `pm_id`, `begin_date`, `end_date` | no | `pm_strategy_correlation` | `pm_id`, optional `begin_date`, optional `end_date` | |
| P1 | `zmpmapi/allocation/get_strategy_allocations_contr` | POST | 策略和基准比较图 | 策略净值与比较基准净值的归一化对比，并计算策略与基准的周度收益差。 | `pm_id`, `begin_date`, `end_date`, `strategy_type`, `base_date`, `bench_id` | no | `pm_strategy_benchmark_comparison` | `pm_id`, `strategy_type`, `bench_id`, optional `begin_date`, optional `end_date`, optional `base_date` | 原建议名 `pm_strategy_allocation_contribution` 不准确；`base_date` 为归一化基期，不传时以首个有效点归一 |
| P0 | `zmpmapi/fof/get_strategy_performance_list` | POST | 策略表现统计表 | 获取指定策略的日度/区间表现统计表。 | `pm_id`, `strategy_type`, `begin_date`, `end_date`, `bench_id` | no | `pm_strategy_performance_list` | `pm_id`, `strategy_type`, optional dates, optional `bench_id` | |
| P0 | `zmpmapi/fof/get_pm_strategy_bench` | POST | 策略比较基准 | 获取指定策略默认比较基准。 | `pm_id`, `strategy_type` | no | `pm_strategy_benchmark` | `pm_id`, `strategy_type` | 多个 tab 共用 |
| P0 | `zmpmapi/allocation/get_strategy_race_list` | POST | 赛道筛选 | 获取指定策略下可用赛道列表。 | `pm_id`, `end_date`, `strategy_type` | no | `pm_strategy_tracks` | `pm_id`, `strategy_type`, optional `end_date` | 支持接口，可进 skills |
| P0 | `zmpmapi/allocation/get_strategy_race_allocation` | POST | 策略表现-赛道配置 | 获取策略下各赛道配置比例。 | `pm_id`, `strategy_type`, `begin_date`, `end_date` | `pm_track_allocation` | `pm_strategy_track_allocation` | `pm_id`, `strategy_type`, optional dates | 新增语义化 API；保留 `pm_track_allocation` 向后兼容 |
| P0 | `zmpmapi/allocation/get_strategy_revenue` | POST | 分赛道累计盈亏 | 获取策略下各赛道累计盈亏。 | `pm_id`, `strategy_type`, `end_date` | `pm_track_revenue` | `pm_strategy_track_cumulative_pnl` | `pm_id`, `strategy_type`, optional `end_date` | 新增语义化 API；保留 `pm_track_revenue` 向后兼容 |
| P0 | `zmpmapi/allocation/get_strategy_race_accu_yield` | POST | 分赛道累计收益 | 获取策略下各赛道累计收益率。 | `pm_id`, `strategy_type`, `begin_date`, `end_date` | no | `pm_strategy_track_cumulative_return` | `pm_id`, `strategy_type`, optional dates | |
| P0 | `zmpmapi/allocation/get_strategy_race_contri` | POST | 分赛道贡献 | 获取策略下各赛道收益贡献。 | `pm_id`, `strategy_type`, `begin_date`, `end_date` | no | `pm_strategy_track_contribution` | `pm_id`, `strategy_type`, optional dates | |

## 风险配置

| Priority | Raw endpoint | Method | UI block | 接口语义(功能) | Request params from frontend | Existing SDK API | Proposed SDK API | Skills parameters | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P0 | `zmpmapi/fof_fund/calc_strategy_asset_exposure_timing` | POST | 大类配置序列图 | 获取组合指定策略的大类资产暴露时间序列。 | `pm_id_list`, `pm_id`, `end_date`, `strategy_type` | no | `pm_risk_asset_exposure_trend` | `pm_id`, `strategy_type`, optional `end_date` | `pm_id_list=[pm_id]` SDK 默认 |
| P0 | `zmpmapi/risk_control/risk_exposure_asset_by_fund` | POST | 大类-按基金暴露 | 获取子基金大类资产暴露截面和持仓比例加权平均。 | `pm_id`, `end_date`, `strategy_type` | no | `pm_risk_asset_exposure_by_fund` | `pm_id`, `strategy_type`, optional `end_date` | |
| P0 | `zmpmapi/risk_control/risk_exposure_asset_by_race` | POST | 大类-按赛道暴露 | 获取按赛道聚合的大类资产暴露和基准偏离。 | `pm_id`, `end_date`, `strategy_type` | no | `pm_risk_asset_exposure_by_track` | `pm_id`, `strategy_type`, optional `end_date` | |
| P0 | `zmpmapi/fof_fund/calc_strategy_style_exposure_timing` | POST | 风格配置序列图 | 获取组合指定策略的风格暴露时间序列。 | `pm_id_list`, `pm_id`, `end_date`, `strategy_type` | no | `pm_risk_style_exposure_trend` | `pm_id`, `strategy_type`, optional `end_date` | |
| P0 | `zmpmapi/risk_control/risk_exposure_style_by_fund` | POST | 风格-按基金暴露 | 获取子基金风格暴露截面、组合加权平均、比较基准和偏离。 | `pm_id`, `end_date`, `frequency=1`, `bench_id`, `strategy_type` | no | `pm_risk_style_exposure_by_fund` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id` | 服务端需要 `strategy_type` 和 `bench_id`，不接收 `frequency` |
| P0 | `zmpmapi/risk_control/risk_exposure_style_by_race` | POST | 风格-按赛道暴露 | 获取按赛道聚合的风格暴露和基准偏离。 | `pm_id`, `end_date`, `frequency=1`, `bench_id`, `strategy_type` | no | `pm_risk_style_exposure_by_track` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id` | constructed from `zmpmapi/risk_control/` + `apiurl` |
| P0 | `zmpmapi/fof_fund/calc_strategy_industry_exposure_timing` | POST | 行业/久期配置序列图 | 获取股票/中性策略行业暴露序列，或债券策略久期暴露序列。 | `pm_id_list`, `pm_id`, `end_date`, `strategy_type` | no | `pm_risk_industry_exposure_trend` | `pm_id`, `strategy_type`, optional `end_date` | 债券策略下 UI 文案是“久期配置” |
| P0 | `zmpmapi/risk_control/risk_exposure_industry_by_fund` | POST | 行业/久期-按基金暴露 | 获取子基金行业/久期暴露截面、组合加权平均、比较基准和偏离。 | `pm_id`, `end_date`, `frequency=1`, `bench_id`, `strategy_type` | no | `pm_risk_industry_exposure_by_fund` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id` | constructed |
| P0 | `zmpmapi/risk_control/risk_exposure_industry_by_race` | POST | 行业/久期-按赛道暴露 | 获取按赛道聚合的行业/久期暴露和基准偏离。 | `pm_id`, `end_date`, `frequency=1`, `bench_id`, `strategy_type` | no | `pm_risk_industry_exposure_by_track` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id` | constructed |
| P0 | `zmpmapi/fof_fund/calc_strategy_credit_exposure_timing` | POST | 信用配置序列图 | 获取债券策略信用暴露时间序列。 | `pm_id_list`, `pm_id`, `end_date`, `strategy_type` | no | `pm_risk_credit_exposure_trend` | `pm_id`, `strategy_type`, optional `end_date` | 主要债券策略 |
| P0 | `zmpmapi/risk_control/risk_exposure_credit_by_fund` | POST | 信用-按基金暴露 | 获取子基金信用暴露截面、组合加权平均、比较基准和偏离。 | `pm_id`, `end_date`, `frequency=1`, `bench_id`, `strategy_type` | no | `pm_risk_credit_exposure_by_fund` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id` | constructed |
| P0 | `zmpmapi/risk_control/risk_exposure_credit_by_race` | POST | 信用-按赛道暴露 | 获取按赛道聚合的信用暴露和基准偏离。 | `pm_id`, `end_date`, `frequency=1`, `bench_id`, `strategy_type` | no | `pm_risk_credit_exposure_by_track` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id` | constructed |
| P0 | `zmpmapi/factor/risk_factor_exposure` | POST | 因子暴露-基金 | 获取子基金风险因子暴露。 | `pm_id`, `begin_date`, `end_date`, `strategy_type` | no | `pm_risk_factor_exposure` | `pm_id`, `strategy_type`, optional dates | |
| P1 | `zmpmapi/factor/adviser_factor_sensitivity` | POST | 因子敏感性-投顾 | 投顾截面市场敏感性，输出投顾简称、仓位超低配、大小盘、成长价值、基差。 | `pm_id`, `begin_date`, `end_date`, `strategy_type` | no | `pm_adviser_factor_sensitivity` | `pm_id`, optional `end_date` | 服务端只实际使用 `pm_id`、`end_date`；不接收 `strategy_type`，不使用 `begin_date` |

## 持仓分析

| Priority | Raw endpoint | Method | UI block | 接口语义(功能) | Request params from frontend | Existing SDK API | Proposed SDK API | Skills parameters | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P0 | `zmpmapi/allocation/get_strategy_fund_net_value` | POST | 子基金净值曲线 | 获取指定策略下子基金净值曲线，并可拼接策略比较基准。 | `pm_id`, `end_date`, `strategy_type`, `compare_end_date`, `sorce_id_list`, `race_name_list`, `is_origin`, `bench_id` | no | `pm_holding_fund_navs` | `pm_id`, `strategy_type`, optional `end_date`, optional `race_name_list`, optional `is_origin`, optional `bench_id` | `sorce_id_list` 拼写按前端保留；skills 可不暴露 |
| P2 | `zmpmapi/allocation/get_strategy_fund_net_value_download` | POST | 下载子基金净值 | 下载指定策略下子基金净值数据。 | same as above | no | no wrapper | no | 下载接口不建议进 skills |
| P0 | `zmpmapi/allocation/get_strategy_race_list` | POST | 赛道筛选 | 获取指定策略下可用赛道列表。 | `pm_id`, `end_date`, `strategy_type` | no | `pm_strategy_tracks` | `pm_id`, `strategy_type`, optional `end_date` | 与资产配置共用 |
| P0 | `zmpmapi/fof/get_pm_strategy_bench` | POST | 策略比较基准 | 获取指定策略默认比较基准。 | `pm_id`, `strategy_type` | no | `pm_strategy_benchmark` | `pm_id`, `strategy_type` | 与资产配置共用 |
| P0 | `zmpmapi/fund_similar/fund_performance` | POST | 子基金绩效/同类对比 | 获取子基金绩效统计及同类组合对比。 | `pm_id`, `begin_date`, `end_date`, `strategy_type`, `last_*`, `compare_*` | no | `pm_holding_fund_performance` | `pm_id`, `strategy_type`, optional dates | compare/last 区间建议 SDK 默认 |
| P0 | `zmpmapi/fund/pms_current_fund_statis` | POST | 当前子基金统计 | 获取当前持仓子基金统计。 | `pm_id`, `bench_id`, `end_date`, `strategy_type`, `race_name_list` | no | `pm_holding_current_fund_stats` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id`, optional `race_name_list` | |
| P0 | `zmpmapi/fund/pms_historical_fund_statis` | POST | 历史子基金统计 | 获取历史持仓子基金统计。 | `pm_id`, `begin_date`, `end_date`, `strategy_type`, `bench_id`, `race_name_list` | no | `pm_holding_historical_fund_stats` | `pm_id`, `strategy_type`, optional dates, optional `bench_id`, optional `race_name_list` | |
| P0 | `zmpmapi/fund/calcSubFundYieldDecompose` | POST | 子基金收益贡献分解 | 获取子基金收益贡献分解。 | `pm_id`, `strategy_type`, `freq`, `end_date` | no | `pm_holding_yield_decomposition` | `pm_id`, `strategy_type`, optional `freq`, optional `end_date` | `freq`: `W/M/Q` |
| P0 | `zmpmapi/fund/calcSubFundCorr` | POST | 子基金相关性 | 获取子基金之间的相关性矩阵。 | `pm_id`, `begin_date`, `end_date`, `strategy_type`, `is_history`, `corr_type` | no | `pm_holding_fund_correlation` | `pm_id`, `strategy_type`, optional dates, optional `corr_type` | |
| P0 | `zmpmapi/fund/calc_subfund_corr_race` | POST | 子基金赛道相关性 | 获取子基金在赛道维度的相关性矩阵。 | `pm_id`, `begin_date`, `end_date`, `strategy_type`, `is_history`, `corr_type`, `race_name_list` | no | `pm_holding_track_correlation` | `pm_id`, `strategy_type`, optional dates, optional `corr_type`, optional `race_name_list` | |
| P1 | `zmpmapi/advistor/yield_corr_track` | POST | 投顾/赛道相关性 | 同一赛道内投顾/基金公司收益相关性；股票多头用基准超额收益，其他策略用收益率。 | `pm_id`, `end_date`, `strategy_type`, `compare_end_date`, `bench_id` | no | `pm_adviser_track_correlation` | `pm_id`, `strategy_type`, optional `end_date`, optional `compare_begin_date`, optional `bench_id` | `advistor` 是后端拼写；`compare_end_date` route 必填但下游基本未使用，SDK 可默认等于 `end_date` |
| P1 | `zmpmapi/advistor/yield_corr_sequence_track` | POST | 赛道相关性序列 | 赛道平均收益之间的 13 周滚动相关性序列；股票多头先扣基准收益。 | `pm_id`, `end_date`, `strategy_type`, `compare_end_date`, `bench_id` | no | `pm_adviser_track_correlation_trend` | `pm_id`, `strategy_type`, optional `end_date`, optional `bench_id` | 服务端不接收 `compare_begin_date`；`compare_end_date` 下游基本未使用，SDK 可默认等于 `end_date` |
| P1 | `zmpmapi/advistor/yield_corr_advistor` | POST | 投顾相关性 | 按投顾/基金公司合成净值后计算收益相关性；股票多头用基准超额收益，其他策略用收益率。 | `pm_id`, `end_date`, `strategy_type`, `compare_begin_date`, `compare_end_date`, `bench_id` | no | `pm_adviser_correlation` | `pm_id`, `strategy_type`, optional `end_date`, optional `compare_begin_date`, optional `bench_id` | `compare_end_date` route 必填但下游基本未使用，SDK 可默认等于 `end_date`；股票多头最好传 `bench_id` |
| P0 | `zmpmapi/factor/risk_factor_exposure` | POST | 持仓因子分析-基金 | 获取子基金风险因子暴露。 | `pm_id`, `begin_date`, `end_date`, `strategy_type` | no | `pm_risk_factor_exposure` | `pm_id`, `strategy_type`, optional dates | 与风险配置共用 |
| P1 | `zmpmapi/factor/adviser_factor_sensitivity` | POST | 持仓因子敏感性-投顾 | 投顾截面市场敏感性，输出投顾简称、仓位超低配、大小盘、成长价值、基差。 | `pm_id`, `begin_date`, `end_date`, `strategy_type` | no | `pm_adviser_factor_sensitivity` | `pm_id`, optional `end_date` | 与风险配置共用；服务端不接收 `strategy_type`，不使用 `begin_date` |
| P2 | `zmpmapi/fund_similar/fund_exposure` | POST | 债券持仓暴露/同类对比 | 前端指向的债券持仓暴露/同类对比接口。 | `pm_id`, `begin_date`, `end_date`, `strategy_type` | no | no wrapper | no | Review confirmed：忽略。当前 `/Users/lee/git/zm_pm_svr` 未找到该 route |
| P2 | `zmpmapi/fund_similar/fund_exposure_industry` | POST | 持仓行业暴露/同类对比 | 前端指向的持仓行业暴露/同类对比接口。 | `pm_id`, `end_date`, `frequency=1`, `bench_id` | no | no wrapper | no | Review confirmed：忽略。当前服务端未找到该 route |
| P1 | `zmpmapi/risk_control/risk_exposure_asset_by_fund` | POST | 持仓大类暴露 | 子基金大类资产暴露截面和持仓比例加权平均。 | `pm_id`, `end_date`, `frequency=1`, `bench_id` | no | `pm_holding_asset_exposure_by_fund` | `pm_id`, `strategy_type`, optional `end_date` | 服务端需要 `strategy_type`，不接收 `frequency`/`bench_id`；建议复用风险配置的 `pm_risk_asset_exposure_by_fund` |
| P1 | `zmpmapi/risk_control/risk_exposure_style_by_fund` | POST | 持仓风格暴露 | 子基金风格暴露截面、组合加权平均、比较基准和偏离。 | `pm_id`, `end_date`, `frequency=1`, `bench_id` | no | `pm_holding_style_exposure_by_fund` | `pm_id`, `strategy_type`, `bench_id`, optional `end_date` | 服务端需要 `strategy_type` 和 `bench_id`，不接收 `frequency`；建议复用风险配置的 `pm_risk_style_exposure_by_fund` |

## Proposed Interface Taxonomy

| Analysis area | User question it answers | Proposed SDK APIs | Include in skills? | Rationale |
|---|---|---|---|---|
| `supporting_lookup` | 这个组合是谁、有哪些可用日期/策略/子基金映射？ | `pm_base_info`, `pm_strategy_tracks`, `pm_strategy_benchmark` | partial | Review confirmed：`pm_trading_days`、`pm_hold_fund_map` 暂不进入 P1/skills；配置接口隐藏 |
| `portfolio_performance` | 组合整体表现如何？收益、回撤、净值、超额如何？ | `pm_performance_trend`, `pm_nav`, `pm_performance_stats`, `pm_subfunds` | yes | 覆盖组合表现 tab |
| `asset_allocation` | 组合的策略/资产/赛道配置及贡献如何？ | `pm_asset_allocation`, `pm_strategy_nav`, `pm_strategy_cumulative_pnl`, `pm_strategy_cumulative_return`, `pm_strategy_pnl_by_period`, `pm_brinson_attribution`, `pm_strategy_correlation`, `pm_strategy_benchmark_comparison`, `pm_strategy_performance_list`, `pm_strategy_track_allocation`, `pm_strategy_track_cumulative_pnl`, `pm_strategy_track_cumulative_return`, `pm_strategy_track_contribution` | yes | 覆盖资产配置 tab；`pm_track_allocation`/`pm_track_revenue` 仅保留向后兼容 |
| `risk_allocation` | 组合在资产、风格、行业/久期、信用、因子上的风险暴露如何？ | `pm_risk_asset_exposure_*`, `pm_risk_style_exposure_*`, `pm_risk_industry_exposure_*`, `pm_risk_credit_exposure_*`, `pm_risk_factor_exposure`, `pm_adviser_factor_sensitivity` | yes | 按风险概念命名，不按后端 `risk_control`/`fof_fund` 命名 |
| `holding_analysis` | 持仓子基金表现、贡献、相关性和投顾/赛道相关性如何？ | `pm_holding_fund_navs`, `pm_holding_fund_performance`, `pm_holding_current_fund_stats`, `pm_holding_historical_fund_stats`, `pm_holding_yield_decomposition`, `pm_holding_fund_correlation`, `pm_holding_track_correlation`, `pm_adviser_track_correlation`, `pm_adviser_track_correlation_trend`, `pm_adviser_correlation`, reusable `pm_risk_*_exposure_by_fund` | yes | 覆盖持仓分析 tab；忽略 `fund_similar/fund_exposure*` 两个服务端缺失接口 |

## 初步优先级建议

P0：直接补齐四个 tab 的主分析能力，且参数清晰。

- `pm_base_info`
- `pm_performance_trend`
- `pm_nav`（已封装）
- `pm_performance_stats`
- `pm_subfunds`（已封装）
- `pm_strategy_nav`（已封装）
- `pm_strategy_period_performance`
- `pm_strategy_full_period_performance`
- `pm_asset_allocation`（已封装）
- `pm_strategy_cumulative_pnl`
- `pm_strategy_cumulative_return`
- `pm_strategy_correlation`
- `pm_strategy_tracks`
- `pm_strategy_benchmark`
- `pm_strategy_performance_list`
- `pm_strategy_track_allocation`（新增语义化 API；`pm_track_allocation` 保留兼容）
- `pm_strategy_track_cumulative_pnl`（新增语义化 API；`pm_track_revenue` 保留兼容）
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

P1：有价值但优先级低于主链路；进入首批实现/skills，但不包括 `pm_trading_days`、`pm_hold_fund_map`，并忽略两个 `fund_similar/fund_exposure*` 接口。

- `pm_brinson_attribution`
- `pm_strategy_pnl_by_period`
- `pm_strategy_benchmark_comparison`
- `pm_adviser_factor_sensitivity`
- `pm_adviser_track_correlation`
- `pm_adviser_track_correlation_trend`
- `pm_adviser_correlation`
- `pm_holding_asset_exposure_by_fund`
- `pm_holding_style_exposure_by_fund`

P2：不建议进入 skills 或仅作 SDK 内部/下载支持。

- `webservice/pm/data/combine/queryPrivilege`
- `webservice/pm/fof/fundList`
- `zmpmapi/fof/get_global_params`
- `zmpmapi/allocation/get_pm_trading_day`
- `/zmpmapi/allocation/get_pm_hold_all`
- `zmpmapi/allocation/get_strategy_fund_net_value_download`
- `zmpmapi/fund_similar/fund_exposure`
- `zmpmapi/fund_similar/fund_exposure_industry`

## Review Decisions Confirmed

- [x] 保留 `pm_*` 命名规范。
- [x] `strategy_type`：如果接口有这个参数则暴露并使用，取值沿用：`1 股票多头，3 市场中性，4 债券，5 CTA，9 ETF`。
- [x] `pm_strategy_period_performance` 与 `pm_strategy_full_period_performance`：保留两个显式函数，不合并为带 `period_scope` 的单一函数；实现时可共享内部 helper。
- [x] `pm_track_allocation` / `pm_track_revenue`：新增更语义化 API `pm_strategy_track_allocation` / `pm_strategy_track_cumulative_pnl`，原函数保留向后兼容。
- [x] 首批进入范围：P0 + P1；P1 不包括 `pm_trading_days` / `pm_hold_fund_map`。
- [x] 忽略 `zmpmapi/fund_similar/fund_exposure` 和 `zmpmapi/fund_similar/fund_exposure_industry`，不进入 SDK/skills。

## Remaining Open Items

- [ ] 下一步是否需要用真实 token 对进入范围内接口逐个跑样例，补充响应字段和空数据情况。
