# ZM投后数据接口

投后(组合)相关接口走 `zm_pm_svr`，调用前必须设置 `PM_API_KEY`。

```python
import zmdata as api

api.PM_API_KEY = '<your-api-key>'
```

也可以通过环境变量 `ZM_PM_API_KEY` 配置。PM V2 接口文档已按 `APIClientResearch/zmdata/apis/pm_v2/` 的代码组织拆分。

## 通用说明

日期和默认值处理：

- 显式传入的参数优先。
- 除 `pm_info_list`、`pm_strategy_benchmark`、`pm_subfund_nav` 等不依赖组合全局参数的接口外，SDK 会先调用 `pm_analysis_config`（服务端 `/api/zmpmapi/fof/get_global_params`，`type=1`），读取 `para_case_content` 作为 PMInfo 页面同口径默认值。
- 常用全局字段包括：`begin_date`、`end_date`、`all_begin_date`、`all_end_date`、`last_begin_date`、`last_end_date`、`compare_begin_date`、`compare_end_date`、`compare_last_begin_date`、`compare_last_end_date`、`all_compare_begin_date`、`all_compare_end_date`、`bench_id`。
- 若全局参数为空，再使用本地兜底：开始日期 `2020-01-01`、结束日期今天、频率 `W`。`base_date` 不再硬编码为 `2020-01-01`，未传时交由服务端决定归一化基期。
- 股票多头等需要比较基准的接口，未显式传 `bench_id` 时会优先调用 `pm_strategy_benchmark` 获取策略默认基准，再兜底使用全局参数里的 `bench_id`。

策略类型 `strategy_type`：

| 值 | 含义 |
|----|------|
| 1 | 股票多头 |
| 3 | 市场中性 |
| 4 | 债券 |
| 5 | CTA |
| 9 | ETF |

返回字段来自 2026-05-15 运行 `/Users/lee/git/APIClientResearch/zm_tests/test_portfolio_v2_integration.py` 和同一批用例的字段探测，样例参数主要使用 `pm_id=10287`、`begin_date=2026-03-01`、`end_date=2026-04-23`。部分接口返回宽表，策略名、赛道名、基金名、基准名会随组合和参数变化。

## 分文件索引

| 文件 | 覆盖范围 |
|------|----------|
| `references/zm_api_pm_v2_support.md` | 产品/母基金列表、PMInfo 全局参数、组合基本信息、策略赛道列表、策略比较基准 |
| `references/zm_api_pm_v2_performance.md` | 组合净值曲线、净值明细、绩效统计、子基金列表、子基金净值 |
| `references/zm_api_pm_v2_allocation.md` | 资产配置、分策略净值/绩效/盈亏、Brinson、策略相关性、赛道配置/贡献、兼容 alias |
| `references/zm_api_pm_v2_risk.md` | 大类/风格/行业/信用暴露、风险因子暴露、投顾因子敏感性 |
| `references/zm_api_pm_v2_holding.md` | 持仓子基金净值/绩效/统计/收益分解/相关性、投顾相关性、持仓暴露 alias |

## 接口清单

### Support

- `pm_info_list`
- `pm_analysis_config`
- `pm_base_info`
- `pm_strategy_tracks`
- `pm_strategy_benchmark`

### Performance

- `pm_performance_trend`
- `pm_nav`
- `pm_performance_stats`
- `pm_subfunds`
- `pm_subfund_nav`

### Allocation

- `pm_asset_allocation`
- `pm_strategy_nav`
- `pm_strategy_period_performance`
- `pm_strategy_full_period_performance`
- `pm_strategy_cumulative_pnl`
- `pm_strategy_cumulative_return`
- `pm_strategy_pnl_by_period`
- `pm_brinson_attribution`
- `pm_strategy_correlation`
- `pm_strategy_benchmark_comparison`
- `pm_strategy_performance_list`
- `pm_strategy_track_allocation`
- `pm_strategy_track_cumulative_pnl`
- `pm_strategy_track_cumulative_return`
- `pm_strategy_track_contribution`
- `pm_track_allocation`
- `pm_track_revenue`

### Risk

- `pm_risk_asset_exposure_trend`
- `pm_risk_asset_exposure_by_fund`
- `pm_risk_asset_exposure_by_track`
- `pm_risk_style_exposure_trend`
- `pm_risk_style_exposure_by_fund`
- `pm_risk_style_exposure_by_track`
- `pm_risk_industry_exposure_trend`
- `pm_risk_industry_exposure_by_fund`
- `pm_risk_industry_exposure_by_track`
- `pm_risk_credit_exposure_trend`
- `pm_risk_credit_exposure_by_fund`
- `pm_risk_credit_exposure_by_track`
- `pm_risk_factor_exposure`
- `pm_adviser_factor_sensitivity`

### Holding

- `pm_holding_fund_navs`
- `pm_holding_fund_performance`
- `pm_holding_current_fund_stats`
- `pm_holding_historical_fund_stats`
- `pm_holding_yield_decomposition`
- `pm_holding_fund_correlation`
- `pm_holding_track_correlation`
- `pm_adviser_track_correlation`
- `pm_adviser_track_correlation_trend`
- `pm_adviser_correlation`
- `pm_holding_asset_exposure_by_fund`
- `pm_holding_style_exposure_by_fund`
