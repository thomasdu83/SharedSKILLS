
# ZM ETF数据接口

## ETF行情(etf_daily_market_data)

ETF日行情数据，包括交易日期、开盘价、最高价、最低价、收盘价、成交量

**请求参数**

| 字段       | 字段说明 | 类型   | 是否必填 | 备注                             |
|------------|---------|--------|----------|----------------------------------|
| etf_code   | ETF编码 | str    | 是       | 例如：'510300', '510050'         |
| start_date | 开始日期 | date   | 否       | 格式为YYYY-MM-DD，默认为基金上市日期 |
| end_date   | 结束日期 | date   | 否       | 格式为YYYY-MM-DD，默认为当前日期     |

**请求响应**

| 字段        | 字段说明 | 类型   |
|-------------|---------|--------|
| etf_code    | ETF编码 | str    |
| trading_day | 交易日期 | date   |
| open_price  | 开盘价   | float  |
| high_price  | 最高价   | float  |
| low_price   | 最低价   | float  |
| close_price | 收盘价   | float  |
| volume      | 成交量   | float  |
| turnover    | 成交额   | float  |
