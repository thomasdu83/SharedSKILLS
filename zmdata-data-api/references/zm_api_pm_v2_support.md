# PM V2 Supporting Lookup 接口

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

## 产品/母基金列表(pm_info_list)

获取可访问的产品/母基金列表，可用于选择后续接口所需的 `pm_id`。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id_list | 母基金 ID 列表 | list | 否 | 默认空列表，不按该维度过滤 |
| fund_manage_company | 基金管理人筛选 | list | 否 | 默认空列表 |
| investment_advisor | 投顾筛选 | list | 否 | 默认空列表 |
| strategy | 策略筛选 | list | 否 | 默认空列表 |
| tag | 标签筛选 | list | 否 | 默认空列表 |
| project_manager | 项目经理筛选 | list | 否 | 默认空列表 |
| clearflag | 清算状态筛选 | list | 否 | 默认空列表 |

**请求响应**

返回产品/母基金列表（DataFrame）。

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| pMID | 母基金 ID | int |
| aMACFundCode | AMAC 产品编码 | str |
| fundShortName | 产品简称 | str |
| frequency | 净值频率 | int/str |
| fundFlag | 产品标记 | str |
| establimentDate | 成立日期 | date |
| fundPutOnDate | 上架/上线日期 | date |
| maxTradingDay | 最新交易日 | date |
| days | 运行天数 | int |
| unitNAV | 单位净值 | float |
| accuNAV | 累计净值 | float |
| assetNetValue | 净资产 | float |
| benchmarkPortName | 基准名称 | str |
| accuYield | 累计收益 | float |
| annualAccuYield | 年化累计收益 | float |
| annualYield | 年化收益 | float |
| sharpe | Sharpe | float |
| maxDrawBackWeek | 周频最大回撤 | float |
| maxDrawBackDay | 日频最大回撤 | float |
| weekBenchYield | 周基准收益 | float |
| benchmarkPortID | 基准 ID | int |
| benchNetValue | 基准净值 | float |
| shares | 份额 | float |
| weekYield | 周收益 | float |
| weekAccuYield | 周累计收益 | float |
| totalYield | 总收益 | float |
| annualSD | 年化波动 | float |
| downRisk | 下行风险 | float |
| yiledYTD | 今年以来收益 | float |
| yieldCurrent | 当期收益 | float |
| threeMonthYield | 近三月收益 | float |
## PMInfo全局参数(pm_analysis_config)

获取 PMInfo 页面使用的全局默认参数。SDK 内部也会用它补全大多数 PM V2 接口的日期参数和默认基准。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| begin_date | 开始日期 | date | 否 | 用于服务端计算本期/上期窗口；不传时服务端按最近区间计算 |
| end_date | 结束日期 | date | 否 | 不传时服务端使用组合最新交易日 |

**请求响应**

返回全局参数配置（DataFrame）。其中第一行通常是服务端实时生成的“最新默认参数”。

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| id | 参数配置 ID；最新默认参数为 `0` | int |
| para_case_name | 参数配置名称 | str |
| para_case_content | 参数内容，包含日期、比较区间、默认基准等 | dict |
| comment | 备注 | str |
| create_time | 创建日期 | date |

`para_case_content` 常见键：`all_begin_date`、`all_end_date`、`begin_date`、`end_date`、`last_begin_date`、`last_end_date`、`compare_begin_date`、`compare_end_date`、`compare_last_begin_date`、`compare_last_end_date`、`all_compare_begin_date`、`all_compare_end_date`、`bench_id`、`bench_name`、`hold_strategy`。
## 组合基本信息(pm_base_info)

获取组合头部基本信息、现金类资产和核心绩效指标。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

返回组合基本信息（DataFrame，一般 1 行）。

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| 数据日期 | 数据日期 | date |
| 份额 | 产品份额 | float |
| 净资产 | 净资产 | float |
| 银行存款 | 银行存款金额 | float |
| 银行存款占比 | 银行存款占比 | float |
| 存出保证金 | 存出保证金金额 | float |
| 存出保证金占比 | 存出保证金占比 | float |
| 信托业保障基金 | 信托业保障基金金额 | float |
| 信托业保障基金占比 | 信托业保障基金占比 | float |
| 可用资金 | 可用资金 | float |
| 现金 | 现金金额 | float |
| 现金占比 | 现金占比 | float |
| 结算备付金 | 结算备付金金额 | float |
| 结算备付金占比 | 结算备付金占比 | float |
| 债券逆回购 | 债券逆回购金额 | float |
| 债券逆回购占比 | 债券逆回购占比 | float |
| date | 数据日期 | date |
| Share | 份额 | float |
| net_asset_value | 净资产 | float |
| fund_short_name | 产品简称 | str |
| amac_fund_code | AMAC 产品编码 | str |
| pm_id | 母基金 ID | int |
| frequency | 净值频率 | int/str |
| fund_reg_date | 产品成立/注册日期 | date |
| bench_mark_port_name | 比较基准名称 | str |
| unit_nav | 单位净值 | float |
| accu_nav | 累计净值 | float |
| IfAdd | 是否允许新增 | int/bool |
| IfModify | 是否允许修改 | int/bool |
| IfDelete | 是否允许删除 | int/bool |
| yield_week | 近一周收益 | float |
| yield_month | 近一月收益 | float |
| yield_3month | 近三月收益 | float |
| yield_year | 近一年收益 | float |
| yield_till_now | 成立以来收益 | float |
| sharpe | Sharpe | float |
| max_draw_back | 最大回撤 | float |
| yield_thisyear | 今年以来收益 | float |
## 策略赛道列表(pm_strategy_tracks)

获取指定策略下可用赛道及当前持仓子基金信息。风险配置、持仓分析和赛道配置类接口如果需要理解或枚举用户输入的赛道名称，优先调用本接口读取 `race_name`；实际可用赛道会随 `pm_id`、`strategy_type`、`end_date` 和组合持仓变化。

常见赛道名称示例：

| 策略类型 | 常见赛道名称 |
|----------|--------------|
| 股票多头(`strategy_type=1`) | `300指增`、`500指增`、`800指增`、`1000指增`、`主观多头`、`量化多头`、`定增增强`、`50增强`、`2000指增`、`A500指增` |
| 债券(`strategy_type=4`) | `高收益信用`、`转债增强`、`QDII信用`、`中长期信用`、`中短期利率`、`REITs`、`长期利率`、`中高收益信用`、`权益增强`、`可转债多头`、`可转债中性` |
| CTA(`strategy_type=5`) | `期货高频`、`期权`、`套利`、`股指`、`期货主观`、`短周期趋势CTA`、`中周期趋势CTA`、`长周期趋势CTA`、`跨境套利`、`期货指增`、`CTA多策略` |
| 市场中性(`strategy_type=3`) | `T0`、`300中性`、`1000中性`、`500中性`、`融券多空`、`做市`、`其他对冲`、`ETF套利` |

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |
| end_date | 结束日期 | date | 否 | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| strategy_type | 策略类型 | int |
| fund_short_name | 子基金简称 | str |
| fund_id | 子基金 ID | int |
| frequency | 净值频率 | int/str |
| fund_manage_company | 基金管理人 | str |
| subscrin_date | 申购/持有起始日期 | date |
| ratio | 持仓占比 | float |
| race_name | 赛道名称；用户输入赛道过滤条件时应使用该字段值，例如 `1000指增`、`500指增`、`期货高频`、`中长期信用` | str |
| market_value | 市值 | float |
| invest_typeII | 投资二级分类 | str |
| weight | 权重 | float |
| weight_one | 归一权重 | float |
| invest_weight | 投资权重 | float |
| invest_weight_one | 归一投资权重 | float |
## 策略比较基准(pm_strategy_benchmark)

获取指定策略默认比较基准。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| pm_id | 母基金 ID | int | 是 | 从 `pm_info_list` 结果中选取 |
| strategy_type | 策略类型 | int | 是 | 见通用说明 |

**请求响应**

| 字段 | 字段说明 | 类型 |
|------|----------|------|
| PMID | 母基金 ID | int |
| YieldSubType | 收益子类型 | int |
| strategytype | 策略类型 | int |
| BenchmarkPortName | 基准名称 | str |
| BenchmarkPortID | 基准 ID | int |
| BenchmarkPortType | 基准类型 | int/str |
