# PM V2 资产配置接口

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

## 资产配置(pm_asset_allocation)

获取策略资产配置总览。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| ratio | 配置比例 | float |
| market | 资产/策略分类 | str |
## 分策略净值(pm_strategy_nav)

获取分策略净值、收益和贡献序列。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| freq | 频率 | str | 否 | 默认 `W` |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| StockNetValue / BondNetValue / CTANetValue / MarketneutralityNetValue / ETFNetValue | 各策略净值 | float |
| StockRatio / BondRatio / CTARatio / MarketneutralityRatio / ETFRatio | 各策略配置比例 | float |
| StockYield / BondYield / CTAYield / MarketneutralityYield / ETFYield | 各策略收益 | float |
| StockContri / BondContri / CTAContri / MarketneutralityContri / ETFContri | 各策略贡献 | float |
## 分策略当期绩效(pm_strategy_period_performance)

获取分策略当期区间绩效，并和上一可比区间对比。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| last_begin_date | 上期开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `last_begin_date`，再按本期长度自动前推 |
| last_end_date | 上期结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `last_end_date`，再按本期长度自动前推 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| begin_date | 区间开始日期 | date |
| end_date | 区间结束日期 | date |
| strategy_type | 策略类型 | int |
| yield | 区间收益 | float |
| annual_yield | 年化收益 | float |
| yield_rank | 收益排名/分位 | float |
| avg_similar_Top10 | 同类前 10% 平均收益 | float |
| avg_similar_Last10 | 同类后 10% 平均收益 | float |
| avg_similar | 同类平均收益 | float |
| last_yield_rank | 上期收益排名/分位 | float |
## 分策略全区间绩效(pm_strategy_full_period_performance)

获取分策略成立以来/全区间绩效。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| begin_date | 区间开始日期 | date |
| end_date | 区间结束日期 | date |
| strategy_type | 策略类型 | int |
| yield | 区间收益 | float |
| max_draw_back | 最大回撤 | float |
| yield_rank | 收益排名/分位 | float |
| max_draw_back_rank | 最大回撤排名/分位 | float |
| avg_similar | 同类平均收益 | float |
| avg_similar_max_draw_down | 同类平均最大回撤 | float |
## 分策略累计盈亏(pm_strategy_cumulative_pnl)

获取分策略累计盈亏序列。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 股票多头 | 股票多头累计盈亏 | float |
| 债券 | 债券累计盈亏 | float |
| CTA | CTA 累计盈亏 | float |
| 市场中性 | 市场中性累计盈亏 | float |
| ETF | ETF 累计盈亏 | float |
| 总盈亏 | 总累计盈亏 | float |
## 分策略累计收益(pm_strategy_cumulative_return)

获取分策略累计收益率序列。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 股票多头 | 股票多头累计收益 | float |
| 债券 | 债券累计收益 | float |
| CTA | CTA 累计收益 | float |
| 市场中性 | 市场中性累计收益 | float |
| ETF | ETF 累计收益 | float |
## 分策略周期盈亏(pm_strategy_pnl_by_period)

按频率得到每个周期内各策略盈亏增量。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| freq | 频率 | str | 否 | 默认 `W`，建议 `W/M/Q/Y` |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 周期结束日 | date |
| data | dict，键为策略名/`总盈亏`，值为该周期盈亏增量 | dict |

样例 `data` 键：`股票多头`、`债券`、`CTA`、`市场中性`、`ETF`、`总盈亏`。
## Brinson归因(pm_brinson_attribution)

获取 Brinson 归因时序。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| brinson_type | 归因类型 | int | 否 | 默认 `4`；1 交互收益，2 资产配置收益，3 选基收益，4 总超额 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 股票多头 | 股票多头单期/累计归因值 | float |
| CTA | CTA 单期/累计归因值 | float |
| 市场中性/债券 | 市场中性/债券单期/累计归因值 | float |
| 股票多头总超额 | 股票多头总超额 | float |
| CTA总超额 | CTA 总超额 | float |
| 市场中性/债券总超额 | 市场中性/债券总超额 | float |
## 策略相关性(pm_strategy_correlation)

获取策略之间的相关性矩阵。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| stock | 股票多头相关性列 | float |
| bond | 债券相关性列 | float |
| cta | CTA 相关性列 | float |
| marketneutrality | 市场中性相关性列 | float |
| strategyname | 行策略名称 | str |
## 策略与基准比较(pm_strategy_benchmark_comparison)

获取策略净值与比较基准净值的归一化对比，并计算策略与基准的周度收益差异。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| base_date | 归一化基期 | date | 否 | 不再硬编码默认值；未传则传 `None`，由服务端决定 |

**请求响应**

返回策略与基准对比序列（DataFrame）。在本次 `pm_id=10287`、`strategy_type=1`、`bench_id=10001` 样例中返回空列 DataFrame；有数据时通常包含交易日、策略/基准归一化净值和收益差异类字段。
## 策略表现统计表(pm_strategy_performance_list)

获取指定策略的日度/区间表现统计表。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| bench_id | 基准 ID | int | 否 | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| accu_netvalue | 累计净值 | float |
| project_num | 项目/产品数 | int |
| ratio | 配置比例 | float |
| calc_cost | 计算成本 | float |
| market_value | 市值 | float |
| purchase_redeem | 申赎金额 | float |
| yield | 收益 | float |
| accu_yield | 累计收益 | float |
| annual_accu_yield | 年化累计收益 | float |
| annual_yield_ytd | 今年以来年化收益 | float |
| annual_yield | 年化收益 | float |
| annual_sd | 年化波动 | float |
## 策略赛道配置(pm_strategy_track_allocation)

获取指定策略下各赛道配置比例。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 动态赛道列 | 各赛道配置比例；样例列：`1000指增`、`2000指增`、`300指增`、`500指增`、`50增强`、`A500指增`、`主观多头`、`指数基金`、`现金流增强`、`量化多头`、`其他` | float |
## 策略赛道累计盈亏(pm_strategy_track_cumulative_pnl)

获取指定策略下各赛道累计盈亏。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 动态赛道列 | 各赛道累计盈亏；样例列同 `pm_strategy_track_allocation` | float |
## 策略赛道累计收益(pm_strategy_track_cumulative_return)

获取指定策略下各赛道累计收益率。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 动态赛道列 | 各赛道累计收益率；样例列：`1000指增`、`2000指增`、`300指增`、`A500指增`、`主观多头`、`现金流增强`、`量化多头` | float |
## 策略赛道贡献(pm_strategy_track_contribution)

获取指定策略下各赛道收益贡献。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 动态`赛道收益`列 | 各赛道收益；样例：`1000指增收益`、`主观多头收益` | float |
| 动态`赛道贡献`列 | 各赛道贡献；样例：`1000指增贡献`、`主观多头贡献` | float |
## 赛道配置(pm_track_allocation)

兼容旧接口名，等同于 `pm_strategy_track_allocation`。

**请求参数**

同 `pm_strategy_track_allocation`。

**请求响应**

同 `pm_strategy_track_allocation`。
## 赛道累计盈亏(pm_track_revenue)

兼容旧接口名，等同于 `pm_strategy_track_cumulative_pnl`。

**请求参数**

同 `pm_strategy_track_cumulative_pnl`。

**请求响应**

同 `pm_strategy_track_cumulative_pnl`。
