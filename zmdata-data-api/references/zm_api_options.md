
# ZM期权数据接口

## 期权合约列表(option_contract_list)

期权合约列表数据，包括期权合约交易代码、期权名称、期权类型、期权行权价格、期权到期日期、期权行权日期

**请求参数**

无

**请求响应**

| 字段           | 字段说明         | 类型   |
|----------------|-----------------|--------|
| option_symbol  | 期权合约交易代码 | str    |
| option_name    | 期权名称         | str    |
| option_type    | 期权类型         | str    |
| strike_price   | 行权价格         | float  |
| expire_date    | 到期日期         | date   |
| exercise_date  | 行权日期         | date   |


## 期权行情(option_daily_market_data)

期权合约日行情数据，包括交易日期、开盘价、最高价、最低价、收盘价、成交量

**请求参数**

| 字段          | 字段说明         | 类型   | 是否必填 | 备注                            |
|---------------|-----------------|--------|----------|---------------------------------|
| option_symbol | 期权合约交易代码 | str    | 是       | 例如：'IO2002-P-3850'           |
| start_date    | 开始日期         | date   | 否       | 格式为YYYY-MM-DD，默认为期权成立日期 |
| end_date      | 结束日期         | date   | 否       | 格式为YYYY-MM-DD，默认为当前日期     |

**请求响应**

| 字段          | 字段说明         | 类型   |
|---------------|-----------------|--------|
| option_symbol | 期权合约交易代码 | str    |
| trading_day   | 交易日期         | date   |
| open_price    | 开盘价           | float  |
| high_price    | 最高价           | float  |
| low_price     | 最低价           | float  |
| close_price   | 收盘价           | float  |
| volume        | 成交量           | float  |
| turnover      | 成交额           | float  |
