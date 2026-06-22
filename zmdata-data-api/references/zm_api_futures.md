
# ZM期货数据接口

## 期货产品列表(future_product_list)

**请求参数**

无

**请求响应**

| 字段            | 字段说明       | 类型   |
|-----------------|---------------|--------|
| product_code    | 期货品种代码   | str    |
| product_name    | 期货品种名称   | str    |


## 期货行情(future_daily_market_data)

期货日行情数据，包括交易日期、开盘价、最高价、最低价、收盘价、成交量

**请求参数**

| 字段           | 字段说明                | 类型   | 是否必填 | 备注                                |
|----------------|------------------------|--------|----------|-------------------------------------|
| future_symbol  | 期货编码(品种代码+合约日期) | str    | 是       | 例如：'cu2512', 'AP505', 'IF2512'   |
| start_date     | 开始日期                | date   | 否       | 格式为YYYY-MM-DD，默认为期货成立日期 |
| end_date       | 结束日期                | date   | 否       | 格式为YYYY-MM-DD，默认为当前日期     |

**请求响应**

| 字段         | 字段说明   | 类型   |
|--------------|-----------|--------|
| future_symbol| 期货编码   | str    |
| trading_day  | 交易日期   | date   |
| open_price   | 开盘价     | float  |
| high_price   | 最高价     | float  |
| low_price    | 最低价     | float  |
| close_price  | 收盘价     | float  |
| volume       | 成交量     | float  |
| turnover     | 成交额     | float  |
