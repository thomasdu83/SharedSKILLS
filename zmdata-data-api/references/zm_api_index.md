
# ZM指数数据接口

## 指数价格(index_price)

获取各类指数、基准、策略标尺和因子的历史行情数据。服务端底层的 `BenchmarkClosePrice` / `BenchmarkYield` 混合保存指数、基准和因子等多类序列，因此查询股票 Barra 因子收益、CTA 策略因子收益等 `pm_risk_factor_exposure` 回归/相关性计算输入数据时，也使用该接口。
bench_id_list 和 index_code_list 至少提供一个

**请求参数**

| 字段             | 字段说明                 | 类型   | 是否必填 | 备注                                             |
|------------------|-------------------------|--------|----------|--------------------------------------------------|
| bench_id_list    | 至明内部指数ID(基准ID)   | list   | 否       | bench_id_list 和 index_code_list 至少提供一个    |
| index_code_list  | 指数标准编码             | list   | 否       |                                                  |
| frequency        | 频率                     | int    | 否       | 默认为1                                          |
| start_date       | 开始日期                 | date   | 否       | 默认1991-01-01                                   |
| end_date         | 结束日期                 | date   | 否       | 默认今天                                         |

**请求响应**

| 字段        | 字段说明                  | 类型   |
|-------------|---------------------------|--------|
| BenchID     | 至明内部指数ID(基准ID)    | int    |
| BenchCode   | 指数标准编码              | str    |
| BenchName   | 指数名称(基准名称)        | str    |
| Frequency   | 频率                      | int    |
| TradingDay  | 交易日期                  | date   |
| OpenPrice   | 开盘价                    | float  |
| HighPrice   | 最高价                    | float  |
| LowPrice    | 最低价                    | float  |
| ClosePrice  | 收盘价                    | float  |
| Yield       | 日收益率(涨跌幅)          | float  |
| Volume      | 成交量(股/份)             | float  |
| Turnover    | 成交金额                  | float  |

**风险因子收益用法**

- 客户端已封装 `risk_factor_returns`，用于查询 `pm_risk_factor_exposure` 计算口径对应的因子收益序列；底层仍调用 `index_price`。
- `Yield` 是因子日收益率，可作为 `pm_risk_factor_exposure` 计算子基金因子暴露时使用的因子收益输入。
- `ClosePrice` 是对应因子/指数净值或收盘价序列。
- 股票 Barra 因子、市场中性基差因子、债券因子、CTA 策略因子的完整 `benchID` 和响应字段映射见 `references/zm_index_ids.md` 的“风险因子收益数据”。
- 封装查询示例：`risk_factor_returns(strategy_type=1, start_date="2024-01-01", end_date="2024-12-31")`。
- 通用接口查询示例：`get_index_price(bench_id_list=[23003, 23004], start_date="2024-01-01", end_date="2024-12-31")`。

## 风险因子收益(risk_factor_returns)

获取 `pm_risk_factor_exposure` 计算口径对应的风险因子收益序列。该接口是 `index_price` 的语义封装，自动按策略类型或因子集合映射到对应 `benchID`，返回字段与 `index_price` 一致；使用 `Yield` 作为因子收益。

**请求参数**

| 字段 | 字段说明 | 类型 | 是否必填 | 备注 |
|------|----------|------|----------|------|
| strategy_type | 策略类型 | int | 否 | `1` 股票 Barra，`3` 市场中性，`4` 债券，`5` CTA；`strategy_type`、`factor_set`、`bench_id_list` 至少提供一个 |
| factor_set | 因子集合别名 | str | 否 | 可用 `stock_barra`、`barra`、`market_neutral`、`bond`、`cta`、`cta_strategy` |
| bench_id_list | 明确指定因子/指数 ID | list | 否 | 传入后优先使用该列表，不再按 `strategy_type` 或 `factor_set` 自动映射 |
| start_date | 开始日期 | date | 否 | 传给底层 `index_price` |
| end_date | 结束日期 | date | 否 | 传给底层 `index_price` |
| closing_date | 截止日期 | date | 否 | 传给底层 `index_price` |
| frequency | 频率 | int | 否 | 默认 `1` |
| columns | 返回列 | list | 否 | 传给底层 `index_price` |

**请求响应**

同 `index_price`。常用字段包括 `BenchID`、`BenchName`、`TradingDay`、`ClosePrice`、`Yield`；其中 `Yield` 是回归或滚动相关性计算使用的因子收益。

**调用示例**

```python
import zmdata as api

# 股票 Barra 因子收益
df = api.risk_factor_returns(strategy_type=1, start_date="2024-01-01", end_date="2024-12-31")

# CTA 策略因子收益
df = api.risk_factor_returns(factor_set="cta", start_date="2024-01-01", end_date="2024-12-31")
```


## 指数成分(index_component)

获取指数的当前成分股列表

**请求参数**

| 字段             | 字段说明         | 类型   | 是否必填 | 备注 |
|------------------|------------------|--------|----------|------|
| index_code_list  | 指数标准编码列表 | list   | 否       |      |

**请求响应**

| 字段                | 字段说明           | 类型   |
|---------------------|-------------------|--------|
| IndexCode           | 指数标准编码       | str    |
| StockCode           | 股票代码           | str    |
| StockName           | 股票名称           | str    |
| RatioInNV           | 权重               | float  |
| FirstIndustryName   | 一级行业名称       | str    |
| SecondIndustryName  | 二级行业名称       | str    |
| ThirdIndustryName   | 三级行业名称       | str    |
| Standard            | 行业分类标准       | int    |
| StandardName        | 行业分类标准名称   | str    |
| TradingDay          | 交易日期           | date   |
