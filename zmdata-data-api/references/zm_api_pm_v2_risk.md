# PM V2 风险配置接口

投后(组合)接口通用认证、默认日期和分文件索引见 `references/zm_api_portfolio_v2.md`。

日期和默认值处理：

- 显式传入的参数优先。
- 需要组合页面默认值的接口会读取 `pm_analysis_config` 返回的 `para_case_content`，再使用本地兜底。
- 本地兜底：开始日期 `2020-01-01`、结束日期今天、频率 `W`。`base_date` 未传时交由服务端处理。

策略类型 `strategy_type`：


| 值   | 含义   |
| --- | ---- |
| 1   | 股票多头 |
| 3   | 市场中性 |
| 4   | 债券   |
| 5   | CTA  |
| 9   | ETF  |


赛道名称说明：

- 赛道名称按 `strategy_type` 不同而不同，按赛道聚合接口返回的 `RaceName` 就是用户可理解的细分赛道名称。
- 实际可用赛道会随 `pm_id`、`end_date` 和组合持仓变化，调用前如需枚举当前组合下可用赛道，优先使用 `pm_strategy_tracks(pm_id, strategy_type, end_date)`，读取返回的 `race_name`。
- 常见赛道名可参考下表；用户输入这些名称时，LLM 可直接按对应策略理解为赛道筛选或赛道聚合维度。


| 策略类型                    | 常见赛道名称                                                                                 |
| ----------------------- | -------------------------------------------------------------------------------------- |
| 股票多头(`strategy_type=1`) | `300指增`、`500指增`、`800指增`、`1000指增`、`主观多头`、`量化多头`、`定增增强`、`50增强`、`2000指增`、`A500指增`         |
| 债券(`strategy_type=4`)   | `高收益信用`、`转债增强`、`QDII信用`、`中长期信用`、`中短期利率`、`REITs`、`长期利率`、`中高收益信用`、`权益增强`、`可转债多头`、`可转债中性` |
| CTA(`strategy_type=5`)  | `期货高频`、`期权`、`套利`、`股指`、`期货主观`、`短周期趋势CTA`、`中周期趋势CTA`、`长周期趋势CTA`、`跨境套利`、`期货指增`、`CTA多策略`   |
| 市场中性(`strategy_type=3`) | `T0`、`300中性`、`1000中性`、`500中性`、`融券多空`、`做市`、`其他对冲`、`ETF套利`                               |


返回字段来自 2026-05-15 运行 `/Users/lee/git/APIClientResearch/zm_tests/test_portfolio_v2_integration.py` 和同一批用例的字段探测，样例参数主要使用 `pm_id=10287`、`begin_date=2026-03-01`、`end_date=2026-04-23`。部分接口返回宽表，策略名、赛道名、基金名、基准名会随组合和参数变化，文档中列出本次样例观测到的动态列。

## 大类资产暴露序列(pm_risk_asset_exposure_trend)

获取组合指定策略的大类资产暴露时间序列。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                          |
| ------------- | ------ | ---- | ---- | ------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                      |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                       |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |


**请求响应**


| 字段         | 字段说明        | 类型    |
| ---------- | ----------- | ----- |
| TradingDay | 交易日         | date  |
| 全A指数       | 股票资产暴露/基准口径 | float |
| 中债新综合总财富   | 债券资产暴露/基准口径 | float |
| 货币基准       | 现金/货币资产暴露   | float |


## 大类资产暴露-按基金(pm_risk_asset_exposure_by_fund)

获取子基金大类资产暴露截面和持仓比例加权平均。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                          |
| ------------- | ------ | ---- | ---- | ------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                      |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                       |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |


**请求响应**


| 字段              | 字段说明      | 类型    |
| --------------- | --------- | ----- |
| fund_short_name | 子基金简称     | str   |
| stock_bench     | 股票资产暴露    | float |
| bond_bench      | 债券资产暴露    | float |
| coin_bench      | 货币/现金资产暴露 | float |


## 大类资产暴露-按赛道(pm_risk_asset_exposure_by_track)

获取按赛道聚合的大类资产暴露和基准偏离。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                          |
| ------------- | ------ | ---- | ---- | ------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                      |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                       |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |


**请求响应**


| 字段          | 字段说明                                                                                                                                              | 类型    |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| RaceName    | 赛道名称；按 `strategy_type` 返回对应策略下的细分赛道，如股票多头的 `1000指增`、`500指增`，CTA 的 `期货高频`、`套利`，债券的 `中长期信用`、`转债增强` 等；实际可用值以 `pm_strategy_tracks` 返回的 `race_name` 为准 | str   |
| stock_bench | 股票资产暴露                                                                                                                                            | float |
| bond_bench  | 债券资产暴露                                                                                                                                            | float |
| coin_bench  | 货币/现金资产暴露                                                                                                                                         | float |


## 风格暴露序列(pm_risk_style_exposure_trend)

获取组合指定策略的风格暴露时间序列。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                          |
| ------------- | ------ | ---- | ---- | ------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                      |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                       |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |


**请求响应**


| 字段         | 字段说明   | 类型    |
| ---------- | ------ | ----- |
| TradingDay | 交易日    | date  |
| 大盘成长       | 大盘成长暴露 | float |
| 大盘价值       | 大盘价值暴露 | float |
| 中盘成长       | 中盘成长暴露 | float |
| 中盘价值       | 中盘价值暴露 | float |
| 小盘成长       | 小盘成长暴露 | float |
| 小盘价值       | 小盘价值暴露 | float |


## 风格暴露-按基金(pm_risk_style_exposure_by_fund)

获取子基金风格暴露截面、组合加权平均、比较基准和偏离。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                                    |
| ------------- | ------ | ---- | ---- | ----------------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                                |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                                 |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天           |
| bench_id      | 基准 ID  | int  | 否    | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |


**请求响应**


| 字段              | 字段说明                    | 类型    |
| --------------- | ----------------------- | ----- |
| fund_short_name | 子基金简称                   | str   |
| big_grow        | 大盘成长暴露                  | float |
| big_value       | 大盘价值暴露                  | float |
| mid_grow        | 中盘成长暴露                  | float |
| mid_value       | 中盘价值暴露                  | float |
| small_grow      | 小盘成长暴露                  | float |
| small_value     | 小盘价值暴露zm_api_pm_v2_risk | float |


## 风格暴露-按赛道(pm_risk_style_exposure_by_track)

获取按赛道聚合的风格暴露和基准偏离。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                                    |
| ------------- | ------ | ---- | ---- | ----------------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                                |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                                 |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天           |
| bench_id      | 基准 ID  | int  | 否    | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |


**请求响应**


| 字段          | 字段说明                                                                               | 类型    |
| ----------- | ---------------------------------------------------------------------------------- | ----- |
| RaceName    | 赛道名称；按 `strategy_type` 返回对应策略下的细分赛道，实际可用值以 `pm_strategy_tracks` 返回的 `race_name` 为准 | str   |
| big_grow    | 大盘成长暴露                                                                             | float |
| big_value   | 大盘价值暴露                                                                             | float |
| mid_grow    | 中盘成长暴露                                                                             | float |
| mid_value   | 中盘价值暴露                                                                             | float |
| small_grow  | 小盘成长暴露                                                                             | float |
| small_value | 小盘价值暴露                                                                             | float |


## 行业/久期暴露序列(pm_risk_industry_exposure_trend)

获取股票/中性策略行业暴露序列，或债券策略久期暴露序列。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                          |
| ------------- | ------ | ---- | ---- | ------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                      |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                       |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |


**请求响应**


| 字段         | 字段说明     | 类型    |
| ---------- | -------- | ----- |
| TradingDay | 交易日      | date  |
| 周期上游       | 周期上游暴露   | float |
| 周期中游       | 周期中游暴露   | float |
| 周期下游       | 周期下游暴露   | float |
| 金融行业       | 金融行业暴露   | float |
| 消费         | 消费行业暴露   | float |
| TMT        | TMT 行业暴露 | float |


## 行业/久期暴露-按基金(pm_risk_industry_exposure_by_fund)

获取子基金行业/久期暴露截面、组合加权平均、比较基准和偏离。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                                    |
| ------------- | ------ | ---- | ---- | ----------------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                                |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                                 |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天           |
| bench_id      | 基准 ID  | int  | 否    | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |


**请求响应**


| 字段                 | 字段说明     | 类型    |
| ------------------ | -------- | ----- |
| fund_short_name    | 子基金简称    | str   |
| period_up          | 周期上游暴露   | float |
| period_mid         | 周期中游暴露   | float |
| period_down        | 周期下游暴露   | float |
| financial_industry | 金融行业暴露   | float |
| consume            | 消费行业暴露   | float |
| tmt                | TMT 行业暴露 | float |


## 行业/久期暴露-按赛道(pm_risk_industry_exposure_by_track)

获取按赛道聚合的行业/久期暴露和基准偏离。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                                    |
| ------------- | ------ | ---- | ---- | ----------------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                                |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                                 |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天           |
| bench_id      | 基准 ID  | int  | 否    | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |


**请求响应**


| 字段                 | 字段说明                                                                                 | 类型    |
| ------------------ | ------------------------------------------------------------------------------------ | ----- |
| RaceName           | 赛道名称；股票多头/市场中性表示行业暴露对应赛道，债券表示久期暴露对应赛道；实际可用值以 `pm_strategy_tracks` 返回的 `race_name` 为准 | str   |
| period_up          | 周期上游暴露                                                                               | float |
| period_mid         | 周期中游暴露                                                                               | float |
| period_down        | 周期下游暴露                                                                               | float |
| financial_industry | 金融行业暴露                                                                               | float |
| consume            | 消费行业暴露                                                                               | float |
| tmt                | TMT 行业暴露                                                                             | float |


## 信用暴露序列(pm_risk_credit_exposure_trend)

获取债券策略信用暴露时间序列。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                          |
| ------------- | ------ | ---- | ---- | ------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                      |
| strategy_type | 策略类型   | int  | 是    | 通常为 `4` 债券                                  |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |


**请求响应**


| 字段         | 字段说明     | 类型    |
| ---------- | -------- | ----- |
| TradingDay | 交易日      | date  |
| 利率债        | 利率债暴露    | float |
| 高等级信用债     | 高等级信用债暴露 | float |
| 高收益信用债     | 高收益信用债暴露 | float |


## 信用暴露-按基金(pm_risk_credit_exposure_by_fund)

获取子基金信用暴露截面、组合加权平均、比较基准和偏离。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                                    |
| ------------- | ------ | ---- | ---- | ----------------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                                |
| strategy_type | 策略类型   | int  | 是    | 通常为 `4` 债券                                            |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天           |
| bench_id      | 基准 ID  | int  | 否    | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |


**请求响应**

返回子基金信用暴露 DataFrame。本次 `pm_id=10287`、债券策略样例返回空列 DataFrame；有数据时字段通常与 `pm_risk_credit_exposure_by_track` 类似，包含基金名称和 `rate_bond`、`high_credict_bond`、`high_return_bond` 等暴露列。

## 信用暴露-按赛道(pm_risk_credit_exposure_by_track)

获取按赛道聚合的信用暴露和基准偏离。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                                    |
| ------------- | ------ | ---- | ---- | ----------------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                                |
| strategy_type | 策略类型   | int  | 是    | 通常为 `4` 债券                                            |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天           |
| bench_id      | 基准 ID  | int  | 否    | 不传时优先自动调用 `pm_strategy_benchmark` 获取，再兜底全局 `bench_id` |


**请求响应**


| 字段                | 字段说明                                                                                     | 类型    |
| ----------------- | ---------------------------------------------------------------------------------------- | ----- |
| RaceName          | 债券赛道名称，如 `高收益信用`、`中长期信用`、`转债增强`、`可转债多头` 等；实际可用值以 `pm_strategy_tracks` 返回的 `race_name` 为准 | str   |
| rate_bond         | 利率债暴露                                                                                    | float |
| high_credict_bond | 高等级信用债暴露                                                                                 | float |
| high_return_bond  | 高收益信用债暴露                                                                                 | float |


## 风险因子暴露(pm_risk_factor_exposure)

获取子基金风险因子暴露。

**请求参数**


| 字段            | 字段说明   | 类型   | 是否必填 | 备注                                                       |
| ------------- | ------ | ---- | ---- | -------------------------------------------------------- |
| pm_id         | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                                   |
| strategy_type | 策略类型   | int  | 是    | 见通用说明                                                    |
| begin_date    | 开始日期   | date | 否    | 默认取 `pm_analysis_config` 的 `begin_date`，再兜底 `2020-01-01` |
| end_date      | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天              |


**请求响应**

返回字段按 `strategy_type` 不同而不同。通用字段：


| 字段              | 字段说明                                | 类型    |
| --------------- | ----------------------------------- | ----- |
| FundID          | 子基金 ID                              | int   |
| fund_short_name | 子基金简称；股票多头/市场中性/债券结果通常额外包含“加权平均”汇总行 | str   |
| Ratio           | 持仓比例；“加权平均”汇总行为空                    | float |


因子收益输入数据优先通过 `risk_factor_returns` 查询；底层也可通过 `index_price` / `get_index_price` 按 `bench_id_list` 查询。取 `Yield` 作为回归或滚动相关性使用的因子收益。完整 `benchID`、服务端 `BenchName` 和下方响应字段的一一映射见 `references/zm_index_ids.md` 的“风险因子收益数据”。

股票多头(`strategy_type=1`)和市场中性(`strategy_type=3`)风险因子字段：

股票多头使用 `23003-23022` 的股票 Barra 因子；市场中性在股票 Barra 因子基础上额外使用 `10660`、`10661` 两个基差因子。下表字段名与 `references/zm_index_ids.md` 中 `pm_risk_factor_exposure响应字段` 对应。


| 字段                 | 字段说明              | 类型    |
| ------------------ | ----------------- | ----- |
| growth             | 成长因子暴露            | float |
| valuation          | 估值因子暴露            | float |
| profit             | 盈利因子暴露            | float |
| size               | 规模因子暴露            | float |
| volatility         | 流动因子暴露（后端当前字段名如此） | float |
| liquidity          | 波动因子暴露（后端当前字段名如此） | float |
| momentum           | 动量因子暴露            | float |
| leverage           | 杠杆因子暴露            | float |
| beta               | Beta 因子暴露         | float |
| non_linear         | 非线性因子暴露           | float |
| dividend           | 股息因子暴露            | float |
| short_reversal     | 短期反转因子暴露          | float |
| seasonality        | 季节性因子暴露           | float |
| long_reversal      | 长期反转因子暴露          | float |
| profit_volatility  | 盈利波动因子暴露          | float |
| profit_quality     | 盈利质量因子暴露          | float |
| investment_quality | 投资质量因子暴露          | float |
| pb                 | PB 因子暴露           | float |
| analyst_forecast   | 分析师预期因子暴露         | float |
| industry_momentum  | 行业动量因子暴露          | float |
| if_basis           | IF 基差因子暴露；市场中性返回  | float |
| ic_basis           | IC 基差因子暴露；市场中性返回  | float |


债券(`strategy_type=4`)风险因子字段：

债券因子使用 `22409-22414`、`22390`、`22325-22339`、`22559-22564` 等因子收益序列。下表字段名与 `references/zm_index_ids.md` 中 `pm_risk_factor_exposure响应字段` 对应。


| 字段                 | 字段说明          | 类型    |
| ------------------ | ------------- | ----- |
| finance_aaa        | 金融债 AAA 暴露    | float |
| cib_aaa            | 城投债 AAA 暴露    | float |
| soe_aaa            | 国企债 AAA 暴露    | float |
| poe_aaa            | 民企债 AAA 暴露    | float |
| estate_aaa         | 地产债 AAA 暴露    | float |
| finance_aap        | 金融债 AA+ 暴露    | float |
| cib_aap            | 城投债 AA+ 暴露    | float |
| soe_aap            | 国企债 AA+ 暴露    | float |
| poe_aap            | 民企债 AA+ 暴露    | float |
| estate_aap         | 地产债 AA+ 暴露    | float |
| finance_aa         | 金融债 AA 及以下暴露  | float |
| cib_aa             | 城投债 AA 及以下暴露  | float |
| soe_aa             | 国企债 AA 及以下暴露  | float |
| poe_aa             | 民企债 AA 及以下暴露  | float |
| estate_aa          | 地产债 AA 及以下暴露  | float |
| rate               | 利率债暴露         | float |
| equity_fac         | 股性因子暴露        | float |
| debt_fac           | 债性因子暴露        | float |
| neutral_conv       | 中性转债因子暴露      | float |
| large_cap          | 大盘因子暴露        | float |
| small_cap          | 小盘因子暴露        | float |
| other_size         | 其他规模因子暴露      | float |
| ce_bond_size       | 央企债规模加权因子暴露   | float |
| ind_bond_size      | 其他产业债规模加权因子暴露 | float |
| callable_bond_size | 含权债规模加权因子暴露   | float |
| sub_bond_size      | 次级债规模加权因子暴露   | float |
| private_bond_size  | 私募债规模加权因子暴露   | float |
| other_credit_size  | 其他信用债规模加权因子暴露 | float |


CTA(`strategy_type=5`)风险因子字段。CTA 使用滚动相关性口径，字段名为服务端 `BenchName` 去除首尾空格后的因子/指数中文名；完整 `benchID` 对照见 `references/zm_index_ids.md` 的“CTA策略因子收益(strategy_type=5)”：


| 字段             | 字段说明                 | 类型    |
| -------------- | -------------------- | ----- |
| 国君期货商品长期动量策略   | 长期动量因子相关性            | float |
| 国君期货商品波动策略     | 波动因子相关性              | float |
| 国君期货商品反转策略     | 反转因子相关性              | float |
| 国君期货商品偏度策略     | 偏度因子相关性              | float |
| 国君期货商品中期动量策略   | 中期动量因子相关性            | float |
| 国君期货商品量价相关性策略  | 量价相关性因子相关性           | float |
| 国君期货商品长期规则动量策略 | 长期规则动量因子相关性          | float |
| 国君期货商品长期截面动量策略 | 长期截面动量因子相关性          | float |
| 国君期货商品期限基差策略   | 期限基差因子相关性            | float |
| 国君期货商品仓单策略     | 仓单因子相关性              | float |
| 国君期货商品库存策略     | 库存因子相关性              | float |
| 国君期货商品基差策略     | 基差因子相关性              | float |
| 国君期货商品利润策略     | 利润因子相关性              | float |
| 国君期货商品基差动量策略   | 基差动量因子相关性            | float |
| 南华黑色指数         | 黑色商品指数相关性            | float |
| 南华有色金属指数       | 有色金属指数相关性            | float |
| 南华贵金属指数        | 贵金属指数相关性             | float |
| 南华农产品指数        | 农产品指数相关性             | float |
| 南华能化指数         | 能化指数相关性              | float |
| CFFEX10年期国债期货  | 10 年期国债期货相关性         | float |
| IC持仓主连合约       | IC 主连合约相关性           | float |
| 独特性1           | 国泰君安 CTA 因子组相关性平方和开方 | float |
| 独特性2           | CTA 大类因子组相关性平方和开方    | float |


## 投顾因子敏感性(pm_adviser_factor_sensitivity)

获取投顾/公司横截面的市场敏感性指标。服务端实际使用 `pm_id`、`end_date`，不接收 `strategy_type`。

**请求参数**


| 字段       | 字段说明   | 类型   | 是否必填 | 备注                                          |
| -------- | ------ | ---- | ---- | ------------------------------------------- |
| pm_id    | 母基金 ID | int  | 是    | 从 `pm_info_list` 结果中选取                      |
| end_date | 结束日期   | date | 否    | 默认取 `pm_analysis_config` 的 `end_date`，再兜底今天 |


**请求响应**


| 字段                | 字段说明              | 类型    |
| ----------------- | ----------------- | ----- |
| invest_short_name | 投顾/公司简称           | str   |
| large_small       | 大小盘敏感性            | float |
| cap               | 仓位/超低配敏感性         | float |
| grwoth_value      | 成长价值敏感性（后端字段拼写如此） | float |
| basis             | 基差敏感性             | float |
