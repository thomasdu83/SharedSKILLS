# PM V2 组合表现接口

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

## 组合净值曲线(pm_performance_trend)

获取组合累计净值、基准、连续回撤、累计超额等图表序列。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |
| base_date | 归一化基期 | date | 否 | 不再硬编码默认值；未传则传 `None`，由服务端决定 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| 动态产品名列 | 组合净值序列；样例列：`慧度·全天候1号` | float |
| 基准 | 基准净值序列 | float |
| 连续回撤 | 连续回撤 | float |
| 累计超额 | 累计超额 | float |
## 母基金净值/业绩走势(pm_nav)

获取组合净值明细表。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| trading_day | 交易日 | date |
| unit_netvalue | 单位净值 | float |
| accu_netvalue | 累计净值 | float |
| bench_netvalue | 基准净值 | float |
| accu_yield | 累计收益 | float |
| annual_accu_yield | 年化累计收益 | float |
| annual_yield | 年化收益 | float |
| max_draw_down | 最大回撤 | float |
## 组合绩效统计(pm_performance_stats)

获取组合区间收益、年化、回撤、胜率、Sharpe、下行标准差等绩效指标。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| period | 统计区间 | str |
| yield | 区间收益 | float |
| annual_yield | 年化收益 | float |
| annual_sd | 年化波动 | float |
| sharpe | Sharpe | float |
| down_sd | 下行标准差 | float |
| sd | 波动率 | float |
| day_win_rate | 日胜率 | float |
| max_draw_back | 最大回撤 | float |
| annual_down_sd | 年化下行标准差 | float |
| bench_yield | 基准收益 | float |
| accu_yield | 累计收益 | float |
| begin_date | 区间开始日期 | date |
| end_date | 区间结束日期 | date |
| pmid | 母基金 ID | int |
## 子基金列表(pm_subfunds)

获取组合旗下基金列表及区间表现。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_begin_date`，再兜底 `2020-01-01` |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `all_end_date`，再兜底今天 |
| sort | 排序条件 | dict | 否 | 默认 `{}` |

**请求响应**

返回子基金列表（DataFrame），可用于选择 `pm_subfund_nav` 所需的 `fund_id`。

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| fundID | 子基金 ID | int |
| quantity | 持仓数量 | float |
| marketValue | 市值 | float |
| unitCost | 单位成本 | float |
| weight | 持仓权重 | float |
| deltaRatio | 权重变化 | float |
| deltaMarketValue | 市值变化 | float |
| riskLevel | 风险等级 | str |
| movePL | 浮动盈亏 | float |
| fundName | 子基金名称 | str |
| frequency | 净值频率 | int/str |
| race | 赛道 | str |
| strategyClass | 策略分类 | str |
| applicationDate | 申购日期 | date |
| sourceID | 来源 ID | int |
| fundRegDate | 基金成立/注册日期 | date |
| aMACFundCode | AMAC 产品编码 | str |
| start_date | 区间开始日期 | date |
| end_date | 区间结束日期 | date |
| workweek | 工作周 | str/int |
| firstApplicationDate | 首次申购日期 | date |
| lastApplicationDate | 最近申购日期 | date |
| maxTradingDay | 最新交易日 | date |
| unitNAV | 单位净值 | float |
| accuNAV | 累计净值 | float |
| virtualNAV | 虚拟净值 | float |
| subscriptionAccuNAV | 申购口径累计净值 | float |
| dAYS | 持有天数 | int |
| lastWeightDay | 上期权重日期 | date |
| lastWeight | 上期权重 | float |
| weekAnnualYield | 周频年化收益 | float |
| thisYield | 本期收益 | float |
| totalYield | 总收益 | float |
| yearYieldYTD | 今年以来收益 | float |
| start_date_ytd | 今年以来起始日期 | date |
| monthYield | 近一月收益 | float |
| start_date_1m | 近一月起始日期 | date |
| threeMonthYield | 近三月收益 | float |
| start_date_3m | 近三月起始日期 | date |
| accuYield_Last | 上期累计收益 | float |
| totalPL | 总盈亏 | float |
| realizedPL | 已实现盈亏 | float |
| weekYield | 周收益 | float |
| putondate | 上线/投资日期 | date |
| cumdividend | 累计分红 | float |
## 子基金净值(pm_subfund_nav)

获取投后子基金净值。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| fund_id | 子基金 ID | int | 是 | 从 `pm_subfunds` 结果中选取 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| fund_id | 子基金 ID | int |
| trading_day | 交易日 | date |
| accu_nav | 累计净值 | float |
| source | 数据来源 | str |
