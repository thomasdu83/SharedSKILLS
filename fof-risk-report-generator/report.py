import argparse
import html
import json
import logging
import os
import sys

import numpy as np
import pandas as pd
import zmdata as api
from typing import Optional


PM_ID = 10898
BEGIN_DATE = pd.Timestamp("2026-02-01")
OUTPUT_HTML_PATH = os.path.join(os.path.dirname(__file__), "FOF_投后归因报告.html")
TOPN = 5


ST_NAME = {1: "股票多头", 3: "市场中性", 4: "债券", 5: "CTA", 9: "ETF"}

_SUBFUNDS_CACHE: dict[tuple[int, str, str], pd.DataFrame] = {}

BENCHID_TO_FIELD = {
    23003: "growth",
    23004: "valuation",
    23005: "profit",
    23006: "size",
    23007: "volatility",
    23008: "liquidity",
    23009: "momentum",
    23010: "leverage",
    23011: "beta",
    23012: "non_linear",
    23013: "dividend",
    23014: "short_reversal",
    23015: "seasonality",
    23016: "long_reversal",
    23017: "profit_volatility",
    23018: "profit_quality",
    23019: "investment_quality",
    23020: "pb",
    23021: "analyst_forecast",
    23022: "industry_momentum",
    10660: "if_basis",
    10661: "ic_basis",
}


def _safe_str(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and np.isnan(x):
        return ""
    return str(x)


def _fmt_pct(x, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x * 100:.{digits}f}%"


def _fmt_bp_from_return(x, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x * 10000:.{digits}f}bp"


def _fmt_bp(x_bp, digits: int = 1) -> str:
    if x_bp is None or (isinstance(x_bp, float) and np.isnan(x_bp)):
        return "-"
    return f"{float(x_bp):.{digits}f}bp"


def _fmt_float(x, digits: int = 3) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{float(x):.{digits}f}"


def _render_table(headers: list[str], rows: list[list[object]]) -> str:
    th = "".join([f"<th>{html.escape(h)}</th>" for h in headers])
    trs = []
    for r in rows:
        tds = "".join([f"<td>{html.escape(_safe_str(v))}</td>" for v in r])
        trs.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def _is_cumulative_series(s: pd.Series) -> bool:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.size < 3:
        return False
    level = float(np.nanmedian(np.abs(x.to_numpy(dtype=float))))
    if level <= 0:
        return False
    diff = float(np.nanmedian(np.abs(x.diff().dropna().to_numpy(dtype=float))))
    return (diff / level) < 0.7


def _interval_sum_or_diff(s: pd.Series) -> Optional[float]:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return None
    return float(x.iloc[-1] - x.iloc[0]) if _is_cumulative_series(x) else float(x.sum())


def _interval_compound_or_diff(s: pd.Series) -> Optional[float]:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return None
    if _is_cumulative_series(x):
        return float(x.iloc[-1] - x.iloc[0])
    return float(np.prod(1.0 + x.to_numpy(dtype=float)) - 1.0)


def _format_topn_text(df: pd.DataFrame, *, name_col: str, value_col: str, k: int = 3, value_fmt=_fmt_bp_from_return) -> str:
    if not isinstance(df, pd.DataFrame) or df.empty or name_col not in df.columns or value_col not in df.columns:
        return "-"
    d = df[[name_col, value_col]].copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    d = d.dropna(subset=[value_col])
    if d.empty:
        return "-"
    items = []
    for _, r in d.head(int(k)).iterrows():
        items.append(f"{_safe_str(r[name_col])}（{value_fmt(r[value_col])}）")
    return "，".join(items) if items else "-"


def _shorten_text(s: object, max_len: int = 420) -> str:
    t = _safe_str(s)
    if t.startswith("{") and t.endswith("}"):
        try:
            obj = json.loads(t)
            if isinstance(obj, dict) and ("msg" in obj or "detail" in obj or "code" in obj):
                parts = []
                if "code" in obj:
                    parts.append(f"code={_safe_str(obj.get('code'))}")
                if "msg" in obj:
                    parts.append(f"msg={_safe_str(obj.get('msg'))}")
                if "detail" in obj:
                    det = _safe_str(obj.get("detail"))
                    det_lines = [x.strip() for x in det.splitlines() if x.strip()]
                    det_short = " / ".join(det_lines[:3]) if det_lines else det
                    parts.append(f"detail={det_short}")
                t = " | ".join(parts) if parts else t
        except Exception:
            pass
    if len(t) <= int(max_len):
        return t
    return t[: int(max_len)] + "…"


def _ensure_pm_key() -> None:
    pm_key = os.environ.get("ZM_PM_API_KEY") or os.environ.get("PM_API_KEY")
    if hasattr(api, "PM_API_KEY") and pm_key:
        api.PM_API_KEY = pm_key
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("zmdata.api").setLevel(logging.WARNING)
    logging.getLogger("zmdata").setLevel(logging.WARNING)


def _resolve_pm_id_by_name(product_name: str) -> tuple[int, str]:
    df = api.pm_info_list(pm_id_list=[])
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise SystemExit("pm_info_list 返回为空，无法根据名称定位 pm_id")
    d = df.copy()
    name_cols = [c for c in ["fundShortName", "fund_short_name", "fundName", "fund_name", "product_name"] if c in d.columns]
    if not name_cols:
        raise SystemExit("pm_info_list 未包含可用的名称列，无法根据名称定位 pm_id")
    pm_cols = [c for c in ["pm_id", "pmID", "PMID", "pmId", "pMID"] if c in d.columns]
    if not pm_cols:
        raise SystemExit("pm_info_list 未包含可用的 pm_id 列，无法根据名称定位 pm_id")
    name_col = name_cols[0]
    pm_col = pm_cols[0]
    d[name_col] = d[name_col].astype(str)
    cand = d[d[name_col].str.contains(str(product_name), na=False)].copy()
    if cand.empty:
        raise SystemExit(f"未找到产品：{product_name}")
    exact = cand[cand[name_col] == str(product_name)]
    pick = exact.iloc[0] if not exact.empty else cand.assign(_len=cand[name_col].str.len()).sort_values(["_len", name_col]).iloc[0]
    pm_id = int(pd.to_numeric(pick[pm_col], errors="coerce"))
    if not pm_id:
        raise SystemExit(f"匹配到的 pm_id 无效：{_safe_str(pick.get(pm_col))}")
    return pm_id, str(pick[name_col])


def _get_pm_subfunds(pm_id: int, begin_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    key = (int(pm_id), str(begin_date.date()), str(end_date.date()))
    cached = _SUBFUNDS_CACHE.get(key)
    if isinstance(cached, pd.DataFrame):
        return cached
    df = api.pm_subfunds(pm_id=pm_id, begin_date=str(begin_date.date()), end_date=str(end_date.date()))
    out = df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    _SUBFUNDS_CACHE[key] = out
    return out


def _get_end_date(pm_id: int, begin_date: pd.Timestamp) -> pd.Timestamp:
    try:
        cfg = api.pm_analysis_config(pm_id=pm_id, begin_date=str(begin_date.date()))
        if isinstance(cfg, pd.DataFrame) and (not cfg.empty) and "para_case_content" in cfg.columns:
            para = cfg.iloc[0]["para_case_content"]
            if isinstance(para, str):
                try:
                    para = json.loads(para)
                except Exception:
                    para = None
            if isinstance(para, dict) and para.get("end_date"):
                ed = pd.to_datetime(para.get("end_date"), errors="coerce")
                if not pd.isna(ed):
                    return pd.Timestamp(ed)
    except Exception:
        pass

    base = api.pm_base_info(pm_id=pm_id)
    if isinstance(base, pd.DataFrame) and (not base.empty):
        for k in ["date", "数据日期", "TradingDay", "trading_day", "maxTradingDay", "max_trading_day"]:
            if k in base.columns:
                ed = pd.to_datetime(base.iloc[0][k], errors="coerce")
                if not pd.isna(ed):
                    return pd.Timestamp(ed)

    return pd.Timestamp.today()


def _nav_kpis(pm_id: int, begin_date: pd.Timestamp, end_date: pd.Timestamp) -> tuple[pd.DataFrame, dict]:
    nav = api.pm_nav(pm_id=pm_id, end_date=str(end_date.date()))
    nav = nav.copy()
    nav["trading_day"] = pd.to_datetime(nav["trading_day"], errors="coerce")
    nav = nav.sort_values("trading_day")
    nav["unit_netvalue"] = pd.to_numeric(nav["unit_netvalue"], errors="coerce")
    nav = nav.dropna(subset=["trading_day", "unit_netvalue"])
    nav = nav[(nav["trading_day"] <= end_date)].reset_index(drop=True)

    if nav.empty:
        return nav, {
            "interval_return": None,
            "max_drawdown": None,
            "peak_date": None,
            "trough_date": None,
            "annual_return": None,
            "annual_vol": None,
            "sharpe": None,
            "n_days": 0,
            "begin_used": None,
            "begin_next_used": None,
            "end_used": None,
        }

    prev = nav[nav["trading_day"] < begin_date]
    if not prev.empty:
        begin_base = pd.Timestamp(prev["trading_day"].iloc[-1])
    else:
        nxt = nav[nav["trading_day"] >= begin_date]
        begin_base = pd.Timestamp(nxt["trading_day"].iloc[0]) if not nxt.empty else pd.Timestamp(nav["trading_day"].iloc[0])

    nav = nav[(nav["trading_day"] >= begin_base) & (nav["trading_day"] <= end_date)].reset_index(drop=True)

    if len(nav) < 2:
        return nav, {
            "interval_return": None,
            "max_drawdown": None,
            "peak_date": None,
            "trough_date": None,
            "annual_return": None,
            "annual_vol": None,
            "sharpe": None,
            "n_days": 0,
            "begin_used": None,
            "begin_next_used": None,
            "end_used": None,
        }

    begin_used = pd.Timestamp(nav["trading_day"].iloc[0])
    begin_next_used = pd.Timestamp(nav["trading_day"].iloc[1]) if len(nav) >= 2 else None
    end_used = pd.Timestamp(nav["trading_day"].iloc[-1])

    interval_return = float(nav["unit_netvalue"].iloc[-1] / nav["unit_netvalue"].iloc[0] - 1.0)
    daily_ret = nav["unit_netvalue"].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    n_days = int(len(daily_ret))
    annual_return = float((1.0 + interval_return) ** (252.0 / max(n_days, 1)) - 1.0) if (1.0 + interval_return) > 0 else None
    annual_vol = float(daily_ret.std(ddof=1) * np.sqrt(252.0)) if n_days > 1 else None
    sharpe = float(annual_return / annual_vol) if annual_return is not None and annual_vol not in (None, 0.0) else None

    cummax = nav["unit_netvalue"].cummax()
    dd = nav["unit_netvalue"] / cummax - 1.0
    trough_idx = int(dd.idxmin())
    max_drawdown = float(dd.iloc[trough_idx])
    peak_idx = int(nav["unit_netvalue"].iloc[: trough_idx + 1].idxmax())
    peak_date = str(pd.Timestamp(nav["trading_day"].iloc[peak_idx]).date())
    trough_date = str(pd.Timestamp(nav["trading_day"].iloc[trough_idx]).date())

    return nav, {
        "interval_return": interval_return,
        "max_drawdown": max_drawdown,
        "peak_date": peak_date,
        "trough_date": trough_date,
        "annual_return": annual_return,
        "annual_vol": annual_vol,
        "sharpe": sharpe,
        "n_days": n_days,
        "begin_used": str(begin_used.date()),
        "begin_next_used": str(begin_next_used.date()) if begin_next_used is not None else None,
        "end_used": str(end_used.date()),
    }


def _strategy_layer(pm_id: int, begin_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    fetch_begin = begin_date - pd.Timedelta(days=14)
    df = api.pm_strategy_nav(pm_id=pm_id, freq="D", begin_date=str(fetch_begin.date()), end_date=str(end_date.date()))
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["trading_day"] = pd.to_datetime(df["trading_day"], errors="coerce")
    df = df[(df["trading_day"] >= fetch_begin) & (df["trading_day"] <= end_date)].sort_values("trading_day").reset_index(drop=True)

    mapping = {
        "股票多头": ("StockRatio", "StockNetValue", "StockYield"),
        "市场中性": ("MarketneutralityRatio", "MarketneutralityNetValue", "MarketneutralityYield"),
        "CTA": ("CTARatio", "CTANetValue", "CTAYield"),
        "债券": ("BondRatio", "BondNetValue", "BondYield"),
        "ETF": ("ETFRatio", "ETFNetValue", "ETFYield"),
    }

    rows = []
    win = (df["trading_day"] > begin_date) & (df["trading_day"] <= end_date)
    win_prev_in = win & (df["trading_day"].shift(1) >= begin_date)
    for name, (c_ratio, c_nv, c_yld) in mapping.items():
        ratio = pd.to_numeric(df.get(c_ratio), errors="coerce")
        nv = pd.to_numeric(df.get(c_nv), errors="coerce")
        yld = pd.to_numeric(df.get(c_yld), errors="coerce")

        avg_ratio = float(ratio[win].dropna().mean()) if ratio is not None and ratio[win].notna().any() else None

        interval_yield = None
        if nv is not None and nv.notna().sum() >= 2:
            nv0 = nv[df["trading_day"] <= begin_date].dropna()
            nv1 = nv[df["trading_day"] <= end_date].dropna()
            if (not nv0.empty) and (not nv1.empty) and float(nv0.iloc[-1]) != 0:
                interval_yield = float(nv1.iloc[-1] / nv0.iloc[-1] - 1.0)
        elif yld is not None and yld[win].notna().any():
            interval_yield = float(np.prod(1.0 + yld[win].dropna().to_numpy(dtype=float)) - 1.0)

        contrib = None
        if nv is not None and nv.notna().sum() >= 2:
            r = nv.pct_change()
            w_prev = ratio.shift(1) if ratio is not None else None
            if w_prev is not None:
                contrib = r * w_prev
        elif yld is not None and yld.notna().any():
            w_prev = ratio.shift(1) if ratio is not None else None
            if w_prev is not None:
                contrib = yld * w_prev

        interval_contri = float(contrib[win_prev_in].dropna().sum()) if contrib is not None and contrib[win_prev_in].notna().any() else None
        rows.append({"strategy": name, "avg_ratio": avg_ratio, "interval_yield": interval_yield, "interval_contri": interval_contri})

    return pd.DataFrame(rows)


def _track_layer(pm_id: int, strategy_type: int, begin_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    tc = api.pm_strategy_track_contribution(
        pm_id=pm_id,
        strategy_type=strategy_type,
        begin_date=str(begin_date.date()),
        end_date=str(end_date.date()),
    )
    if not isinstance(tc, pd.DataFrame) or tc.empty:
        return pd.DataFrame(columns=["race_name", "avg_ratio", "track_return", "track_contrib"])
    d = tc.copy()
    base_td = begin_date
    if "trading_day" in d.columns:
        d["trading_day"] = pd.to_datetime(d["trading_day"], errors="coerce")
        d = d.dropna(subset=["trading_day"])
        d = d[(d["trading_day"] <= end_date)]
        td0 = d.loc[d["trading_day"] <= begin_date, "trading_day"]
        base_td = pd.Timestamp(td0.max()) if (not td0.empty) else pd.Timestamp(d["trading_day"].min())
        d = d[(d["trading_day"] >= base_td)]
    contrib_cols = [c for c in d.columns if isinstance(c, str) and c.endswith("贡献")]

    alloc = api.pm_strategy_track_allocation(
        pm_id=pm_id,
        strategy_type=strategy_type,
        begin_date=str(begin_date.date()),
        end_date=str(end_date.date()),
    )
    alloc2 = alloc.copy() if isinstance(alloc, pd.DataFrame) else pd.DataFrame()
    if not alloc2.empty and "trading_day" in alloc2.columns:
        alloc2["trading_day"] = pd.to_datetime(alloc2["trading_day"], errors="coerce")
        alloc2 = alloc2.dropna(subset=["trading_day"])
        alloc2 = alloc2[(alloc2["trading_day"] > base_td) & (alloc2["trading_day"] <= end_date)]

    rows = []
    if "trading_day" in d.columns:
        d = d.sort_values("trading_day").reset_index(drop=True)
        win_main = (d["trading_day"] > base_td) & (d["trading_day"] <= end_date)
    else:
        win_main = pd.Series([True] * len(d), index=d.index)
    for c in contrib_cols:
        rn = c[: -len("贡献")].strip()
        cs = pd.to_numeric(d[c], errors="coerce").dropna()
        if cs.empty:
            total_contrib = None
        elif _is_cumulative_series(cs):
            total_contrib = float(cs.iloc[-1] - cs.iloc[0])
        else:
            total_contrib = float(pd.to_numeric(d.loc[win_main, c], errors="coerce").dropna().sum())
        ycol = f"{rn}收益"
        interval_ret = None
        if ycol in d.columns:
            ys = pd.to_numeric(d[ycol], errors="coerce").dropna()
            if not ys.empty and _is_cumulative_series(ys):
                interval_ret = float(ys.iloc[-1] - ys.iloc[0])
            else:
                y_win = pd.to_numeric(d.loc[win_main, ycol], errors="coerce").dropna()
                interval_ret = float(np.prod(1.0 + y_win.to_numpy(dtype=float)) - 1.0) if not y_win.empty else None
        avg_ratio = None
        if not alloc2.empty and rn in alloc2.columns:
            avg_ratio = float(pd.to_numeric(alloc2[rn], errors="coerce").dropna().mean()) if alloc2[rn].notna().any() else None
        rows.append({"race_name": rn, "avg_ratio": avg_ratio, "track_return": interval_ret, "track_contrib": total_contrib})
    out = pd.DataFrame(rows).dropna(subset=["track_contrib"], how="all")
    return out.sort_values("track_contrib").reset_index(drop=True) if not out.empty else out


def _select_drilldown(track_contrib: pd.DataFrame, top_k: int = 2, abs_threshold_bp: float = 20.0) -> pd.DataFrame:
    if track_contrib.empty:
        return pd.DataFrame(columns=["race_name", "track_contrib", "reason"])
    df = track_contrib.copy()
    df["abs_bp"] = df["track_contrib"].abs() * 10000.0
    sel = df[df["abs_bp"] >= float(abs_threshold_bp)].copy()
    if sel.empty:
        head = df.nsmallest(int(top_k), "track_contrib")
        tail = df.nlargest(int(top_k), "track_contrib")
        sel = pd.concat([head, tail], ignore_index=True).drop_duplicates(subset=["race_name"])
        sel["reason"] = f"top{int(top_k)}/bottom{int(top_k)}"
    else:
        sel["reason"] = f"|contrib|≥{abs_threshold_bp:.0f}bp"
    return sel[["race_name", "track_contrib", "reason"]].sort_values("track_contrib").reset_index(drop=True)


def _parse_yield_decomp(res) -> pd.DataFrame:
    if res is None or not isinstance(res, pd.DataFrame) or res.empty:
        return pd.DataFrame()
    row0 = res.iloc[0]
    bar = row0.get("bar", None)
    if isinstance(bar, str):
        try:
            bar = json.loads(bar)
        except Exception:
            bar = None
    if not isinstance(bar, dict):
        return pd.DataFrame()
    rows = []
    for k, lst in bar.items():
        td = pd.to_datetime(k, errors="coerce")
        for it in (lst or []):
            if isinstance(it, dict):
                r = dict(it)
                r["TradingDay_key"] = td
                rows.append(r)
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    if df.empty:
        return df
    df["TradingDay_key"] = pd.to_datetime(df["TradingDay_key"], errors="coerce")
    df["FundID"] = pd.to_numeric(df.get("FundID"), errors="coerce")
    df["Yield"] = pd.to_numeric(df.get("Yield"), errors="coerce")
    df["NetValue"] = pd.to_numeric(df.get("NetValue"), errors="coerce")
    if "Name" in df.columns:
        df["Name"] = df["Name"].astype(str)
    else:
        df["Name"] = ""
    return df


def _subfund_topn(
    pm_id: int,
    begin_date: pd.Timestamp,
    end_date: pd.Timestamp,
    strategy_type: int,
    selected_races: pd.DataFrame,
) -> tuple[dict, str]:
    tracks = api.pm_strategy_tracks(pm_id=pm_id, strategy_type=strategy_type, end_date=str(end_date.date()))
    if not isinstance(tracks, pd.DataFrame) or tracks.empty:
        return {}, "赛道映射表为空，无法下钻子基金。"
    tracks = tracks.copy()
    tracks["fund_id"] = pd.to_numeric(tracks.get("fund_id"), errors="coerce")
    tracks["ratio"] = pd.to_numeric(tracks.get("ratio"), errors="coerce")
    tracks["fund_short_name"] = tracks.get("fund_short_name")
    tracks["race_name"] = tracks.get("race_name")

    ratio_col = {1: "StockRatio", 3: "MarketneutralityRatio", 4: "BondRatio", 5: "CTARatio", 9: "ETFRatio"}.get(strategy_type, None)
    nv_col = {1: "StockNetValue", 3: "MarketneutralityNetValue", 4: "BondNetValue", 5: "CTANetValue", 9: "ETFNetValue"}.get(strategy_type, None)
    yld_col = {1: "StockYield", 3: "MarketneutralityYield", 4: "BondYield", 5: "CTAYield", 9: "ETFYield"}.get(strategy_type, None)
    strat_interval_contri = None
    strat_avg_ratio = None
    if ratio_col:
        try:
            strat_nav = api.pm_strategy_nav(
                pm_id=pm_id,
                freq="D",
                begin_date=str((begin_date - pd.Timedelta(days=30)).date()),
                end_date=str(end_date.date()),
            )
        except Exception:
            strat_nav = pd.DataFrame()
        if isinstance(strat_nav, pd.DataFrame) and (not strat_nav.empty) and ("trading_day" in strat_nav.columns):
            s = strat_nav.copy()
            s["trading_day"] = pd.to_datetime(s["trading_day"], errors="coerce")
            s = s.dropna(subset=["trading_day"]).sort_values("trading_day").reset_index(drop=True)
            win = (s["trading_day"] > begin_date) & (s["trading_day"] <= end_date)
            win_prev_in = win & (s["trading_day"].shift(1) >= begin_date)
            ratio = pd.to_numeric(s.get(ratio_col), errors="coerce")
            strat_avg_ratio = float(ratio[win].dropna().mean()) if ratio is not None and ratio[win].notna().any() else None
            nv = pd.to_numeric(s.get(nv_col), errors="coerce") if nv_col else None
            yld = pd.to_numeric(s.get(yld_col), errors="coerce") if yld_col else None

            contrib = None
            if nv is not None and nv.notna().sum() >= 2 and ratio is not None:
                r = nv.pct_change()
                contrib = r * ratio.shift(1)
            elif yld is not None and yld.notna().any() and ratio is not None:
                contrib = yld * ratio.shift(1)
            strat_interval_contri = float(contrib[win_prev_in].dropna().sum()) if contrib is not None and contrib[win_prev_in].notna().any() else None

    yd = api.pm_holding_yield_decomposition(pm_id=pm_id, strategy_type=strategy_type, freq="W", end_date=str(end_date.date()))
    bars = _parse_yield_decomp(yd)
    if bars.empty:
        return {}, "周度子基金收益分解为空，无法下钻子基金。"
    begin_anchor = begin_date - pd.Timedelta(days=int((begin_date.dayofweek + 1) % 7))
    end_anchor = end_date - pd.Timedelta(days=int((end_date.dayofweek + 1) % 7))
    bars = bars[(bars["TradingDay_key"] >= begin_anchor) & (bars["TradingDay_key"] <= end_anchor)]
    if bars.empty:
        return {}, "区间内周度数据为空，无法下钻子基金。"

    subfunds = _get_pm_subfunds(pm_id=pm_id, begin_date=begin_date, end_date=end_date)
    sub_w = pd.DataFrame()
    if isinstance(subfunds, pd.DataFrame) and (not subfunds.empty):
        sub_w = subfunds.copy()
        if "fundID" in sub_w.columns:
            sub_w["FundID"] = pd.to_numeric(sub_w.get("fundID"), errors="coerce")
        else:
            sub_w["FundID"] = pd.to_numeric(sub_w.get("FundID"), errors="coerce")
        sub_w["weight"] = pd.to_numeric(sub_w.get("weight"), errors="coerce")
        keep_cols = ["FundID", "weight"]
        for c in ["fundName", "FundName", "race", "strategyClass", "lastWeight", "lastWeightDay"]:
            if c in sub_w.columns:
                keep_cols.append(c)
        sub_w = sub_w[keep_cols].dropna(subset=["FundID"]).drop_duplicates(subset=["FundID"])

    m = bars[["TradingDay_key", "FundID", "Name", "Yield", "NetValue"]].merge(
        tracks[["fund_id", "fund_short_name", "race_name", "ratio"]].drop_duplicates(subset=["fund_id"]),
        left_on="FundID",
        right_on="fund_id",
        how="left",
        indicator=True,
    )
    m["y"] = pd.to_numeric(m.get("Yield"), errors="coerce")
    m = m.dropna(subset=["TradingDay_key", "FundID"]).copy()

    m = m.sort_values(["FundID", "TradingDay_key"]).reset_index(drop=True)
    m["td_prev"] = m.groupby("FundID")["TradingDay_key"].shift(1)
    valid = (m["TradingDay_key"] > begin_anchor) & (m["td_prev"] >= begin_anchor)
    m["y_inc"] = m.groupby("FundID")["y"].transform(lambda s: s.diff() if _is_cumulative_series(s) else s)

    raw = pd.to_numeric(m["y_inc"], errors="coerce").where(valid, 0.0).fillna(0.0)
    total_raw = float(raw.sum())
    scale_decomp = float(strat_interval_contri / total_raw) if strat_interval_contri is not None and total_raw != 0.0 else None
    use_decomp = bool(scale_decomp is not None and scale_decomp > 0 and 0.05 <= abs(scale_decomp) <= 5.0)
    m["contrib_est"] = raw * float(scale_decomp) if use_decomp else raw

    abs_raw = raw.abs().fillna(0.0)
    denom = float(abs_raw.sum())
    numer = float(abs_raw[m["_merge"] == "both"].sum())
    cov_track_abs = numer / denom if denom > 0 else None
    cov_track_rows = float((m.loc[valid, "_merge"] == "both").mean()) if int(valid.sum()) else None

    m["display_name"] = m["fund_short_name"].where(m["fund_short_name"].notna(), m["Name"])
    if not sub_w.empty:
        m = m.merge(sub_w, on="FundID", how="left")
    if "FundName" in m.columns:
        m["display_name"] = m["display_name"].where(m["display_name"].notna(), m["FundName"])
    if "fundName" in m.columns:
        m["display_name"] = m["display_name"].where(m["display_name"].notna(), m["fundName"])
    if "race" in m.columns:
        m["race_name"] = m["race_name"].where(m["race_name"].notna(), m["race"])
    m["race_name"] = m["race_name"].replace({"nan": np.nan, "None": np.nan})
    m["race_name"] = m["race_name"].fillna("未映射/需核对")

    cov_race_rows = float((m.loc[valid, "race_name"] != "未映射/需核对").mean()) if int(valid.sum()) else None
    numer2 = float(abs_raw[m["race_name"] != "未映射/需核对"].sum())
    cov_race_abs = numer2 / denom if denom > 0 else None

    m["w"] = pd.to_numeric(m.get("ratio"), errors="coerce")
    m["w"] = m["w"].where(m["w"].notna() & (m["w"] > 0), pd.to_numeric(m.get("weight"), errors="coerce"))
    m["w"] = m["w"].fillna(0.0)
    ratio0 = pd.to_numeric(m.get("ratio"), errors="coerce")
    weight0 = pd.to_numeric(m.get("weight"), errors="coerce")
    m["w_src"] = np.where(ratio0.notna() & (ratio0 > 0), "tracks", np.where(weight0.notna() & (weight0 > 0), "subfunds", "none"))

    fund_ret = {}
    fund_mdd = {}
    for fid, g in m.groupby("FundID"):
        gg = g.sort_values("TradingDay_key")
        nv0 = pd.to_numeric(gg.get("NetValue"), errors="coerce")
        td = pd.to_datetime(gg.get("TradingDay_key"), errors="coerce")
        td_prev = pd.to_datetime(gg.get("td_prev"), errors="coerce")
        if nv0 is not None and nv0.notna().sum() >= 2:
            r = nv0.pct_change().replace([np.inf, -np.inf], np.nan)
            mask = (td <= end_anchor) & (td > begin_anchor) & (td_prev >= begin_anchor)
            rr = pd.to_numeric(r[mask], errors="coerce").dropna()
            if rr.size >= 1:
                nav = pd.Series(np.cumprod(1.0 + rr.to_numpy(dtype=float)))
                dd = nav / nav.cummax() - 1.0
                fund_ret[fid] = float(nav.iloc[-1] - 1.0)
                fund_mdd[fid] = float(dd.min())
                continue
            nv = nv0.dropna()
            if nv.size >= 2 and float(nv.iloc[0]) != 0:
                nav = pd.Series((nv / nv.iloc[0]).to_numpy(dtype=float))
                dd = nav / nav.cummax() - 1.0
                fund_ret[fid] = float(nav.iloc[-1] - 1.0)
                fund_mdd[fid] = float(dd.min())
                continue

        y = pd.to_numeric(gg.get("y"), errors="coerce").dropna()
        if y.empty:
            fund_ret[fid] = np.nan
            fund_mdd[fid] = np.nan
            continue
        fund_ret[fid] = np.nan
        fund_mdd[fid] = np.nan

    agg = m.groupby(["race_name", "FundID", "display_name"], dropna=False, as_index=False).agg(
        weight=("w", "max"),
        contrib_est=("contrib_est", "sum"),
        bar_count=("contrib_est", lambda s: int((s != 0).sum())),
        has_track_ratio=("w_src", lambda s: int((pd.Series(s).astype(str) == "tracks").any())),
    )
    agg["fund_return"] = agg["FundID"].map(fund_ret)
    agg["fund_mdd"] = agg["FundID"].map(fund_mdd)
    if strat_avg_ratio is not None and float(strat_avg_ratio) == float(strat_avg_ratio):
        mult = np.where(pd.to_numeric(agg["has_track_ratio"], errors="coerce").fillna(0.0) > 0, float(strat_avg_ratio), 1.0)
    else:
        mult = 1.0
    agg["contrib_wr"] = pd.to_numeric(agg["fund_return"], errors="coerce").fillna(0.0) * pd.to_numeric(agg["weight"], errors="coerce").fillna(0.0) * mult
    sum_wr = float(pd.to_numeric(agg["contrib_wr"], errors="coerce").fillna(0.0).sum())
    scale_wr = float(strat_interval_contri / sum_wr) if strat_interval_contri is not None and sum_wr != 0.0 else None
    use_wr_scaled = bool((not use_decomp) and scale_wr is not None and scale_wr > 0 and 0.05 <= abs(scale_wr) <= 5.0)
    if not use_decomp:
        agg["contrib_est"] = agg["contrib_wr"] * (float(scale_wr) if use_wr_scaled else 1.0)
    agg = agg.sort_values("contrib_est").reset_index(drop=True)

    tables = {}
    race_list = selected_races["race_name"].tolist() if isinstance(selected_races, pd.DataFrame) and (not selected_races.empty) else []
    for rn in race_list:
        g = agg[agg["race_name"] == rn].copy()
        if g.empty:
            continue
        neg = g.nsmallest(TOPN, "contrib_est")
        pos = g.nlargest(TOPN, "contrib_est")
        out = pd.concat([neg, pos], ignore_index=True).drop_duplicates(subset=["FundID"]).sort_values("contrib_est")
        out["contrib_bp"] = out["contrib_est"] * 10000.0
        tables[rn] = out[["FundID", "display_name", "weight", "fund_return", "fund_mdd", "bar_count", "contrib_bp"]]

    g_unmapped = agg[agg["race_name"] == "未映射/需核对"].copy()
    if not g_unmapped.empty:
        g_unmapped = g_unmapped.assign(abs_contrib=lambda x: x["contrib_est"].abs(), abs_ret=lambda x: x["fund_return"].abs())
        g_unmapped = g_unmapped.sort_values(["abs_contrib", "abs_ret"], ascending=False).head(max(10, TOPN))
        g_unmapped["contrib_bp"] = g_unmapped["contrib_est"] * 10000.0
        tables["未映射/需核对"] = g_unmapped[["FundID", "display_name", "weight", "fund_return", "fund_mdd", "bar_count", "contrib_bp"]]

    method = "bar.Yield(差分/求和)比例缩放到策略贡献" if use_decomp else "w×r 估算（必要时比例缩放）"
    scale_txt = "-"
    if use_decomp and scale_decomp is not None:
        scale_txt = _fmt_float(scale_decomp, 4)
    elif (not use_decomp) and scale_wr is not None:
        scale_txt = _fmt_float(scale_wr, 4) if use_wr_scaled else "-"

    summary = (
        f"子基金层采用 FundID 做赛道映射；贡献口径：{method}（scale={scale_txt}）。"
        f"本次映射覆盖率（tracks）：记录比例 {_safe_str(cov_track_rows)}，按|收益|加权覆盖 {_safe_str(cov_track_abs)}；"
        f"映射覆盖率（tracks+subfunds 兜底）：记录比例 {_safe_str(cov_race_rows)}，按|收益|加权覆盖 {_safe_str(cov_race_abs)}。"
        f"周频窗口边界：{begin_anchor.date()}~{end_anchor.date()}；贡献累加从首期后一周开始（避免把窗口外周收益计入）。"
        "区间收益/回撤优先基于 pm_holding_yield_decomposition.bar.NetValue（周频净值）计算；NetValue 缺失时不从 Yield 反推收益。"
    )
    return tables, summary


def _weighted_avg_exposure(exp2: pd.DataFrame) -> tuple[dict, dict]:
    if exp2.empty:
        return {}, {}
    if "fund_short_name" in exp2.columns:
        mask = exp2["fund_short_name"].astype(str).str.contains("加权平均", regex=False, na=False)
        if mask.any():
            avg_row = exp2[mask].iloc[0]
            avg = {}
            cov = {}
            wsum = float(pd.to_numeric(exp2.loc[~mask, "Ratio"], errors="coerce").fillna(0.0).sum()) if "Ratio" in exp2.columns else np.nan
            for c in exp2.columns:
                if c in ("FundID", "fund_short_name", "Ratio"):
                    continue
                avg[c] = pd.to_numeric(avg_row.get(c), errors="coerce")
                cov[c] = float(wsum) if avg[c] == avg[c] else 0.0
            return avg, cov

    w = pd.to_numeric(exp2.get("Ratio"), errors="coerce").fillna(0.0)
    wsum = float(w.sum())
    avg = {}
    cov = {}
    for c in exp2.columns:
        if c in ("FundID", "fund_short_name", "Ratio"):
            continue
        v = pd.to_numeric(exp2.get(c), errors="coerce")
        m = v.notna() & w.notna()
        denom = float(w[m].sum())
        avg[c] = float((v[m].fillna(0.0) * w[m]).sum() / denom) if denom > 0 else np.nan
        cov[c] = (denom / wsum) if wsum > 0 else np.nan
    return avg, cov


def _factor_table(
    pm_id: int,
    begin_date: pd.Timestamp,
    begin_next_date: Optional[pd.Timestamp],
    end_date: pd.Timestamp,
    strategy_type: int,
) -> tuple[pd.DataFrame, str]:
    exp = api.pm_risk_factor_exposure(
        pm_id=pm_id, strategy_type=strategy_type, begin_date=str(begin_date.date()), end_date=str(end_date.date())
    )
    if not isinstance(exp, pd.DataFrame) or exp.empty:
        return pd.DataFrame(), "因子暴露为空。"

    exp2 = exp.copy()
    ratio_sum_now = float(pd.to_numeric(exp2.get("Ratio"), errors="coerce").fillna(0.0).sum()) if "Ratio" in exp2.columns else np.nan
    exp_day_col = "trading_day" if "trading_day" in exp2.columns else ("TradingDay" if "TradingDay" in exp2.columns else None)
    has_exposure_ts = bool(exp_day_col is not None)
    avg_now, cov_now = _weighted_avg_exposure(exp2) if not has_exposure_ts else ({}, {})

    window_days = int((end_date - begin_date).days)
    prev_end = begin_date - pd.Timedelta(days=1)
    prev_begin = prev_end - pd.Timedelta(days=max(window_days, 1))
    prev_begin = max(prev_begin, pd.Timestamp("2020-01-01"))
    exp_prev = api.pm_risk_factor_exposure(
        pm_id=pm_id, strategy_type=strategy_type, begin_date=str(prev_begin.date()), end_date=str(prev_end.date())
    )
    exp_prev2 = exp_prev.copy() if isinstance(exp_prev, pd.DataFrame) else pd.DataFrame()
    ratio_sum_prev = (
        float(pd.to_numeric(exp_prev2.get("Ratio"), errors="coerce").fillna(0.0).sum()) if (not exp_prev2.empty and "Ratio" in exp_prev2.columns) else np.nan
    )
    avg_prev, _ = _weighted_avg_exposure(exp_prev2) if (not exp_prev2.empty and (not has_exposure_ts)) else ({}, {})

    start_dt = begin_next_date if begin_next_date is not None else begin_date
    fr = api.risk_factor_returns(strategy_type=strategy_type, start_date=str(start_dt.date()), end_date=str(end_date.date()), frequency=1)
    if not isinstance(fr, pd.DataFrame) or fr.empty:
        return pd.DataFrame(), "因子收益为空。"

    fr2 = fr.copy()
    fr2["TradingDay"] = pd.to_datetime(fr2["TradingDay"], errors="coerce")
    fr2["Yield"] = pd.to_numeric(fr2["Yield"], errors="coerce")
    fr2 = fr2.dropna(subset=["TradingDay", "Yield"])

    stats = []
    for (bid, bname), g in fr2.sort_values("TradingDay").groupby(["BenchID", "BenchName"]):
        y = pd.to_numeric(g["Yield"], errors="coerce").dropna()
        if y.empty:
            continue
        nav = pd.Series(np.cumprod(1.0 + y.to_numpy(dtype=float)))
        dd = nav / nav.cummax() - 1.0
        stats.append(
            {
                "BenchID": int(bid),
                "BenchName": str(bname),
                "factor_return": float(nav.iloc[-1] - 1.0),
                "factor_vol": float(y.std(ddof=1) * np.sqrt(252.0)) if y.size > 1 else np.nan,
                "factor_mdd": float(dd.min()),
                "sum_yield": float(y.sum()),
            }
        )
    cum = pd.DataFrame(stats)
    if cum.empty:
        return pd.DataFrame(), "因子收益统计为空。"

    cum["factor_field"] = cum["BenchID"].map(BENCHID_TO_FIELD).fillna(cum["BenchName"].astype(str))
    if not has_exposure_ts:
        cum["exposure_now"] = cum["factor_field"].map(lambda k: pd.to_numeric(avg_now.get(k), errors="coerce"))
        cum["exposure_prev"] = cum["factor_field"].map(lambda k: pd.to_numeric(avg_prev.get(k), errors="coerce"))
        cum["exposure_delta"] = cum["exposure_now"] - cum["exposure_prev"]
        cum["coverage_now"] = cum["factor_field"].map(lambda k: pd.to_numeric(cov_now.get(k), errors="coerce"))
        cum["diag_contrib_bp"] = np.nan
    else:
        exp2 = exp2.copy()
        exp2[exp_day_col] = pd.to_datetime(exp2[exp_day_col], errors="coerce")
        exp2 = exp2.dropna(subset=[exp_day_col]).sort_values(exp_day_col)
        rows = []
        for td, g in exp2.groupby(exp_day_col):
            avg, cov = _weighted_avg_exposure(g)
            item = {"trading_day": pd.Timestamp(td)}
            for k, v in avg.items():
                item[str(k)] = v
            item["_ratio_sum"] = float(pd.to_numeric(g.get("Ratio"), errors="coerce").fillna(0.0).sum()) if "Ratio" in g.columns else np.nan
            rows.append(item)
        exp_ts = pd.DataFrame(rows).dropna(subset=["trading_day"]).sort_values("trading_day").reset_index(drop=True)
        exp_now = exp_ts.tail(1).iloc[0].to_dict() if not exp_ts.empty else {}
        cum["exposure_now"] = cum["factor_field"].map(lambda k: pd.to_numeric(exp_now.get(k), errors="coerce"))
        cum["exposure_prev"] = np.nan
        cum["exposure_delta"] = np.nan
        cum["coverage_now"] = float(pd.to_numeric(exp_now.get("_ratio_sum"), errors="coerce")) if exp_now else np.nan

        fr2x = fr2[["TradingDay", "BenchID", "BenchName", "Yield"]].copy()
        fr2x = fr2x.sort_values("TradingDay")
        exp_ts2 = exp_ts.rename(columns={"trading_day": "TradingDay"}).sort_values("TradingDay")
        diag_map = {}
        for (bid, bname), g in fr2x.groupby(["BenchID", "BenchName"]):
            left = g[["TradingDay"]].copy()
            asof = pd.merge_asof(left, exp_ts2, on="TradingDay", direction="backward")
            field = BENCHID_TO_FIELD.get(int(bid), str(bname))
            e = pd.to_numeric(asof.get(field), errors="coerce")
            y = pd.to_numeric(g["Yield"], errors="coerce")
            m = e.notna() & y.notna()
            diag_map[field] = float((e[m] * y[m]).sum() * 10000.0) if m.any() else np.nan
        cum["diag_contrib_bp"] = cum["factor_field"].map(lambda k: pd.to_numeric(diag_map.get(k), errors="coerce"))

    if pd.to_numeric(cum["diag_contrib_bp"], errors="coerce").notna().any():
        cum = cum.sort_values("diag_contrib_bp", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)
    else:
        cum = cum.sort_values("exposure_now", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)
    summary = (
        f"因子暴露来自 pm_risk_factor_exposure（组合加权平均，当前窗口 {begin_date.date()}~{end_date.date()}；"
        f"对比窗口 {prev_begin.date()}~{prev_end.date()}），因子收益来自 risk_factor_returns(Yield)。"
        f"暴露覆盖率（RatioSum）：本期 {_fmt_pct(ratio_sum_now, 1)}，上期 {_fmt_pct(ratio_sum_prev, 1)}。"
        + ("暴露为截面（无时序）时不计算历史贡献，仅展示最新暴露与区间因子表现。" if not has_exposure_ts else "诊断性贡献为 Σ_t(暴露_t×因子日收益_t) 的估计。")
    )
    return cum, summary


def _sum_named_row(df: pd.DataFrame, type_name: str) -> Optional[float]:
    if not isinstance(df, pd.DataFrame) or df.empty or "type_name" not in df.columns:
        return None
    d = df[df["type_name"] == type_name].copy()
    if d.empty:
        return None
    row = d.iloc[0]
    cols = [c for c in df.columns if c not in ("type_name",)]
    s = pd.to_numeric(pd.Series({c: row.get(c) for c in cols}), errors="coerce").dropna()
    return float(s.sum()) if not s.empty else None


def _pick_main_strategy(strat_df: pd.DataFrame) -> Optional[str]:
    if not isinstance(strat_df, pd.DataFrame) or strat_df.empty:
        return None
    d = strat_df.copy()
    d["interval_contri"] = pd.to_numeric(d.get("interval_contri"), errors="coerce")
    d = d.dropna(subset=["interval_contri"])
    if d.empty:
        return None
    d["abs"] = d["interval_contri"].abs()
    return str(d.sort_values("abs", ascending=False).iloc[0].get("strategy"))


def _race_top_text(track_sections: list[dict], strategy_name: str) -> tuple[str, str]:
    st_id = None
    for k, v in ST_NAME.items():
        if v == strategy_name:
            st_id = k
            break
    if st_id is None:
        return "-", "-"
    sec = None
    for s in track_sections or []:
        if s.get("st") == st_id:
            sec = s
            break
    if not sec:
        return "-", "-"
    df = sec.get("top_tbl")
    if not isinstance(df, pd.DataFrame) or df.empty or "track_contrib" not in df.columns:
        return "-", "-"
    d = df.copy()
    d["track_contrib"] = pd.to_numeric(d.get("track_contrib"), errors="coerce")
    d = d.dropna(subset=["track_contrib"])
    if d.empty:
        return "-", "-"
    pos = d[d["track_contrib"] > 0].copy()
    neg = d[d["track_contrib"] < 0].copy()
    pos_txt = _format_topn_text(pos.sort_values("track_contrib", ascending=False), name_col="race_name", value_col="track_contrib", k=2) if not pos.empty else "-"
    neg_txt = _format_topn_text(neg.sort_values("track_contrib"), name_col="race_name", value_col="track_contrib", k=2) if not neg.empty else "无显著负贡献赛道"
    return neg_txt, pos_txt


def _subfund_top_text(subfund_sections: list[dict]) -> tuple[str, str, int]:
    rows = []
    unmapped_cnt = 0
    for sec in subfund_sections or []:
        st = sec.get("st")
        st_name = ST_NAME.get(st, str(st))
        for rn, df in (sec.get("tables") or {}).items():
            if rn == "未映射/需核对":
                unmapped_cnt += len(df) if isinstance(df, pd.DataFrame) else 0
                continue
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            d = df.copy()
            d["contrib_bp"] = pd.to_numeric(d.get("contrib_bp"), errors="coerce")
            d = d.dropna(subset=["contrib_bp"])
            if d.empty:
                continue
            for _, r in d.iterrows():
                rows.append(
                    {
                        "strategy": st_name,
                        "race": rn,
                        "name": r.get("display_name"),
                        "contrib_bp": r.get("contrib_bp"),
                    }
                )
    if not rows:
        return "-", "-", unmapped_cnt
    df = pd.DataFrame(rows)
    df["contrib_bp"] = pd.to_numeric(df["contrib_bp"], errors="coerce")
    df = df.dropna(subset=["contrib_bp"])
    if df.empty:
        return "-", "-", unmapped_cnt
    pos = df[df["contrib_bp"] > 0].copy()
    neg = df[df["contrib_bp"] < 0].copy()
    helpx = pos.sort_values("contrib_bp", ascending=False).head(2) if not pos.empty else df.sort_values("contrib_bp", ascending=False).head(2)
    drag = neg.sort_values("contrib_bp").head(2) if not neg.empty else pd.DataFrame()
    drag_txt = (
        "，".join([f"{_safe_str(r['name'])}@{_safe_str(r['race'])}/{_safe_str(r['strategy'])}（{_fmt_bp(r['contrib_bp'])}）" for _, r in drag.iterrows()])
        if not drag.empty
        else "无显著负贡献子基金"
    )
    help_txt = "，".join([f"{_safe_str(r['name'])}@{_safe_str(r['race'])}/{_safe_str(r['strategy'])}（{_fmt_bp(r['contrib_bp'])}）" for _, r in helpx.iterrows()])
    return drag_txt or "-", help_txt or "-", unmapped_cnt


def _portfolio_factor_exposure(factor_sections: list[dict], strat_df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    if not isinstance(strat_df, pd.DataFrame) or strat_df.empty:
        return pd.DataFrame(), float("nan")
    wmap = {}
    d = strat_df.copy()
    d["avg_ratio"] = pd.to_numeric(d.get("avg_ratio"), errors="coerce")
    for _, r in d.iterrows():
        name = _safe_str(r.get("strategy"))
        w = r.get("avg_ratio")
        if name and w == w:
            wmap[name] = float(w)

    standard = set(BENCHID_TO_FIELD.values())
    standard |= {"if_basis", "ic_basis"}

    rows = []
    for sec in factor_sections or []:
        st = sec.get("st")
        st_name = ST_NAME.get(st, str(st))
        w = wmap.get(st_name)
        if w is None:
            continue
        df = sec.get("table")
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        t = df.copy()
        if "factor_field" not in t.columns or "exposure_now" not in t.columns:
            continue
        t["exposure_now"] = pd.to_numeric(t["exposure_now"], errors="coerce")
        t["coverage_now"] = pd.to_numeric(t.get("coverage_now"), errors="coerce")
        t = t.dropna(subset=["exposure_now"])
        if t.empty:
            continue
        t = t[t["factor_field"].astype(str).isin(standard)]
        if t.empty:
            continue
        for _, r in t.iterrows():
            rows.append(
                {
                    "factor": str(r.get("factor_field")),
                    "w": float(w),
                    "exposure": float(r.get("exposure_now")),
                    "coverage": float(r.get("coverage_now")) if r.get("coverage_now") == r.get("coverage_now") else np.nan,
                }
            )
    if not rows:
        return pd.DataFrame(), float("nan")
    x = pd.DataFrame(rows)
    x["wx"] = x["w"] * x["exposure"]
    agg = x.groupby("factor", as_index=False).agg(port_exposure=("wx", "sum"))
    agg["abs"] = agg["port_exposure"].abs()

    cov = x.copy()
    cov["wabs"] = cov["w"].abs()
    cov_num = float((cov["wabs"] * cov["coverage"].fillna(0.0)).sum())
    cov_den = float(cov["wabs"].sum())
    cov_wavg = (cov_num / cov_den) if cov_den > 0 else float("nan")
    return agg.sort_values("abs", ascending=False).drop(columns=["abs"]).reset_index(drop=True), cov_wavg


def _factor_risk_hint(factor: str, exposure: float) -> str:
    if exposure != exposure:
        return ""
    tag = "偏高" if float(exposure) > 0 else "偏低"
    val = _fmt_float(exposure, 3)
    if factor == "size":
        return f"size 暴露{tag}（{val}）：组合风格偏向大小盘一侧，风格切换时可能出现系统性顺/逆风。"
    if factor == "beta":
        return f"beta 暴露{tag}（{val}）：对市场方向的敏感度更高/更低，需关注权益波动放大时的回撤风险或牛市阶段的跟涨能力。"
    if factor == "volatility":
        return f"volatility 暴露{tag}（{val}）：对波动环境更敏感，波动率上行/下行阶段的相对表现可能分化。"
    if factor == "momentum":
        return f"momentum 暴露{tag}（{val}）：动量/反转风格更集中，若出现风格反转可能带来阶段性回撤。"
    if factor == "liquidity":
        return f"liquidity 暴露{tag}（{val}）：流动性因子敏感度更高，流动性冲击时需关注回撤与成交约束。"
    if factor == "valuation":
        return f"valuation 暴露{tag}（{val}）：估值因子敞口更显著，估值扩张/压缩阶段可能对收益造成更强解释力。"
    if factor in ("if_basis", "ic_basis"):
        return f"{factor} 暴露{tag}（{val}）：对股指期货基差/对冲成本更敏感，需关注展期成本与对冲比率漂移。"
    return f"{factor} 暴露{tag}（{val}）：该因子方向在环境变化时可能放大组合波动，建议设置暴露容忍区间并跟踪。"


def _build_exec_summary_text(
    *,
    product_name: str,
    begin_date: pd.Timestamp,
    end_date: pd.Timestamp,
    kpis: dict,
    strat_df: pd.DataFrame,
    brinson_df: pd.DataFrame,
    track_sections: list[dict],
    subfund_sections: list[dict],
    factor_sections: list[dict],
) -> str:
    interval_ret = kpis.get("interval_return")
    mdd = kpis.get("max_drawdown")
    peak = _safe_str(kpis.get("peak_date"))
    trough = _safe_str(kpis.get("trough_date"))

    neg_str = "-"
    pos_str = "-"
    has_neg_strategy = False
    residual_bp = None
    if isinstance(strat_df, pd.DataFrame) and not strat_df.empty:
        d = strat_df.copy()
        d["interval_contri"] = pd.to_numeric(d.get("interval_contri"), errors="coerce")
        d = d.dropna(subset=["interval_contri"])
        if not d.empty:
            pos = d[d["interval_contri"] > 0].copy()
            neg = d[d["interval_contri"] < 0].copy()
            has_neg_strategy = not neg.empty
            pos_str = _format_topn_text(pos.sort_values("interval_contri", ascending=False), name_col="strategy", value_col="interval_contri", k=2) if not pos.empty else "-"
            if not neg.empty:
                neg_str = _format_topn_text(neg.sort_values("interval_contri"), name_col="strategy", value_col="interval_contri", k=2)
            else:
                neg_str = "其余策略贡献缺失/接近0" if len(d) <= 2 else _format_topn_text(d.sort_values("interval_contri"), name_col="strategy", value_col="interval_contri", k=2)
            strat_sum = float(d["interval_contri"].sum())
            if interval_ret is not None:
                residual_bp = float((interval_ret - strat_sum) * 10000.0)

    alloc = _sum_named_row(brinson_df, "资产配置收益")
    sel = _sum_named_row(brinson_df, "选基收益")

    main_strategy = _pick_main_strategy(strat_df) or "-"
    race_neg, race_pos = _race_top_text(track_sections, main_strategy) if main_strategy != "-" else ("-", "-")
    drag_sf, help_sf, unmapped_cnt = _subfund_top_text(subfund_sections)

    port_exp, cov_wavg = _portfolio_factor_exposure(factor_sections, strat_df)
    exp_txt = "-"
    risk_txt = ""
    if isinstance(port_exp, pd.DataFrame) and not port_exp.empty:
        top = port_exp.head(3).copy()
        exp_txt = "，".join([f"{_safe_str(r.get('factor'))}（{_fmt_float(r.get('port_exposure'),3)}）" for _, r in top.iterrows()])
        hints = []
        for _, r in top.iterrows():
            hint = _factor_risk_hint(str(r.get("factor")), float(r.get("port_exposure")))
            if hint:
                hints.append(hint)
        risk_txt = " ".join(hints[:2])

    s = []
    base_txt = _safe_str(kpis.get("begin_used"))
    s.append(
        f"{product_name}在 {begin_date.date()}~{end_date.date()} 区间收益{_fmt_pct(interval_ret)}、最大回撤{_fmt_pct(mdd)}（峰-谷 {peak}→{trough}），回撤窗口可作为重点复盘时段。"
        + (f"本报告净值起点取起始日前一交易日（基准日：{base_txt}）。" if base_txt else "")
    )
    if has_neg_strategy:
        s.append(f"策略层贡献显示：主要拖累来自{neg_str}，主要贡献来自{pos_str}" + (f"，Residual约{_fmt_bp(residual_bp)}" if residual_bp is not None else "") + "。")
    else:
        s.append(f"策略层贡献显示：本期各策略贡献未出现显著为负项，贡献靠前为{pos_str}，贡献相对靠后为{neg_str}" + (f"，Residual约{_fmt_bp(residual_bp)}" if residual_bp is not None else "") + "。")
    if alloc is not None or sel is not None:
        s.append(f"Brinson 视角下，资产配置贡献{_fmt_bp_from_return(alloc)}、选基贡献{_fmt_bp_from_return(sel)}，用于判断“结构”与“选基”孰主导。")
    s.append(f"细分赛道层聚焦在{main_strategy}：{('拖累Top为'+race_neg+'，') if '无显著负贡献' not in race_neg else ''}贡献Top为{race_pos}。")
    s.append(f"子基金层：拖累Top为{drag_sf}；贡献Top为{help_sf}。" + (f"另有未映射条目{unmapped_cnt}条需核对。" if unmapped_cnt else ""))
    s.append(
        f"因子暴露（组合口径加权汇总）Top为：{exp_txt}"
        + (f"（覆盖权重加权均值约{_fmt_pct(cov_wavg,1)}）" if cov_wavg == cov_wavg else "")
        + ("。" if exp_txt else "")
        + (f"风险提示：{risk_txt}" if risk_txt else "")
    )
    return " ".join([x for x in s if x])


def _build_exec_summary_html(**kwargs) -> str:
    return f"<p>{html.escape(_build_exec_summary_text(**kwargs))}</p>"


def _brinson_tables(pm_id: int, begin_date: pd.Timestamp, end_date: pd.Timestamp) -> tuple[pd.DataFrame, str]:
    frames = []
    desc = {2: "资产配置收益", 3: "选基收益", 4: "总超额"}
    for t in [2, 3, 4]:
        try:
            df = api.pm_brinson_attribution(
                pm_id=pm_id,
                begin_date=str(begin_date.date()),
                end_date=str(end_date.date()),
                brinson_type=t,
            )
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            d = df.copy()
            if "trading_day" in d.columns:
                d["trading_day"] = pd.to_datetime(d["trading_day"], errors="coerce")
                d = d[(d["trading_day"] >= begin_date) & (d["trading_day"] <= end_date)].sort_values("trading_day")
            cols = [c for c in d.columns if c != "trading_day" and isinstance(c, str)]
            row = {"brinson_type": t, "type_name": desc.get(t, str(t))}
            for c in cols:
                row[c] = _interval_sum_or_diff(d[c])
            frames.append(row)
        except Exception:
            continue
    out = pd.DataFrame(frames)
    if out.empty:
        return out, "Brinson 归因接口返回为空或不可用。"
    main_cols = [c for c in ["股票多头", "CTA", "市场中性", "债券", "ETF"] if c in out.columns]
    show = out[["type_name", *main_cols]].copy() if main_cols else out.copy()
    txt = "Brinson 归因用于区分“资产配置”与“选基”对超额的贡献；数值口径以接口为准，区间贡献按序列求和或首末差计算。"
    return show, txt


def _pnl_by_period(pm_id: int, begin_date: pd.Timestamp, end_date: pd.Timestamp, freq: str = "W") -> tuple[pd.DataFrame, str]:
    try:
        df = api.pm_strategy_pnl_by_period(
            pm_id=pm_id,
            freq=freq,
            begin_date=str(begin_date.date()),
            end_date=str(end_date.date()),
        )
    except Exception as e:
        return pd.DataFrame(), f"分段盈亏取数失败：{e}"
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(), "分段盈亏为空或不可用。"
    d = df.copy()
    d["trading_day"] = pd.to_datetime(d["trading_day"], errors="coerce")
    d = d.dropna(subset=["trading_day"]).sort_values("trading_day")

    rows = []
    for _, r in d.iterrows():
        payload = r.get("data")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = None
        if not isinstance(payload, dict):
            continue
        td = pd.Timestamp(r["trading_day"]).date()
        item = {"trading_day": str(td)}
        for k, v in payload.items():
            item[str(k)] = pd.to_numeric(v, errors="coerce")
        rows.append(item)
    out = pd.DataFrame(rows)
    if out.empty:
        return out, "分段盈亏解析为空。"
    if "总盈亏" in out.columns:
        out = out.sort_values("总盈亏")
    summary = "分段盈亏用于定位“拖累发生在哪些周/月”。单位为接口原始口径（通常为金额增量），建议结合当期净资产/保证金占用做归一化解释。"
    return out.reset_index(drop=True), summary


def _build_text_report(
    *,
    product_name: str,
    pm_id: int,
    begin_date: pd.Timestamp,
    end_date: pd.Timestamp,
    kpis: dict,
    strat_df: pd.DataFrame,
    brinson_df: pd.DataFrame,
    brinson_summary: str,
    pnl_df: pd.DataFrame,
    pnl_summary: str,
    track_sections: list[dict],
    subfund_sections: list[dict],
    factor_sections: list[dict],
) -> str:
    lines = []
    lines.append(f"产品：{product_name}（PMID={pm_id}）")
    lines.append(
        f"区间：{begin_date.date()} ~ {end_date.date()}（起点净值基准日：{_safe_str(kpis.get('begin_used'))}；净值有效交易日：{_safe_str(kpis.get('begin_used'))} ~ {_safe_str(kpis.get('end_used'))}）"
    )
    lines.append(f"区间收益：{_fmt_pct(kpis.get('interval_return'))}；最大回撤：{_fmt_pct(kpis.get('max_drawdown'))}（峰-谷 {_safe_str(kpis.get('peak_date'))}→{_safe_str(kpis.get('trough_date'))}）")
    lines.append("")

    lines.append("策略层（大类赛道）")
    if isinstance(strat_df, pd.DataFrame) and not strat_df.empty:
        for _, r in strat_df.iterrows():
            lines.append(
                f"- {r.get('strategy')}：平均权重{_fmt_pct(r.get('avg_ratio'))}；区间收益{_fmt_pct(r.get('interval_yield'))}；区间贡献{_fmt_bp_from_return(r.get('interval_contri'))}"
            )
        strat_sum = float(pd.to_numeric(strat_df.get("interval_contri"), errors="coerce").fillna(0.0).sum())
        residual = (kpis.get("interval_return") - strat_sum) if kpis.get("interval_return") is not None else None
        lines.append(f"一致性：Σ策略贡献{_fmt_bp_from_return(strat_sum)}；组合区间收益{_fmt_bp_from_return(kpis.get('interval_return'))}；Residual{_fmt_bp_from_return(residual)}")
    else:
        lines.append("- 策略层数据为空")
    lines.append("")

    lines.append("Brinson（资产配置 vs 选基）")
    lines.append(brinson_summary or "-")
    if isinstance(brinson_df, pd.DataFrame) and not brinson_df.empty:
        cols = [c for c in brinson_df.columns if c != "type_name"]
        for _, r in brinson_df.iterrows():
            seg = [f"{_safe_str(r.get('type_name'))}"]
            for c in cols:
                seg.append(f"{c}:{_fmt_bp_from_return(r.get(c))}")
            lines.append("- " + "；".join(seg))
    else:
        lines.append("- Brinson 数据为空")
    lines.append("")

    lines.append("分段损益（按周）")
    lines.append(pnl_summary or "-")
    if isinstance(pnl_df, pd.DataFrame) and not pnl_df.empty:
        show_cols = [c for c in ["trading_day", "总盈亏", "股票多头", "市场中性", "CTA", "债券", "ETF"] if c in pnl_df.columns]
        show = pnl_df[show_cols].head(12)
        for _, r in show.iterrows():
            parts = []
            for c in show_cols:
                if c == "trading_day":
                    parts.append(str(r.get(c)))
                else:
                    parts.append(f"{c}:{_fmt_float(r.get(c), 2)}")
            lines.append("- " + "；".join(parts))
    else:
        lines.append("- 分段损益数据为空")
    lines.append("")

    lines.append("赛道层（细分赛道）")
    for sec in track_sections or []:
        st = sec.get("st")
        lines.append(f"- {ST_NAME.get(st, str(st))}（strategy_type={st}）：{_safe_str(sec.get('summary'))}")
    lines.append("")

    lines.append("子基金层（下钻关键赛道）")
    for sec in subfund_sections or []:
        st = sec.get("st")
        lines.append(f"- {ST_NAME.get(st, str(st))}（strategy_type={st}）：{_safe_str(sec.get('summary'))}")
        if sec.get("error"):
            lines.append(f"  无法输出：{_safe_str(sec.get('error'))}")
            continue
        for rn, df in (sec.get("tables") or {}).items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            d = df.copy()
            d["contrib_bp"] = pd.to_numeric(d.get("contrib_bp"), errors="coerce")
            neg = d.nsmallest(3, "contrib_bp")
            pos = d.nlargest(3, "contrib_bp")
            lines.append(f"  赛道：{rn}；拖累Top：{_format_topn_text(neg, name_col='display_name', value_col='contrib_bp', k=3, value_fmt=_fmt_bp)}；贡献Top：{_format_topn_text(pos, name_col='display_name', value_col='contrib_bp', k=3, value_fmt=_fmt_bp)}")
    lines.append("")

    lines.append("因子（暴露与因子收益表现）")
    for sec in factor_sections or []:
        st = sec.get("st")
        df = sec.get("table")
        lines.append(f"- {ST_NAME.get(st, str(st))}（strategy_type={st}）：{_safe_str(sec.get('summary'))}")
        if not isinstance(df, pd.DataFrame) or df.empty:
            lines.append(f"  数据为空：{_safe_str(sec.get('error'))}")
            continue
        has_diag = pd.to_numeric(df.get("diag_contrib_bp"), errors="coerce").notna().any() if "diag_contrib_bp" in df.columns else False
        top = df.head(5).copy()
        if has_diag:
            lines.append(f"  Top风险（|诊断性贡献|）：{_format_topn_text(top, name_col='factor_field', value_col='diag_contrib_bp', k=5, value_fmt=_fmt_bp)}")
        else:
            lines.append(
                "  Top暴露（|暴露|）：" + _format_topn_text(top, name_col="factor_field", value_col="exposure_now", k=5, value_fmt=lambda x: _fmt_float(x, 3))
            )
    lines.append("")
    lines.append("总结陈述")
    lines.append(
        _build_exec_summary_text(
            product_name=product_name,
            begin_date=begin_date,
            end_date=end_date,
            kpis=kpis,
            strat_df=strat_df,
            brinson_df=brinson_df,
            track_sections=track_sections,
            subfund_sections=subfund_sections,
            factor_sections=factor_sections,
        )
    )
    return "\n".join(lines)


def main() -> None:
    global PM_ID, BEGIN_DATE, OUTPUT_HTML_PATH, TOPN
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-name", type=str, default=None)
    parser.add_argument("--pm-id", type=int, default=int(PM_ID))
    parser.add_argument("--begin-date", type=str, default=str(BEGIN_DATE.date()))
    parser.add_argument("--end-date", type=str, default=None)
    parser.add_argument("--topn", type=int, default=int(TOPN))
    parser.add_argument("--output-format", type=str, default="html", choices=["html", "text", "both"])
    parser.add_argument("--output-html", type=str, default=str(OUTPUT_HTML_PATH))
    args = parser.parse_args()

    _ensure_pm_key()

    if args.product_name:
        resolved, matched = _resolve_pm_id_by_name(str(args.product_name))
        PM_ID = int(resolved)
    else:
        PM_ID = int(args.pm_id)

    BEGIN_DATE = pd.Timestamp(pd.to_datetime(args.begin_date, errors="coerce"))
    OUTPUT_HTML_PATH = str(args.output_html)
    TOPN = int(args.topn)
    end_date = pd.Timestamp(pd.to_datetime(args.end_date, errors="coerce")) if args.end_date else _get_end_date(PM_ID, BEGIN_DATE)
    base = api.pm_base_info(pm_id=PM_ID)
    product_name = str(base.iloc[0]["fund_short_name"]) if isinstance(base, pd.DataFrame) and (not base.empty) and "fund_short_name" in base.columns else "母基金"

    nav_df, kpis = _nav_kpis(PM_ID, BEGIN_DATE, end_date)
    begin_used = pd.to_datetime(kpis.get("begin_used"), errors="coerce")
    begin_used = pd.Timestamp(begin_used) if not pd.isna(begin_used) else BEGIN_DATE
    begin_next_used = pd.to_datetime(kpis.get("begin_next_used"), errors="coerce")
    begin_next_used = pd.Timestamp(begin_next_used) if not pd.isna(begin_next_used) else None
    end_used = pd.to_datetime(kpis.get("end_used"), errors="coerce")
    end_used = pd.Timestamp(end_used) if not pd.isna(end_used) else end_date

    strat_df = _strategy_layer(PM_ID, begin_used, end_used)
    brinson_df, brinson_summary = _brinson_tables(PM_ID, begin_used, end_used)
    pnl_df, pnl_summary = _pnl_by_period(PM_ID, begin_used, end_used, freq="W")

    strategy_types = [1, 3, 5, 4]
    track_sections = []
    subfund_sections = []
    factor_sections = []

    for st in strategy_types:
        try:
            contrib = _track_layer(PM_ID, st, begin_used, end_used)
            if contrib.empty:
                top_tbl = pd.DataFrame(columns=["race_name", "avg_ratio", "track_return", "track_contrib"])
                selected = pd.DataFrame(columns=["race_name", "track_contrib", "reason"])
                summary = "赛道贡献为空或不可用。"
            else:
                pos_pool = contrib[pd.to_numeric(contrib["track_contrib"], errors="coerce") > 0].copy()
                neg_pool = contrib[pd.to_numeric(contrib["track_contrib"], errors="coerce") < 0].copy()
                top = pos_pool.nlargest(6, "track_contrib") if not pos_pool.empty else contrib.nlargest(6, "track_contrib")
                bot = neg_pool.nsmallest(6, "track_contrib") if not neg_pool.empty else pd.DataFrame(columns=contrib.columns)
                top_tbl = (
                    pd.concat([bot, top], ignore_index=True)
                    .drop_duplicates(subset=["race_name"])
                    .sort_values("track_contrib")
                    .reset_index(drop=True)
                )
                selected = _select_drilldown(contrib)
                summary = (
                    f"拖累端（最负）Top：{(_format_topn_text(bot, name_col='race_name', value_col='track_contrib', k=3) if not bot.empty else '无显著负贡献赛道')}；"
                    f"贡献端（最正）Top：{_format_topn_text(top, name_col='race_name', value_col='track_contrib', k=3)}。"
                    "下钻赛道选择规则：优先 |贡献|≥20bp，否则取 Top2/Bottom2。"
                )
            track_sections.append({"st": st, "top_tbl": top_tbl, "selected": selected, "summary": summary})
        except Exception as e:
            track_sections.append({"st": st, "top_tbl": pd.DataFrame(), "selected": pd.DataFrame(), "summary": f"赛道层取数失败：{e}"})
            selected = pd.DataFrame(columns=["race_name", "track_contrib", "reason"])

        try:
            tables, ssum = _subfund_topn(PM_ID, begin_used, end_used, st, selected)
            subfund_sections.append({"st": st, "tables": tables, "summary": ssum, "error": None if tables else "无可用下钻表"})
        except Exception as e:
            subfund_sections.append({"st": st, "tables": {}, "summary": "子基金层取数失败。", "error": _shorten_text(e, 420)})

        try:
            fdf, fsum = _factor_table(PM_ID, begin_used, begin_next_used, end_used, st)
            factor_sections.append({"st": st, "table": fdf, "summary": fsum, "error": None if not fdf.empty else "因子表为空"})
        except Exception as e:
            factor_sections.append({"st": st, "table": pd.DataFrame(), "summary": "因子模块取数失败。", "error": str(e)})

    style = """
    :root{--fg:#111827;--muted:#6b7280;--border:#e5e7eb;--bg:#ffffff;--bg2:#f9fafb;--warn:#b91c1c;}
    body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans","Liberation Sans","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;}
    .container{max-width:1100px;margin:24px auto;padding:0 16px 40px;}
    h1{font-size:22px;margin:0 0 8px;}
    h2{font-size:16px;margin:18px 0 8px;padding-top:6px;border-top:1px solid var(--border);}
    h3{font-size:14px;margin:14px 0 8px;}
    h4{font-size:13px;margin:12px 0 8px;}
    .meta{color:var(--muted);margin:0 0 14px;}
    .note{background:var(--bg2);border:1px solid var(--border);padding:10px 12px;border-radius:8px;color:var(--muted);margin:10px 0 14px;}
    .note strong{color:var(--fg);}
    .section-lead{color:var(--muted);margin:0 0 6px;}
    .small{font-size:12px;color:var(--muted);}
    .warn{color:var(--warn);font-weight:700;}
    .kpi{display:grid;grid-template-columns:repeat(4,minmax(180px,1fr));gap:10px;margin:10px 0 6px;}
    .card{border:1px solid var(--border);border-radius:10px;padding:10px 12px;background:#fff;}
    .card .label{color:var(--muted);font-size:12px;}
    .card .value{font-size:18px;font-weight:700;margin-top:2px;}
    .card .sub{color:var(--muted);font-size:12px;margin-top:2px;}
    .badge{display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid var(--border);background:var(--bg2);color:var(--muted);font-size:12px;margin-left:6px;}
    .hr{height:1px;background:var(--border);margin:18px 0;}
    table{width:100%;border-collapse:collapse;margin:8px 0 10px;background:#fff;}
    th,td{border:1px solid var(--border);padding:8px 10px;vertical-align:top;word-break:break-word;}
    th{background:var(--bg2);text-align:left;font-weight:600;}
    @media (max-width:900px){.kpi{grid-template-columns:1fr 1fr;}}
    @media (max-width:520px){.kpi{grid-template-columns:1fr;}}
    """

    title = f"{product_name}：{str(BEGIN_DATE.date())}以来表现分析"
    parts = []
    parts.append("<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'/>")
    parts.append("<meta name='viewport' content='width=device-width,initial-scale=1'/>")
    parts.append(f"<title>{html.escape(title)}</title>")
    parts.append(f"<style>{style}</style></head><body><div class='container'>")
    parts.append(f"<h1>{html.escape(title)}</h1>")
    parts.append(
        f"<p class='meta'>产品：{html.escape(product_name)}（PMID={PM_ID}）｜区间：{BEGIN_DATE.date()} ~ {end_date.date()}（起点净值基准日：{html.escape(_safe_str(kpis.get('begin_used')))}；净值有效交易日：{html.escape(_safe_str(kpis.get('begin_used')))} ~ {html.escape(_safe_str(kpis.get('end_used')))}）<span class='badge'>数据源：ZMData 投后/因子接口</span></p>"
    )

    parts.append("<div class='note'><strong>口径说明：</strong><ul>")
    parts.append("<li>区间收益/最大回撤：基于 <code>pm_nav</code> 的单位净值切片计算。</li>")
    parts.append("<li>策略层/赛道层：优先使用系统字段汇总；子基金层用 <code>FundID</code> 对齐，并以 <code>pm_holding_yield_decomposition.bar.Yield</code> 作为策略内分解权重，按比例缩放到策略层区间贡献口径。</li>")
    parts.append("<li>因子贡献为 <strong>诊断性估计</strong>（暴露×因子收益序列），用于风险来源定位，<span class='warn'>不得表述为严格业绩归因</span>。</li>")
    parts.append("</ul></div>")

    parts.append("<h2>分析结论</h2>")
    strat_top_neg = "-"
    strat_top_pos = "-"
    if isinstance(strat_df, pd.DataFrame) and (not strat_df.empty) and "interval_contri" in strat_df.columns:
        tmp = strat_df.copy()
        tmp["interval_contri"] = pd.to_numeric(tmp["interval_contri"], errors="coerce")
        strat_top_neg = _format_topn_text(tmp.nsmallest(2, "interval_contri"), name_col="strategy", value_col="interval_contri", k=2)
        strat_top_pos = _format_topn_text(tmp.nlargest(2, "interval_contri"), name_col="strategy", value_col="interval_contri", k=2)
    parts.append(
        f"<p class='section-lead'>截至 {end_date.date()}，组合自 {BEGIN_DATE.date()} 以来区间收益 {_fmt_pct(kpis['interval_return'])}，最大回撤 {_fmt_pct(kpis['max_drawdown'])}（峰-谷 {_safe_str(kpis.get('peak_date'))}→{_safe_str(kpis.get('trough_date'))}）。"
        f"策略层视角下，主要拖累来自：{html.escape(strat_top_neg)}；主要贡献来自：{html.escape(strat_top_pos)}。"
        "后续章节将按“三层结构”把结果拆到策略→赛道→子基金，并用因子暴露/因子收益解释顺逆风。</p>"
    )
    parts.append("<div class='kpi'>")
    parts.append(f"<div class='card'><div class='label'>区间收益</div><div class='value'>{_fmt_pct(kpis['interval_return'])}</div><div class='sub'>单位净值切片</div></div>")
    parts.append(f"<div class='card'><div class='label'>最大回撤</div><div class='value'>{_fmt_pct(kpis['max_drawdown'])}</div><div class='sub'>峰-谷：{_safe_str(kpis.get('peak_date'))} → {_safe_str(kpis.get('trough_date'))}</div></div>")
    parts.append(f"<div class='card'><div class='label'>年化收益（估算）</div><div class='value'>{_fmt_pct(kpis['annual_return'])}</div><div class='sub'>按交易日折算</div></div>")
    parts.append(f"<div class='card'><div class='label'>年化波动 / Sharpe（估算）</div><div class='value'>{_fmt_pct(kpis['annual_vol'])} / {_fmt_float(kpis['sharpe'],2)}</div><div class='sub'>rf=0 近似</div></div>")
    parts.append("</div>")
    parts.append("<p>本节文字总结：区间收益刻画最终结果，最大回撤刻画最差体验。若回撤峰-谷较集中，后续应优先对照该时间段的赛道/子基金负贡献来源，并检查风格因子与对冲成本是否与环境方向相悖。</p>")

    parts.append("<h2>大类赛道归因（策略层）</h2>")
    parts.append("<p class='section-lead'>口径：<code>pm_strategy_nav(freq='D')</code>；区间收益采用收益序列连乘，区间贡献采用贡献序列求和，并与母基金区间净值保持同一“有效交易日窗口”。Residual 用于提示口径差，不把残差强行归因到单一策略。</p>")
    if strat_df.empty:
        parts.append("<p>策略层接口返回为空，无法输出策略层归因表。</p>")
    else:
        rows = [[r['strategy'], _fmt_pct(r['avg_ratio']), _fmt_pct(r['interval_yield']), _fmt_bp_from_return(r['interval_contri'])] for _, r in strat_df.iterrows()]
        parts.append(_render_table(["大类赛道", "平均权重", "区间收益", "区间贡献"], rows))
        strat_sum = float(pd.to_numeric(strat_df["interval_contri"], errors="coerce").fillna(0.0).sum())
        residual = (kpis["interval_return"] - strat_sum) if kpis["interval_return"] is not None else None
        parts.append(f"<p class='small'>一致性校验：Σ策略贡献 {_fmt_bp_from_return(strat_sum)} vs 组合区间收益 {_fmt_bp_from_return(kpis['interval_return'])}，Residual {_fmt_bp_from_return(residual)}。</p>")
        warn = ""
        if residual is not None and abs(residual) * 10000.0 > 50.0:
            warn = " Residual 超过 50bp，需谨慎解读归因结果并优先解释口径差来源。"
        parts.append(
            f"<p>本节文字总结：策略层用于快速判断组合风险预算的主要来源。主要拖累：{html.escape(strat_top_neg)}；主要贡献：{html.escape(strat_top_pos)}。"
            f"Residual 用于提示口径差（现金/费用/衍生品保证金/净值边界等），不建议把残差强行归因到某一策略。{html.escape(warn)}</p>"
        )

    parts.append("<h2>Brinson 归因（资产配置 vs 选基）</h2>")
    parts.append(f"<p class='section-lead'>{html.escape(brinson_summary)}</p>")
    if isinstance(brinson_df, pd.DataFrame) and (not brinson_df.empty):
        headers = ["归因类型"] + [c for c in brinson_df.columns if c != "type_name"]
        rows = []
        for _, r in brinson_df.iterrows():
            row = [r.get("type_name")]
            for c in headers[1:]:
                row.append(_fmt_bp_from_return(r.get(c)))
            rows.append(row)
        parts.append(_render_table(headers, rows))
        parts.append(
            "<p>本节文字总结：Brinson 归因把“超额来源”拆成资产配置与选基两部分。若资产配置收益为主要拖累，通常意味着策略权重结构与环境不匹配；若选基收益为主要拖累，则应优先在关键赛道内定位具体子基金与风格漂移，并结合投后限额/替换动作处理。</p>"
        )
    else:
        parts.append("<p>本次区间未能取到可用的 Brinson 归因结果（接口为空或该产品未维护）。</p>")

    parts.append("<h2>分段损益归因（按周）</h2>")
    parts.append(f"<p class='section-lead'>{html.escape(pnl_summary)}</p>")
    if isinstance(pnl_df, pd.DataFrame) and (not pnl_df.empty):
        show_cols = [c for c in ["trading_day", "总盈亏", "股票多头", "市场中性", "CTA", "债券", "ETF"] if c in pnl_df.columns]
        show = pnl_df[show_cols].copy()
        show = show.head(12)
        headers = [("周期结束日" if c == "trading_day" else c) for c in show.columns]
        rows = []
        for _, r in show.iterrows():
            rr = []
            for c in show.columns:
                if c == "trading_day":
                    rr.append(r[c])
                else:
                    rr.append(_fmt_float(r[c], 2))
            rows.append(rr)
        parts.append(_render_table(headers, rows))
        parts.append(
            "<p>本节文字总结：分段损益用于回答“回撤/反弹集中发生在哪些周”。建议重点关注总盈亏最差的几周：对照当周主拖累策略与赛道，并与净值峰-谷窗口交叉验证；若 CTA/中性在关键周未能对冲，需进一步检查对冲比率、基差/展期成本与风格暴露方向。</p>"
        )
    else:
        parts.append("<p>该区间未能取到可用的分段损益数据。</p>")

    parts.append("<h2>细分赛道归因（Race 层）</h2>")
    parts.append("<p class='section-lead'>本节按策略类型分别输出赛道贡献 Top/Bottom，并给出下钻赛道清单（触发原因：|贡献|≥20bp 或 top2/bottom2）。赛道层定位结构性拖累/对冲，下一节将把赛道拆到具体子基金。</p>")
    for sec in track_sections:
        st = sec["st"]
        parts.append(f"<h3>{html.escape(ST_NAME.get(st, str(st)))}（strategy_type={st}）</h3>")
        parts.append(f"<p>{html.escape(sec['summary'])}</p>")
        df = sec["top_tbl"]
        if isinstance(df, pd.DataFrame) and (not df.empty):
            rows = []
            for _, r in df.iterrows():
                rows.append([r["race_name"], _fmt_pct(r.get("avg_ratio")), _fmt_pct(r.get("track_return")), _fmt_bp_from_return(r.get("track_contrib"))])
            parts.append(_render_table(["细分赛道", "平均权重", "区间收益", "赛道贡献"], rows))
            dfx = df.copy()
            dfx["track_contrib"] = pd.to_numeric(dfx["track_contrib"], errors="coerce")
            neg = dfx.nsmallest(3, "track_contrib")
            pos = dfx.nlargest(3, "track_contrib")
            parts.append(
                f"<p>本段文字总结：{html.escape(ST_NAME.get(st, str(st)))} 内部赛道贡献分化明显时，应优先定位最负贡献赛道并解释其收益与权重的组合效应。"
                f"该策略的主要拖累赛道：{html.escape(_format_topn_text(neg, name_col='race_name', value_col='track_contrib', k=3))}；"
                f"主要贡献赛道：{html.escape(_format_topn_text(pos, name_col='race_name', value_col='track_contrib', k=3))}。</p>"
            )
        else:
            parts.append("<p>该策略赛道贡献表为空或不可用。</p>")
        sel = sec["selected"]
        if isinstance(sel, pd.DataFrame) and (not sel.empty):
            rows = [[r["race_name"], r["reason"], _fmt_bp_from_return(r["track_contrib"])] for _, r in sel.iterrows()]
            parts.append("<p>下钻赛道清单（含触发原因）：</p>")
            parts.append(_render_table(["下钻赛道", "触发原因", "赛道贡献"], rows))
    parts.append("<p>本节文字总结：赛道层可解释为何策略总体贡献为正/负。例如 CTA 若出现期货主观显著为负而趋势/跨境套利为正，通常意味着风格分化或单一方向暴露过高；股票多头若由 1000/300 指增贡献驱动，应结合 size/beta/volatility 等因子判断环境顺逆风。</p>")

    parts.append("<h2>子基金归因（子基金层，下钻关键赛道）</h2>")
    parts.append("<p class='section-lead'>本节输出关键赛道下钻子基金 TopN（展示基金简称，保留 FundID 以便核验）。为避免基金全称/简称不一致导致无法聚合，使用 FundID 做主键映射到赛道。子基金贡献以 <code>bar.Yield</code> 作为策略内分解权重，并按比例缩放到策略层区间贡献口径后累加排序。</p>")
    for sec in subfund_sections:
        st = sec["st"]
        parts.append(f"<h3>{html.escape(ST_NAME.get(st, str(st)))}（strategy_type={st}）</h3>")
        parts.append(f"<p>{html.escape(sec['summary'])}</p>")
        if sec.get("error"):
            parts.append(f"<p>无法输出该策略子基金 TopN：{html.escape(_safe_str(sec['error']))}</p>")
            continue
        for rn, df in (sec["tables"] or {}).items():
            parts.append(f"<h4>赛道：{html.escape(rn)}（Top{TOPN}/Bottom{TOPN}）</h4>")
            parts.append("<p>表内‘子基金贡献’以 <code>pm_holding_yield_decomposition.bar.Yield</code> 作为策略内分解权重，并按比例缩放到策略层区间贡献口径后在区间内累加；区间收益/最大回撤来自 bar.NetValue（周频净值）按窗口边界计算。权重列优先取 tracks.ratio（若缺失则用 pm_subfunds.weight 兜底），用于识别“贡献集中度”。</p>")
            rows = []
            df2 = df.copy()
            df2["contrib_bp"] = pd.to_numeric(df2.get("contrib_bp"), errors="coerce")
            drag = df2.nsmallest(3, "contrib_bp")
            helpx = df2.nlargest(3, "contrib_bp")
            parts.append(
                f"<p>本段文字总结：在“{html.escape(rn)}”赛道内，主要拖累子基金：{html.escape(_format_topn_text(drag, name_col='display_name', value_col='contrib_bp', k=3, value_fmt=_fmt_bp))}；"
                f"主要贡献子基金：{html.escape(_format_topn_text(helpx, name_col='display_name', value_col='contrib_bp', k=3, value_fmt=_fmt_bp))}。"
                "若拖累集中于少数高权重基金，需优先复核其风格漂移/风险预算/止损机制；若贡献集中，需评估可持续性与相关性。</p>"
            )
            for _, r in df.iterrows():
                rows.append(
                    [
                        int(r["FundID"]) if r["FundID"] == r["FundID"] else "-",
                        r["display_name"],
                        _fmt_pct(r.get("weight")),
                        _fmt_pct(r.get("fund_return")),
                        _fmt_pct(r.get("fund_mdd")),
                        _safe_str(r.get("bar_count")),
                        _fmt_bp(r.get("contrib_bp"), 1),
                    ]
                )
            parts.append(_render_table(["FundID", "基金简称", "权重(近似)", "区间收益(2/1以来)", "最大回撤(周)", "周数", "子基金贡献(bp)"], rows))
    parts.append("<p>本节文字总结：子基金层把赛道贡献拆到具体基金，支持投后动作（复核/替换/限额）。需要注意本节贡献为估算口径，若要做严格归因应以系统贡献字段或更细颗粒权重序列为准，并对残差进行解释。</p>")

    parts.append("<h2>因子风险暴露与因子收益表现（核心）</h2>")
    parts.append("<p class='section-lead'>本节将 pm_risk_factor_exposure 的组合暴露与 risk_factor_returns 的因子收益并列，给出诊断性贡献（Σ 暴露×因子日收益）。该诊断用于解释顺逆风与风险来源，不作为严格归因。</p>")
    for sec in factor_sections:
        st = sec["st"]
        parts.append(f"<h3>{html.escape(ST_NAME.get(st, str(st)))}（strategy_type={st}）</h3>")
        parts.append(f"<p>{html.escape(sec['summary'])}</p>")
        df = sec["table"]
        if not isinstance(df, pd.DataFrame) or df.empty:
            parts.append(f"<p>该策略因子表为空或不可用：{html.escape(_safe_str(sec.get('error')))}</p>")
            continue
        show = df.head(12).copy()
        rows = []
        for _, r in show.iterrows():
            rows.append(
                [
                    r["factor_field"],
                    _fmt_float(r.get("exposure_now"), 3),
                    _fmt_float(r.get("exposure_prev"), 3),
                    _fmt_float(r.get("exposure_delta"), 3),
                    _fmt_pct(r.get("factor_return"), 2),
                    _fmt_pct(r.get("factor_mdd"), 2),
                    _fmt_bp(r.get("diag_contrib_bp"), 1),
                    _fmt_pct(r.get("coverage_now"), 1),
                ]
            )
        parts.append(_render_table(["因子", "暴露(本期)", "暴露(上期)", "Δ暴露", "因子累计收益", "因子最大回撤", "诊断性贡献(bp)", "暴露覆盖率"], rows))
        has_diag = pd.to_numeric(df.get("diag_contrib_bp"), errors="coerce").notna().any() if "diag_contrib_bp" in df.columns else False
        top_risk = df.head(5).copy()
        if has_diag:
            lead = f"该策略本期主要风险来源（按|诊断性贡献|排序）为：{html.escape(_format_topn_text(top_risk, name_col='factor_field', value_col='diag_contrib_bp', k=5, value_fmt=_fmt_bp))}。"
        else:
            lead = f"该策略本期主要暴露因子（按|暴露|排序）为：{html.escape(_format_topn_text(top_risk, name_col='factor_field', value_col='exposure_now', k=5, value_fmt=lambda x: _fmt_float(x, 3)))}。"
        parts.append(
            f"<p>本段文字总结：{lead}"
            "当暴露与因子收益同向时通常顺风；当暴露方向与因子收益方向相反时通常逆风。Δ暴露用于识别风格漂移：若某些因子暴露在本期相对上期显著抬升/下降，应结合赛道与子基金 TopN 解释其来源并评估是否需要约束。</p>"
        )

    parts.append("<h2>告警项与风控关注</h2>")
    parts.append("<p class='section-lead'>本节将关键风险点用可核验指标表达：Residual 偏大、单赛道/单基金贡献过于集中、基差方向不一致、因子暴露与环境方向相悖等。</p>")
    parts.append("<ul>")
    parts.append("<li><strong>Residual：</strong>若策略层 Σ贡献 与组合收益差异较大，优先核对现金/费用/衍生品保证金/份额因素口径。</li>")
    parts.append("<li><strong>CTA 单点：</strong>若期货主观为主要拖累且权重高，建议单列风控维度（仓位上限/回撤阈值/相关性约束）。</li>")
    parts.append("<li><strong>基差风险：</strong>市场中性端如 IF/IC 基差暴露方向不一致，需复核对冲合约、展期成本与对冲比率漂移。</li>")
    parts.append("<li><strong>风格因子：</strong>股票多头如偏低波动/低Beta/偏大市值，在小盘/高波动占优阶段可能系统性逆风，建议设置暴露上限或偏离容忍区间。</li>")
    parts.append("</ul>")
    parts.append("<p>本节文字总结：告警的目的不是给出单点结论，而是把风险显性化并指向可执行检查项。建议将告警与回撤峰-谷时段做对照，优先处理高权重且贡献集中的风险源。</p>")

    parts.append("<h2>持仓建议（可执行）</h2>")
    parts.append("<ul>")
    parts.append("<li><strong>CTA 风险预算：</strong>对期货主观/贵金属方向设置更严格的仓位与回撤阈值，避免成为组合回撤单点来源。</li>")
    parts.append("<li><strong>股票多头风格约束：</strong>把 size/beta/volatility 作为组合级约束项，控制极端暴露；环境切换时优先通过指增池替换。</li>")
    parts.append("<li><strong>中性对冲复核：</strong>按周复核 IF/IC 基差暴露、展期成本与净敞口，避免收益被对冲成本吞噬。</li>")
    parts.append("<li><strong>TopN 动作：</strong>对子基金 TopN 做投后复核与替换评估：拖累基金重点查风格漂移/回撤控制，贡献基金重点查可持续性与相关性。</li>")
    parts.append("</ul>")
    parts.append("<p>本节文字总结：建议优先从高权重-高贡献集中的赛道/子基金入手，用风格约束与风险预算把风险转化为规则，同时复核对冲成本与基差风险，形成可持续的风险控制闭环。</p>")

    parts.append("<h2>总结陈述</h2>")
    parts.append(
        _build_exec_summary_html(
            product_name=product_name,
            begin_date=BEGIN_DATE,
            end_date=end_date,
            kpis=kpis,
            strat_df=strat_df,
            brinson_df=brinson_df,
            track_sections=track_sections,
            subfund_sections=subfund_sections,
            factor_sections=factor_sections,
        )
    )

    parts.append("<div class='hr'></div>")
    parts.append(f"<p class='small'>生成时间：{pd.Timestamp.today().date()}｜输出：HTML</p>")
    parts.append("</div></body></html>")

    report = "\n".join(parts)
    if args.output_format in ("html", "both"):
        with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(report)
        print(OUTPUT_HTML_PATH)
    if args.output_format in ("text", "both"):
        text = _build_text_report(
            product_name=product_name,
            pm_id=PM_ID,
            begin_date=BEGIN_DATE,
            end_date=end_date,
            kpis=kpis,
            strat_df=strat_df,
            brinson_df=brinson_df,
            brinson_summary=brinson_summary,
            pnl_df=pnl_df,
            pnl_summary=pnl_summary,
            track_sections=track_sections,
            subfund_sections=subfund_sections,
            factor_sections=factor_sections,
        )
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
