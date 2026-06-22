# PM V2 持仓分析接口

投后(组合)接口通用认证、默认日期和分文件索引见 `references/zm_api_portfolio_v2.md`。

日期和默认值处理：

- 显式传入的参数优先。
- 需要组合页面默认值的接口会读取 `pm_analysis_config` 返回的 `para_case_content`，再使用本地兜底。
- 本地兜底：开始日期 `2020-01-01`、结束日期今天、频率 `W`。`base_date` 未传时交由服务端处理。

策略类型 `strategy_type`：

| 值 | 含义 |
|----|------|
| 1 | 股票多头 |
| 3 | 市场中性 |
| 4 | 债券 |
| 5 | CTA |
| 9 | ETF |

返回字段来自 2026-05-15 运行 `/Users/lee/git/APIClientResearch/zm_tests/test_portfolio_v2_integration.py` 和同一批用例的字段探测，样例参数主要使用 `pm_id=10287`、`begin_date=2026-03-01`、`end_date=2026-04-23`。部分接口返回宽表，策略名、赛道名、基金名、基准名会随组合和参数变化，文档中列出本次样例观测到的动态列。

## 持仓子基金净值(pm_holding_fund_navs)

获取指定策略下子基金净值曲线，并可拼接策略比较基准。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| compare_end_date | 对比结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_end_date`，再等于 `end_date` |
| sorce_id_list | 来源 ID 列表 | list | 否 | 后端/前端字段拼写为 `sorce`，默认 `[]` |
| race_name_list | 赛道名称列表 | list | 否 | 默认 `[]` |
| is_origin | 是否原始净值 | int/bool | 否 | 默认 `0` |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 动态基金/基准列 | 子基金或基准净值序列；样例列：`中证800`、`宁苑沛华稳定增长一号`、`中信收益互换` | float |
## 持仓子基金绩效(pm_holding_fund_performance)

获取子基金绩效统计及同类组合对比。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| last_begin_date | 上期开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `last_begin_date`，再按本期长度自动前推 |
| last_end_date | 上期结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `last_end_date`，再按本期长度自动前推 |
| compare_begin_date | 同类比较开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_begin_date`，再等于 `begin_date` |
| compare_end_date | 同类比较结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_end_date`，再等于 `end_date` |
| compare_last_begin_date | 同类比较上期开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_last_begin_date`，再自动前推 |
| compare_last_end_date | 同类比较上期结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_last_end_date`，再自动前推 |

**请求响应**

返回 1 行 DataFrame，包含两个嵌套列：

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| this | 本期子基金绩效列表 | list[dict] |
| since | 持有以来子基金绩效列表 | list[dict] |

`this`/`since` 中的 dict 常见字段：`fund_short_name`、`max_trading_day`、`interval_yield`、`annual_yield`、`max_drawback`、`yield_rank`、`drawback_rank`、`similar_average_top_ten_yield`、`similar_average_after_ten_yield`、`similar_average_yield`、`similar_average_drawback`、`total_num`。`this` 还可能有 `last_yield_rank`、`last_interval_yield`；`since` 还可能有 `subscrin_date`。
## 当前子基金统计(pm_holding_current_fund_stats)

获取当前持仓子基金统计。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |
| race_name_list | 赛道名称列表 | list | 否 | 默认 `None`，不按赛道过滤 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| FundID | 子基金 ID | int |
| FundName | 子基金名称 | str |
| AccuYield | 累计收益 | float |
| AccuAnnualYield | 年化累计收益 | float |
| Yield | 区间收益 | float |
| AnnualYield | 年化收益 | float |
| SD | 波动率 | float |
| AnnualSD | 年化波动 | float |
| DownSD | 下行标准差 | float |
| MaxDrawBack | 最大回撤 | float |
| ReplenshmentWeek | 补充/恢复周数 | float |
| VaR | VaR | float |
| Sharpe | Sharpe | float |
| Sortino | Sortino | float |
| Calmar | Calmar | float |
## 历史子基金统计(pm_holding_historical_fund_stats)

获取历史持仓子基金统计。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 不传则不发送该字段，由服务端决定历史统计起点 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |
| race_name_list | 赛道名称列表 | list | 否 | 默认 `None`，不按赛道过滤 |

**请求响应**

字段同 `pm_holding_current_fund_stats`，并额外包含：

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| FundRegDate | 基金成立/注册日期 | date |
| RedeemDate | 赎回日期 | date |
## 子基金收益贡献分解(pm_holding_yield_decomposition)

获取子基金收益贡献分解。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| freq | 频率 | str | 否 | 默认 `W`，建议 `W/M/Q` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

返回 1 行嵌套结果：

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| bar | dict，键为交易日，值为该日子基金收益贡献列表 | dict |
| line | dict，键为基金/策略/基准名称，值为净值时间序列列表 | dict |
| tradingday | 交易日列表 | list |

`bar` 内部列表常见字段：`TradingDay`、`FundID`、`Yield`、`Name`、`NetValue`。`line` 内部列表常见字段：`TradingDay`、`NetValue`、`Type`、`Name`。
## 子基金相关性(pm_holding_fund_correlation)

获取子基金之间的相关性矩阵。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| is_history | 是否历史持仓 | int | 否 | 默认 `0` |
| corr_type | 相关性类型 | str | 否 | 默认 `Yield` |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| fund1 | 基金 1 | str |
| fund2 | 基金 2 | str |
| value | 相关系数 | float |
## 子基金赛道相关性(pm_holding_track_correlation)

获取子基金在赛道维度的相关性矩阵。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| is_history | 是否历史持仓 | int | 否 | 默认 `0` |
| corr_type | 相关性类型 | str | 否 | 默认 `Yield` |
| race_name_list | 赛道名称列表 | list | 否 | 默认 `None`，不按赛道过滤 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| 赛道 | 参与相关性计算的赛道名称列表；样例：`主观多头`、`A500指增`、`2000指增`、`1000指增`、`现金流增强` | list |
## 投顾/赛道相关性(pm_adviser_track_correlation)

获取同一赛道内投顾/基金公司收益相关性。股票多头使用 benchmark excess return，其他策略使用原始收益。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| compare_begin_date | 对比开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_compare_begin_date`，再兜底全局 `compare_begin_date` |
| compare_end_date | 对比结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_end_date`，再等于 `end_date` |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |

**请求响应**

返回投顾/赛道相关性 DataFrame。本次 `pm_id=10287`、股票多头样例返回空 DataFrame；有数据时通常为相关性矩阵或长表。
## 赛道相关性趋势(pm_adviser_track_correlation_trend)

获取不同策略赛道平均收益的 13 周滚动相关性趋势。股票多头会扣 benchmark。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| compare_end_date | 对比结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_end_date`，再等于 `end_date` |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| name | 图表/结果名称；样例：`时间序列超额相关性图` | str |
| value | list[dict]，每个 dict 包含 `trading_day` 和动态赛道对相关性列 | list |
## 投顾相关性(pm_adviser_correlation)

按投顾/基金公司合成净值后计算收益相关性。股票多头使用超额收益。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| compare_begin_date | 对比开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_compare_begin_date`，再兜底全局 `compare_begin_date` |
| compare_end_date | 对比结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `compare_end_date`，再等于 `end_date` |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| name | 图表/结果名称；样例：`多头超额收益相关性分析` | str |
| value | list[dict]，投顾相关性结果；本次样例为空列表 | list |
## 持仓大类资产暴露-按基金(pm_holding_asset_exposure_by_fund)

持仓分析 tab 使用的别名，等同于 `pm_risk_asset_exposure_by_fund`。

**请求参数**

同 `pm_risk_asset_exposure_by_fund`。

**请求响应**

同 `pm_risk_asset_exposure_by_fund`。
## 持仓风格暴露-按基金(pm_holding_style_exposure_by_fund)

持仓分析 tab 使用的别名，等同于 `pm_risk_style_exposure_by_fund`。

**请求参数**

同 `pm_risk_style_exposure_by_fund`。

**请求响应**

同 `pm_risk_style_exposure_by_fund`。
