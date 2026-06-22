
# ZM基金数据接口

## 基金搜索(fund_search_quick)

封装投研平台 `searchQuick`，用于按关键词搜索基金。该接口不需要 token 或 `PM_API_KEY`。

**请求参数**

| 字段      | 字段说明                         | 类型 | 是否必填 | 备注 |
|-----------|----------------------------------|------|----------|------|
| keyword   | 搜索关键词                       | str  | 是       |      |
| pageIndex | 页码                             | int  | 否       | 默认 1 |
| pageSize  | 每页条数                         | int  | 否       | 默认 10 |
| typeName  | 搜索范围                         | str  | 否       | 默认 `投后子基金,尽调,至明库` |

**请求响应**

返回搜索结果 DataFrame。分页元信息保存在 `df.attrs`：

| attrs 字段 | 字段说明 |
|------------|----------|
| totalCount | 总记录数 |
| totalPage  | 总页数   |
| counter    | 计数器信息 |

常见响应字段包括：

| 字段                    | 字段说明       | 类型 |
|-------------------------|----------------|------|
| fundID                  | 基金 ID        | str  |
| fundCode                | 基金代码       | str  |
| fundName                | 基金名称       | str  |
| fundManageCompany       | 管理人名称     | str  |
| fundManager             | 基金经理       | str  |
| typeName                | 数据来源类型   | str  |
| sourceID                | 来源 ID        | int  |
| sourceName              | 来源名称       | str  |
| strategyType            | 策略类型       | str  |
| fundType                | 基金类型       | str  |
| analysisStatus          | 样本状态       | str  |
| minNVDate               | 最早净值日期   | date |
| maxNVDate               | 最新净值日期   | date |
| frequency               | 净值频率       | int  |
| frequencyList           | 可用净值频率   | list |
| labelIDs                | 标签 ID 列表   | list |
| benchID                 | 基准 ID        | int  |
| benchName               | 基准名称       | str  |
| rankConfigID            | 评分配置 ID    | int  |

**示例**

```python
import zmdata as api

df = api.fund_search_quick("数法1000")
print(df[["fundID", "fundCode", "fundName", "typeName"]].head())
print(df.attrs["totalCount"], df.attrs["totalPage"])
```

## 公募基金列表(open_fund_list)

**请求参数**

无

**请求响应**

| 字段              | 字段说明                           | 类型   |
|-------------------|-----------------------------------|--------|
| FundID            | 至明编码                           | int    |
| FundCode          | 市场编码                           | int    |
| FundSysCode       | 至明入库基金编码                   | int    |
| DataSourceCode    | 来源ID（FundlnitCode）             | int    |
| SourceName        | 公募/私募                          | str    |
| FundRegDate       | 注册日期                           | date   |
| FundName          | 基金名称                           | str    |
| Manager           | 当前（请求时间）经理名称，多个逗号分隔 | str    |
| fundmanagecompany | 投顾名称                           | str    |
| EndDate           | 当前时间                           | str    |


## 基金池(get_fund_in_label)

**请求参数**

| 字段           | 字段说明       | 类型   | 是否必填 | 备注         |
|----------------|---------------|--------|----------|--------------|
| label_id_list  | 标签id列表     | list   | 否       |              |
| end_date       | 结束日期       | date   | 否       | 默认是今天   |

**请求响应**

| 字段      | 字段说明   | 类型   |
|-----------|-----------|--------|
| FundID    | 基金ID     | int    |
| FundCode  | 基金编码   | str    |
| FundName  | 基金名称   | str    |
| LabelDay  | 标签日期   | date   |
| LabelID   | 标签ID     | int    |
| LabelName | 标签名称   | str    |


## 基金净值(fund_nav)

**请求参数**

| 字段         | 字段说明                     | 类型   | 是否必填 | 备注               |
|--------------|----------------------------|--------|----------|--------------------|
| fund_id_list | 基金id列表                  | list   | 否       |                    |
| start_date   | 开始日期                    | date   | 否       | 默认最早日期       |
| end_date     | 结束日期                    | date   | 否       | 默认当前日期       |
| is_origin    | 是否返回来源净值            | int    | 否       | 默认1              |
| frequency    | 频率(映射见常量表-统计周期) | int    | 否       | 默认2              |

**请求响应**

| 字段         | 字段说明       | 类型     |
|--------------|---------------|----------|
| FundID       | 基金ID        | int      |
| FundCode     | 基金编码      | str      |
| FundName     | 基金名称      | str      |
| TradingDay   | 交易日        | datetime |
| UnitNav      | 单位净值      | float    |
| AccuNAV      | 累计净值      | float    |
| AdjustedNav  | 复权累计净值  | float    |
| Yield        | 收益          | float    |


## 基金规模(fund_scale)

**请求参数**

| 字段         | 字段说明     | 类型   | 是否必填 | 备注 |
|--------------|-------------|--------|----------|------|
| fund_id_list | 基金id列表   | list   | 否       |      |

**请求响应**

| 字段                 | 字段说明                       | 类型   |
|----------------------|-------------------------------|--------|
| TradingDay           | 交易日                         | date   |
| FundID               | 基金ID                         | int    |
| FundCode             | 基金编码                       | str    |
| NetAssetsValue       | 净资产值                       | float  |
| TotalNetAssetsValue  | 汇总净资产值，包括A类和C类     | float  |
| TotalShare           | 汇总份额，包括A类和C类         | float  |
| InfoPublDate         | 发布日期                       | date   |
| EndDate              | 结束日期                       | date   |
| FundName             | 基金名称                       | str    |


## 基金持仓明细-半年报(fund_stock_info_hreport)

**请求参数**

| 字段         | 字段说明     | 类型   | 是否必填 | 备注 |
|--------------|-------------|--------|----------|------|
| fund_id_list | 基金id列表   | list   | 否       |      |

**请求响应**

| 字段                | 字段说明       | 类型   |
|---------------------|---------------|--------|
| FundID              | 基金ID        | int    |
| FundCode            | 基金编码      | str    |
| FundName            | 基金名称      | str    |
| StockCode           | 股票代码      | str    |
| StockInnerCode      | 股票内部代码  | int    |
| StockName           | 股票名称      | str    |
| RatioInNV           | 权重          | float  |
| ReportDate          | 报告日期      | date   |
| InfoPublDate        | 发布日期      | date   |
| FirstIndustryName   | 一级行业名称  | str    |
| SecondIndustryName  | 二级行业名称  | str    |
| ThirdIndustryName   | 三级行业名称  | str    |
| Standard            | 行业分类标准  | int    |


## 基金前十大持仓-季报(fund_top_holdings_qreport)

**请求参数**

| 字段         | 字段说明     | 类型   | 是否必填 | 备注 |
|--------------|-------------|--------|----------|------|
| fund_id_list | 基金id列表   | list   | 否       |      |

**请求响应**

| 字段            | 字段说明   | 类型   |
|-----------------|-----------|--------|
| report_date     | 报告日期   | date   |
| serial_number   | 序号       | int    |
| stock_code      | 股票代码   | str    |
| stock_name      | 股票名称   | str    |
| ratio_in_nv     | 权重       | float  |
| info_publ_date  | 发布日期   | date   |
| FundID          | 基金ID     | int    |
| FundCode        | 基金编码   | str    |
| FundName        | 基金名称   | str    |


## 基金评分(get_fund_score)

非评分的基金池、标签列表或 `label_id` 映射查询，优先参考 `docs/data_api/zm_fund_group_ids.md`；评分样本组和 `rankconfigid` 查询，参考 `docs/data_api/rankconfig_id.md`。

**请求参数**

| 字段         | 字段说明       | 类型   | 是否必填 | 备注                                                      |
|--------------|---------------|--------|----------|-----------------------------------------------------------|
| fund_id_list | 基金id列表     | list   | 是       |                                                           |
| rankconfigid | 评分样本组ID   | int    | 是       | 定义见 `docs/data_api/rankconfig_id.md`                  |
| start_date   | 开始日期       | date   | 否       | 默认最早可用日, 时序明细的开始期, is_day=1时有效                                          |
| end_date     | 结束日期       | date   | 否       | 默认当前期, 时序明细的结束期, is_day=1时有效                                              |
| is_day       | 是否返回日频   | int    | 否       | 默认0；0表示截面评分，1表示时序明细                      |
| is_norm      | 是否归一化     | int    | 否       | 默认0；0表示原始评分，1表示归一化评分                    |

**请求响应**

返回基金评分结果（DataFrame）。响应字段会随 `rankconfigid` 与参数配置变化，通常包含基金标识、日期以及对应评分值。
字段中文说明见 `docs/data_api/zm_fund_score_fields.md`（按 `score_type` 分类）。

### 典型调用流程（产品评分）
当用户查询“市场跟踪池/私募跟踪池 CTA 类型产品评分”时，建议按以下顺序调用：

1. 在 `docs/data_api/rankconfig_id.md` 中定位 `rank_config_name = 市场跟踪池` 下的 `CTA` 子节点，确定目标 `rankconfigid` 和  `label_id`。
2. 使用 `get_fund_in_label(label_id_list=[label_id])` 获取对应标签下的基金列表。
3. 调用 `get_fund_score(fund_id_list=..., rankconfigid=..., is_day=0, is_norm=1)` 获取评分结果。
