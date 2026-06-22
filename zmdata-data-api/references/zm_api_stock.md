
# ZM股票数据接口

## 上市股票列表(stock_list)

**请求参数**

无

**请求响应**

| 字段          | 字段说明     | 类型      | 说明                                                                 |
|---------------|--------------|-----------|----------------------------------------------------------------------|
| CompanyCode   | 公司代码     | int       |                                                                      |
| CompanyName   | 公司名称     | str       |                                                                      |
| InnerCode     | 聚源代码     | int       |                                                                      |
| ListedDate    | 上市日期     | datetime  |                                                                      |
| ListedSector  | 上市板块     | int       | 1-主板，2-中小企业板，3-三板，4-其他，5-大宗交易系统，6-创业板，7-科创板，8-北交所股票 |
| ListedState   | 上市状态     | int       | 1-上市，3-暂停，5-终止，9-其他                                        |
| SecuMarket    | 证券市场     | int       | 18-北交所，83-上交所，90-深交所                                       |
| StockCode     | 股票代码     | str       |                                                                      |
| StockName     | 股票名称     | str       |                                                                      |
| SecuCategory  | 证券类别     | str       | A股 / 开放式基金                                                     |


## 股票 daily 行情(stock_daily_quote)

**请求参数**

| 字段             | 字段说明         | 类型   | 是否必填 | 备注                         |
|------------------|------------------|--------|----------|------------------------------|
| stock_code_list  | 股票代码列表     | list   | 否       | 默认取股票主表的全部股票, stock_code 是6位数字编码, 比如贵州茅台 "600519" |
| start_date       | 开始日期         | date   | 否       |                              |
| end_date         | 结束日期         | date   | 否       |                              |

**请求响应**

| 字段                  | 字段说明                     | 类型   |
|-----------------------|------------------------------|--------|
| StockCode             | 股票代码                     | str    |
| StockName             | 股票名称                     | str    |
| TradingDay            | 交易日期                     | date   |
| SecuCategory          | 证券类别(A股/开放式基金)   | str    |
| OpenClose             | 开盘价                       | float  |
| HighPrice             | 最高价                       | float  |
| LowPrice              | 最低价                       | float  |
| ClosePrice            | 收盘价                       | float  |
| AdjustedClosePrice    | 前复权收盘价                 | float  |
| AdjustedCloseFactor   | 复权因子                     | float  |
| TurnoverDeals         | 成交笔数(笔)               | float  |
| TurnoverValue         | 成交额(元)                 | float  |
| TurnoverVolume        | 成交量(股)                 | float  |
| TotalMV               | 总市值                       | float  |
| NegotiableMV          | 流通市值(A/B股流通市值)    | float  |


## 股票行业(stock_industry)

**请求参数**

| 字段            | 字段说明         | 类型   | 是否必填 | 备注                         |
|-----------------|------------------|--------|----------|------------------------------|
| stock_code_list | 股票代码列表     | list   | 否       | 默认取股票主表的全部股票     |
| start_date      | 开始日期         | date   | 否       |                              |
| end_date        | 结束日期         | date   | 否       |                              |
| closing_date    | 截止日期         | date   | 否       |                              |
| standard        | 行业分类标准     | int    | 否       | 默认 38, 38-申万行业分类(新)（该版本融合申万2021、2014、2011版分类标准，兼容历史股票），41-申万行业分类2021版，43-中信行业2019分类           |

**请求响应**

| 字段                | 字段说明             | 类型   |
|---------------------|----------------------|--------|
| StockCode           | 股票代码             | str    |
| StockName           | 股票名称             | str    |
| FirstIndustryName   | 一级行业             | str    |
| SecondIndustryName  | 二级行业             | str    |
| ThirdIndustryName   | 三级行业             | str    |
| InfoPublicdate      | 发布日期             | date   |
| Companycode         | 公司代码             | str    |
| Standard            | 行业分类标准         | int    |
| CancelDate          | 取消日期             | date   |
| InsertTime          | 发布时间             | date   |


## 股票估值(stock_valuation)

**请求参数**

| 字段            | 字段说明         | 类型   | 是否必填 | 备注 |
|-----------------|------------------|--------|----------|------|
| stock_code_list | 股票代码列表     | list   | 否       |      |

**请求响应**

| 字段        | 字段说明                   | 类型   |
|-------------|---------------------------|--------|
| stock_code  | 股票代码                   | str    |
| stock_name  | 股票名称                   | str    |
| trading_day | 交易日期                   | date   |
| total_mv    | 总市值                     | float  |
| pe_ttm      | 市盈率(TTM)                | float  |
| pb_lf       | 市净率(LF)                 | float  |
| ps_ttm      | 市销率(TTM)                | float  |


## 行业列表(industry_list)

**请求参数**

无

**请求响应**

| 字段                 | 字段说明       | 类型   | 说明      |
|----------------------|---------------|--------|-----------|
| industry_name        | 行业名称       | str    |           |
| classification       | 行业等级       | int    | 1, 2, 3   |
| first_industry_name  | 一级行业名称   | str    |           |
| second_industry_name | 二级行业名称   | str    |           |
| third_industry_name  | 三级行业名称   | str    |           |
| standard_name        | 行业标准名称   | str    |           |


## 行业估值(industry_valuation)

**请求参数**

| 字段               | 字段说明         | 类型   | 是否必填 | 备注 |
|--------------------|------------------|--------|----------|------|
| industry_name_list | 行业名称列表     | list   | 否       |      |

**请求响应**

| 字段          | 字段说明                   | 类型   |
|---------------|---------------------------|--------|
| industry_name | 行业名称                   | str    |
| trading_day   | 交易日期                   | date   |
| total_mv      | 总市值                     | float  |
| pe_ttm        | 市盈率(TTM)                | float  |
| pb_lf         | 市净率(LF)                 | float  |
| ps_ttm        | 市销率(TTM)                | float  |
| standard_name | 行业标准名称               | str    |


## 交易日历(trading_calendar)

A股交易日历

**请求参数**

无

**请求响应**

| 字段         | 字段说明 | 类型   |
|--------------|----------|--------|
| trading_date | 交易日期 | date   |
