# PM V2 Global Params Date Defaults Plan

日期：2026-05-15

## 背景

PMInfo 网页端通过 `/api/zmpmapi/fof/get_global_params` 获取默认分析区间、比较区间、成立以来区间和默认基准。SDK 中原有 PM V2 接口使用本地静态默认值，例如 `today`、`2020-01-01` 和 `previous_period`，与网页端默认分析口径可能不一致。

## 实施原则

- 当接口日期类参数为 `None` 时，优先从 `get_global_params` 返回的 `para_case_content` 中按同名字段填充。
- 用户显式传入的参数永远优先，不被全局参数覆盖。
- `get_global_params` 使用 `type=1`，不暴露 `UserID`。
- `compare_*` 日期不在 SDK 本地重新计算，直接沿用服务端返回的周日对齐字段。
- 如果 `get_global_params` 获取失败、返回空或缺少字段，沿用旧逻辑回退，保持向后兼容。

## 字段映射

- 普通区间：`begin_date`、`end_date`
- 上期区间：`last_begin_date`、`last_end_date`
- 同类比较区间：`compare_begin_date`、`compare_end_date`
- 同类比较上期区间：`compare_last_begin_date`、`compare_last_end_date`
- 成立以来区间：`all_begin_date`、`all_end_date`
- 默认基准：`bench_id`

## APIClientResearch 修改

- 在 `zmdata/apis/pm_v2/_client.py` 中增加：
  - `analysis_config_df`
  - `global_params_content`
  - `coalesce_global`
  - 进程内短缓存，key 为 `pm_id + begin_date + end_date + x_mars_token`
- 在 `support.py` 中增加公开接口：
  - `pm_analysis_config(pm_id, begin_date=None, end_date=None, x_mars_token=None)`
- 在 `performance.py`、`allocation.py`、`risk.py`、`holding.py` 中，将日期默认值改为优先读取全局参数。
- `pm_strategy_full_period_performance` 默认使用 `all_begin_date/all_end_date`。
- 支持 `bench_id` 的接口在 `bench_id=None` 时默认读取全局 `bench_id`。

## 测试计划

- 非联网单测 mock `para_case_content`，验证日期和 `bench_id` 按字段填充。
- 验证显式传参优先。
- 验证全局参数为空时回退旧逻辑。
- 验证持仓绩效使用 `compare_last_begin_date/compare_last_end_date`。
- 可选真实联调：`pm_analysis_config(10287)` 和 `pm_holding_fund_performance(10287, strategy_type=1)`。

