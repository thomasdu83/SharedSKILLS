
# python安装说明与接口列表

## 如何下载安装

**安装**
pip install -i http://10.168.30.14:8081/repository/flare-custom/simple --trusted-host 10.168.30.14 zmdata

**当前版本**
20260522 发布版本 1.4.1

**版本检查**

```python
import zmdata
print(zmdata.__version__)
```

## 接口汇总

投后(组合)相关接口必须设置 `PM_API_KEY` 后再调用：

```python
import zmdata as api

api.PM_API_KEY = '<your-api-key>'
```

| 接口分类 | 接口名称 | 接口说明 |
|---------|---------|---------|
| 股票 | stock_list | 上市股票列表 |
| 股票 | stock_daily_quote | 股票 daily 行情 |
| 股票 | stock_industry | 股票行业 |
| 股票 | stock_valuation | 股票估值 |
| 股票 | industry_list | 行业列表 |
| 股票 | industry_valuation | 行业估值 |
| 股票 | trading_calendar | 交易日历 |
| 基金 | open_fund_list | 公募基金列表 |
| 基金 | get_fund_in_label | 基金池 |
| 基金 | fund_nav | 基金净值 |
| 基金 | fund_scale | 基金规模 |
| 基金 | fund_stock_info_hreport | 基金持仓明细-半年报 |
| 基金 | fund_top_holdings_qreport | 基金前十大持仓-季报 |
| 投后 | pm_info_list | 产品/母基金列表 |
| 投后 | pm_nav | 母基金净值/业绩走势 |
| 投后 | pm_asset_allocation | 资产配置 |
| 投后 | pm_strategy_nav | 分策略净值 |
| 投后 | pm_track_allocation | 赛道配置 |
| 投后 | pm_track_revenue | 赛道累计盈亏 |
| 投后 | pm_subfunds | 子基金列表 |
| 投后 | pm_subfund_nav | 子基金净值 |
| 债券 | cb_list | 可转债列表 |
| 债券 | cb_daily_market_data | 可转债行情 |
| ETF | etf_daily_market_data | ETF行情 |
| 期权 | option_contract_list | 期权合约列表 |
| 期权 | option_daily_market_data | 期权行情 |
| 期货 | future_product_list | 期货产品列表 |
| 期货 | future_daily_market_data | 期货行情 |
| 指数 | index_price | 指数价格 |
| 指数 | risk_factor_returns | 风险因子收益序列；用于 `pm_risk_factor_exposure` 回归/滚动相关性输入 |
| 指数 | index_component | 指数成分 |
