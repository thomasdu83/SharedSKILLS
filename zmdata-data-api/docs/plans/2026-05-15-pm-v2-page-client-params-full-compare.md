# PM V2 页面参数与 Client 默认参数全量核对

日期：2026-05-15  
页面：`http://10.168.40.65:2001/PMInfo/10287`  
PM_ID：`10287`

## 结论

已按 PMInfo 页面前端 chunk 和已抓取请求核对约 50 个接口调用点。Client 侧本轮已补齐/调整以下关键差异：

- 策略/基准比较相关接口默认 `bench_id` 改为 `/api/zmpmapi/fof/get_pm_strategy_bench` 返回的策略基准，不再使用 `get_global_params.bench_id`。
- 分策略净值、分赛道累计收益、分赛道收益贡献、策略/基准比较表等默认区间按页面使用 `all_begin_date` 到 `end_date`。
- 子基金相关性默认 `corr_type="Yield"`，默认区间按页面使用 `all_begin_date` 到 `end_date`。
- 投顾相关性补齐 `compare_begin_date`，默认取 `all_compare_begin_date`，`compare_end_date` 仍取同名字段。
- `pm_subfunds` 默认改为 `all_begin_date` 到 `end_date`，保持与页面构造一致。

非联网验证已通过：

```text
pytest zm_tests/test_portfolio_v2_structure.py zm_tests/test_request_logging.py
23 passed
```

## 全局默认参数来源

页面通过 `/api/zmpmapi/fof/get_global_params` 请求：

```json
{
  "pm_id": 10287,
  "type": 1,
  "begin_date": null,
  "end_date": null
}
```

Client 对齐原则：

- 用户显式传入参数优先。
- 日期参数为 `None` 时，从 `para_case_content` 同名字段取。
- 页面使用成立以来区间的接口，用 `all_begin_date` 和 `end_date/all_end_date`。
- 页面使用策略基准的接口，用 `/api/zmpmapi/fof/get_pm_strategy_bench` 获取 `BenchmarkPortID`。

## 核对表

| 模块 | 页面接口 | 页面请求参数默认 | Client 接口 | Client 默认参数 | 是否一致 |
|---|---|---|---|---|---|
| 初始化 | `webservice/pm/data/combine/queryPrivilege` | 权限查询 | 不封装 | 不属于 PM V2 分析数据接口 | 不纳入 |
| 初始化 | `/api/zmpmapi/allocation/get_pm_trading_day` | `pm_id` | 不封装 | 页面日期控件辅助接口 | 不纳入 |
| 初始化 | `/api/zmpmapi/fof/get_global_params` | `pm_id,type=1,begin_date=null,end_date=null` | `pm_analysis_config` | 同页面 | 一致 |
| 初始化 | `/api/zmpmapi/fof/get_pm_base_info` | `pm_id,end_date` | `pm_base_info` | `end_date` 取全局同名字段 | 一致 |
| 初始化 | `/api/zmpmapi/allocation/get_pm_hold_all` | `pm_id` | 不封装 | 页面持仓辅助数据 | 不纳入 |
| 初始化 | `webservice/pm/fof/fundList` | 页面子基金辅助列表 | 不封装 | webservice 旧接口 | 不纳入 |
| 组合表现 | `/api/zmpmapi/fof/get_performance_trend` | `pm_id,end_date,base_date=null` | `pm_performance_trend` | `end_date` 同名字段，`base_date=None` | 一致 |
| 组合表现 | `/api/zmpmapi/fof/get_performance_trend_list` | `pm_id,end_date` | `pm_nav` | `end_date` 同名字段 | 一致 |
| 组合表现 | `/api/zmpmapi/fof/get_pm_performance` | `pm_id,begin_date,end_date` | `pm_performance_stats` | 同名字段 | 一致 |
| 组合表现 | `/api/zmpmapi/fund/sub_fund_list` | `pm_id,begin_date=all_begin_date,end_date,sort={}` | `pm_subfunds` | `all_begin_date,end_date,sort={}` | 已调整一致 |
| 组合表现 | `/api/zmpmapi/fund/sub_fund_nav` | `fund_id` | `pm_subfund_nav` | `fund_id` | 一致 |
| 资产配置 | `/api/zmpmapi/fof/get_pm_strategy_yield_contri` | 净值图：`freq,all_begin_date,end_date` | `pm_strategy_nav` | `freq=W,all_begin_date,all_end_date/end_date` | 一致 |
| 资产配置 | `/api/zmpmapi/fof/get_pm_strategy_yield_contri` | 区间统计表：`freq,all_begin_date,end_date` | `pm_strategy_nav` | 同上 | 一致 |
| 资产配置 | `/api/zmpmapi/fof/get_pm_strategy_performance_thisperiod` | `begin_date,end_date,last_begin_date,last_end_date` | `pm_strategy_period_performance` | 同名字段 | 一致 |
| 资产配置 | `/api/zmpmapi/fof/get_pm_strategy_performance_allperiod` | `begin_date=all_begin_date,end_date=all_end_date` | `pm_strategy_full_period_performance` | `all_begin_date,all_end_date` | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_allocations` | `begin_date,end_date` | `pm_asset_allocation` | 同名字段 | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_allocations_contribute_new` | `begin_date,end_date` | `pm_strategy_cumulative_pnl` | 同名字段 | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_pm_strategy_accu_yield` | `begin_date,end_date` | `pm_strategy_cumulative_return` | 同名字段 | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_allocations_contribute_new_year` | `freq=W,begin_date,end_date` | `pm_strategy_pnl_by_period` | `freq=W,begin_date,end_date` | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/brinson_momentums` | `begin_date,end_date,brinson_type` | `pm_brinson_attribution` | 同名字段，默认 `brinson_type=4` | 一致 |
| 资产配置 | `/api/zmpmapi/fof/get_pm_performance_corr` | `begin_date=all_begin_date,end_date=end_date` | `pm_strategy_correlation` | `all_begin_date,all_end_date/end_date` | 一致 |
| 资产配置 | `/api/zmpmapi/fof/get_pm_strategy_bench` | `pm_id,strategy_type` | `pm_strategy_benchmark` | 同页面 | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_allocations_contr` | `pm_id,strategy_type,begin_date=成立日,end_date,base_date=null,bench_id=策略基准` | `pm_strategy_benchmark_comparison` | `all_begin_date,end_date,base_date=None,bench_id=策略基准` | 已调整一致 |
| 资产配置 | `/api/zmpmapi/fof/get_strategy_performance_list` | `pm_id,strategy_type,begin_date=all_begin_date,end_date,bench_id=策略基准` | `pm_strategy_performance_list` | 同页面 | 已调整一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_race_list` | `pm_id,end_date=all_end_date,strategy_type` | `pm_strategy_tracks` | `end_date` 默认最新净值日 | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_race_allocation` | `begin_date,end_date,strategy_type` | `pm_strategy_track_allocation` | 同名字段 | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_revenue` | `end_date,strategy_type` | `pm_strategy_track_cumulative_pnl` | `end_date` 同名字段 | 一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_race_accu_yield` | `begin_date=all_begin_date,end_date,strategy_type` | `pm_strategy_track_cumulative_return` | `all_begin_date,end_date` | 已调整一致 |
| 资产配置 | `/api/zmpmapi/allocation/get_strategy_race_contri` | `begin_date=all_begin_date,end_date,strategy_type` | `pm_strategy_track_contribution` | `all_begin_date,end_date` | 已调整一致 |
| 风险配置 | `/api/zmpmapi/fof_fund/calc_strategy_asset_exposure_timing` | `pm_id_list,pm_id,end_date,strategy_type` | `pm_risk_asset_exposure_trend` | 同页面 | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_asset_by_fund` | `pm_id,end_date,strategy_type` | `pm_risk_asset_exposure_by_fund` | 同页面，不默认加 `bench_id` | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_asset_by_race` | `pm_id,end_date,strategy_type` | `pm_risk_asset_exposure_by_track` | 同页面，不默认加 `bench_id` | 一致 |
| 风险配置 | `/api/zmpmapi/fof_fund/calc_strategy_style_exposure_timing` | `pm_id_list,pm_id,end_date,strategy_type` | `pm_risk_style_exposure_trend` | 同页面 | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_style_by_fund` | `pm_id,end_date,strategy_type,bench_id` | `pm_risk_style_exposure_by_fund` | `bench_id` 默认策略基准 | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_style_by_race` | `pm_id,end_date,strategy_type,bench_id` | `pm_risk_style_exposure_by_track` | `bench_id` 默认策略基准 | 一致 |
| 风险配置 | `/api/zmpmapi/fof_fund/calc_strategy_industry_exposure_timing` | `pm_id_list,pm_id,end_date,strategy_type` | `pm_risk_industry_exposure_trend` | 同页面 | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_industry_by_fund` | `pm_id,end_date,strategy_type,bench_id` | `pm_risk_industry_exposure_by_fund` | `bench_id` 默认策略基准 | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_industry_by_race` | `pm_id,end_date,strategy_type,bench_id` | `pm_risk_industry_exposure_by_track` | `bench_id` 默认策略基准 | 一致 |
| 风险配置 | `/api/zmpmapi/fof_fund/calc_strategy_credit_exposure_timing` | `pm_id_list,pm_id,end_date,strategy_type` | `pm_risk_credit_exposure_trend` | 同页面 | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_credit_by_fund` | `pm_id,end_date,strategy_type,bench_id` | `pm_risk_credit_exposure_by_fund` | `bench_id` 默认策略基准 | 一致 |
| 风险配置 | `/api/zmpmapi/risk_control/risk_exposure_credit_by_race` | `pm_id,end_date,strategy_type,bench_id` | `pm_risk_credit_exposure_by_track` | `bench_id` 默认策略基准 | 一致 |
| 风险配置 | `/api/zmpmapi/factor/risk_factor_exposure` | `pm_id,strategy_type,begin_date,end_date` | `pm_risk_factor_exposure` | 同名字段 | 一致 |
| 风险配置 | `/api/zmpmapi/factor/adviser_factor_sensitivity` | `pm_id,end_date` | `pm_adviser_factor_sensitivity` | `end_date` 同名字段 | 一致 |
| 持仓分析 | `/api/zmpmapi/allocation/get_strategy_fund_net_value` | `pm_id,end_date,strategy_type,compare_end_date,sorce_id_list,race_name_list,is_origin,bench_id` | `pm_holding_fund_navs` | 同页面，`bench_id` 默认策略基准 | 一致 |
| 持仓分析 | `/api/zmpmapi/allocation/get_strategy_fund_net_value_download` | 导出请求 | 不封装 | 下载型接口 | 不纳入 |
| 持仓分析 | `/api/zmpmapi/fund_similar/fund_performance` | `begin_date,end_date,last_*,compare_*,compare_last_*` | `pm_holding_fund_performance` | 同名字段 | 一致 |
| 持仓分析 | `/api/zmpmapi/fund/pms_current_fund_statis` | `begin_date,end_date,strategy_type,bench_id=策略基准,race_name_list=null` | `pm_holding_current_fund_stats` | 同页面 | 一致 |
| 持仓分析 | `/api/zmpmapi/fund/pms_historical_fund_statis` | `end_date,strategy_type,bench_id=策略基准,race_name_list=null` | `pm_holding_historical_fund_stats` | 同页面，不默认传 `begin_date` | 一致 |
| 持仓分析 | `/api/zmpmapi/fund/calcSubFundYieldDecompose` | `pm_id,strategy_type,freq=W,end_date` | `pm_holding_yield_decomposition` | 同页面 | 一致 |
| 持仓分析 | `/api/zmpmapi/fund/calc_subfund_corr_race` | `begin_date=all_begin_date,end_date,strategy_type,is_history=0,corr_type=Yield` | `pm_holding_track_correlation` | `all_begin_date,end_date,is_history=0,corr_type=Yield` | 已调整一致 |
| 持仓分析 | `/api/zmpmapi/fund/calcSubFundCorr` | `begin_date=all_begin_date,end_date,strategy_type,is_history=0,corr_type=Yield,race_name_list` | `pm_holding_fund_correlation` | 同页面 | 已调整一致 |
| 持仓分析 | `/api/zmpmapi/advistor/yield_corr_track` | `end_date,compare_begin_date=all_compare_begin_date,compare_end_date,strategy_type,bench_id=策略基准` | `pm_adviser_track_correlation` | 同页面 | 已调整一致 |
| 持仓分析 | `/api/zmpmapi/advistor/yield_corr_sequence_track` | `end_date,compare_end_date,strategy_type,bench_id=策略基准` | `pm_adviser_track_correlation_trend` | 同页面 | 一致 |
| 持仓分析 | `/api/zmpmapi/advistor/yield_corr_advistor` | `end_date,compare_begin_date=all_compare_begin_date,compare_end_date,strategy_type,bench_id=策略基准` | `pm_adviser_correlation` | 同页面 | 已调整一致 |
| 持仓分析 | `/api/zmpmapi/fund_similar/fund_exposure` | 基金画像/暴露扩展 | 不封装 | PM V2 首轮未纳入 | 不纳入 |
| 持仓分析 | `/api/zmpmapi/fund_similar/fund_exposure_industry` | 基金行业暴露扩展 | 不封装 | PM V2 首轮未纳入 | 不纳入 |

## 说明

- 页面存在同一接口在多个模块重复调用的情况，例如 `get_pm_strategy_yield_contri`、`get_strategy_race_list`、`get_pm_strategy_bench`。Client 只保留一个语义明确的包装函数或内部 helper。
- 页面首次加载 `get_strategy_fund_net_value` 可能先出现一次 `bench_id=null` 的过渡请求，随后 `get_pm_strategy_bench` 返回后会以策略基准重发。Client 默认直接补齐策略基准，按稳定态请求对齐。
- `all_end_date` 和 `end_date` 在 10287 样例中同为 `2026-05-12`。表中按前端代码语义记录；Client 对使用者可见的默认效果保持一致。
