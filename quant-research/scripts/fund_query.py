"""
基金数据查询脚本

提供基金相关的数据查询功能，直接使用 data_management 核心模块。

使用方法：
    .venv\\Scripts\\python.exe fund_query.py

功能列表：
    1. 基金收益率查询
    2. 基金净值查询
    3. 基金ID信息查询
    4. 基金分类查询
    5. 基金经理信息查询
    6. 基金持仓查询
    7. 基金规模查询
    8. 基金资产配置查询
    ... 更多功能
"""

import sys

# 强制 UTF-8 编码，解决 Windows 终端乱码问题
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from typing import Literal
import pandas as pd

# 导入配置，确保路径正确
from main_config import add_project_path_to_sys
add_project_path_to_sys()

# 导入 data_management 核心模块
from data_management.core import FundData, SqliteSource, DBSource, ExcelSource


# ============================================================================
# 辅助函数
# ============================================================================

def _get_fund_data(source: str):
    """获取 FundData 实例"""
    if source == "sqlite":
        return FundData(SqliteSource(update=False))
    elif source == "db":
        return FundData(DBSource(update=False))
    elif source == "excel":
        return FundData(ExcelSource(update=False))
    else:
        raise ValueError(f"不支持的数据源: {source}")


def _format_to_markdown(df: pd.DataFrame, title: str = None) -> str:
    """将 DataFrame 格式化为 Markdown"""
    if df is None or df.empty:
        return "未找到数据"
    
    result = ""
    if title:
        result += f"\n【{title}】\n"
    result += df.to_markdown(index=False)
    return result


# ============================================================================
# 快捷查询函数
# ============================================================================

def query_fund_ytd_return(fund_codes: list[str], source: str = "sqlite"):
    """
    查询基金年初至今（YTD）收益率
    
    Args:
        fund_codes: 基金代码列表，如 ["377240", "000001"]
        source: 数据源，默认 "sqlite"
    
    Returns:
        pd.DataFrame: 收益率数据
    """
    today = datetime.now().strftime("%Y-%m-%d")
    year_start = f"{datetime.now().year}-01-01"
    
    print(f"\n{'='*60}")
    print(f"查询基金年初至今（YTD）收益率")
    print(f"基金代码: {', '.join(fund_codes)}")
    print(f"时间范围: {year_start} 至 {today}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    # 获取数据
    fund_data = _get_fund_data(source)
    df = fund_data.fund_ret(fund_codes, year_start, today)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    # 格式化展示
    df_display = df.copy()
    df_display.columns = ['基金代码', '截止日期', '累计收益率']
    df_display['累计收益率'] = df_display['累计收益率'].apply(
        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
    )
    df_display['截止日期'] = pd.to_datetime(df_display['截止日期']).dt.strftime('%Y-%m-%d')
    
    print(_format_to_markdown(df_display, "基金收益率"))
    return df


def query_fund_recent_return(fund_codes: list[str], days: int = 30, source: str = "sqlite"):
    """
    查询基金最近N天的收益率
    
    Args:
        fund_codes: 基金代码列表
        days: 最近天数，默认30天
        source: 数据源
    
    Returns:
        pd.DataFrame: 收益率数据
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"查询基金最近 {days} 天收益率")
    print(f"基金代码: {', '.join(fund_codes)}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    # 获取数据
    fund_data = _get_fund_data(source)
    df = fund_data.fund_ret(fund_codes, start_date, end_date)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    # 格式化展示
    df_display = df.copy()
    df_display.columns = ['基金代码', '截止日期', '累计收益率']
    df_display['累计收益率'] = df_display['累计收益率'].apply(
        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
    )
    df_display['截止日期'] = pd.to_datetime(df_display['截止日期']).dt.strftime('%Y-%m-%d')
    
    print(_format_to_markdown(df_display, "基金收益率"))
    return df


def query_fund_period_return(fund_codes: list[str], start_date: str, end_date: str, source: str = "sqlite"):
    """
    查询基金在指定日期范围内的收益率
    
    Args:
        fund_codes: 基金代码列表，如 ["377240", "000001"]
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        source: 数据源，默认 "sqlite"
    
    Returns:
        pd.DataFrame: 收益率数据
    """
    print(f"\n{'='*60}")
    print(f"查询基金区间收益率")
    print(f"基金代码: {', '.join(fund_codes)}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    # 获取数据
    fund_data = _get_fund_data(source)
    df = fund_data.fund_ret(fund_codes, start_date, end_date)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    # 格式化展示
    df_display = df.copy()
    df_display.columns = ['基金代码', '截止日期', '累计收益率']
    df_display['累计收益率'] = df_display['累计收益率'].apply(
        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
    )
    df_display['截止日期'] = pd.to_datetime(df_display['截止日期']).dt.strftime('%Y-%m-%d')
    
    print(_format_to_markdown(df_display, "基金收益率"))
    return df


def query_fund_info_complete(fund_code: str, source: str = "sqlite"):
    """
    查询基金的完整信息（ID、分类、经理、规模等）
    
    Args:
        fund_code: 基金代码
        source: 数据源
    
    Returns:
        dict: 包含各项信息的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"查询基金完整信息")
    print(f"基金代码: {fund_code}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    fund_data = _get_fund_data(source)
    result = {}
    
    # 1. 基金ID信息
    try:
        df_id = fund_data.fund_id([fund_code])
        if df_id is not None and not df_id.empty:
            print(_format_to_markdown(df_id, "基金ID信息"))
            result['id'] = df_id
    except Exception as e:
        print(f"⚠️ 获取基金ID信息失败: {e}")
    
    # 2. 基金经理信息
    try:
        df_pm = fund_data.fund_pm([fund_code])
        if df_pm is not None and not df_pm.empty:
            print(_format_to_markdown(df_pm, "基金经理信息"))
            result['pm'] = df_pm
    except Exception as e:
        print(f"⚠️ 获取基金经理信息失败: {e}")
    
    # 3. 基金规模信息（最近一年）
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        df_scale = fund_data.fund_scale([fund_code], start_date, end_date)
        if df_scale is not None and not df_scale.empty:
            print(_format_to_markdown(df_scale, "基金规模信息"))
            result['scale'] = df_scale
    except Exception as e:
        print(f"⚠️ 获取基金规模信息失败: {e}")
    
    return result


def query_fund_performance_analysis(fund_code: str, months: int = 12, source: str = "sqlite"):
    """
    查询基金业绩分析（收益率 + 周期收益率）
    
    Args:
        fund_code: 基金代码
        months: 分析月数，默认12个月
        source: 数据源
    
    Returns:
        dict: 包含收益率和周期收益率的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"基金业绩分析")
    print(f"基金代码: {fund_code}")
    print(f"分析周期: {months} 个月")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    fund_data = _get_fund_data(source)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    result = {}
    
    # 1. 累计收益率
    try:
        df_ret = fund_data.fund_ret([fund_code], start_date, end_date)
        if df_ret is not None and not df_ret.empty:
            df_display = df_ret.copy()
            df_display.columns = ['基金代码', '截止日期', '累计收益率']
            df_display['累计收益率'] = df_display['累计收益率'].apply(lambda x: f"{x:.2%}")
            df_display['截止日期'] = pd.to_datetime(df_display['截止日期']).dt.strftime('%Y-%m-%d')
            print(_format_to_markdown(df_display, "累计收益率"))
            result['total_return'] = df_ret
    except Exception as e:
        print(f"⚠️ 获取累计收益率失败: {e}")
    
    # 2. 周期收益率（1个月、3个月、6个月）
    for period in ['1M', '3M', '6M']:
        try:
            df_period = fund_data.fund_periodic_return([fund_code], start_date, end_date, period)
            if df_period is not None and not df_period.empty:
                print(_format_to_markdown(df_period, f"{period} 周期收益率"))
                result[f'return_{period}'] = df_period
        except Exception as e:
            print(f"⚠️ 获取 {period} 周期收益率失败: {e}")
    
    return result


def query_fund_holdings(fund_code: str, source: str = "sqlite"):
    """
    查询基金持仓（股票+资产配置）
    
    Args:
        fund_code: 基金代码
        source: 数据源
    
    Returns:
        dict: 包含持仓信息的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"基金持仓查询")
    print(f"基金代码: {fund_code}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    fund_data = _get_fund_data(source)
    
    # 查询最近一年的持仓数据
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    result = {}
    
    # 1. 股票持仓
    try:
        df_stock = fund_data.fund_stock([fund_code], start_date, end_date)
        if df_stock is not None and not df_stock.empty:
            # 只显示最近的持仓（取最新日期）
            latest_date = df_stock['rpt_date'].max()
            df_latest = df_stock[df_stock['rpt_date'] == latest_date].head(10)
            print(_format_to_markdown(df_latest, f"股票持仓 (截至 {latest_date})"))
            result['stock'] = df_stock
    except Exception as e:
        print(f"⚠️ 获取股票持仓失败: {e}")
    
    # 2. 资产配置
    try:
        df_asset = fund_data.fund_asset([fund_code], start_date, end_date)
        if df_asset is not None and not df_asset.empty:
            print(_format_to_markdown(df_asset, "资产配置"))
            result['asset'] = df_asset
    except Exception as e:
        print(f"⚠️ 获取资产配置失败: {e}")
    
    return result


# ============================================================================
# 主函数 - 提供交互式菜单
# ============================================================================

def main():
    """
    主函数 - 提供交互式查询菜单
    """
    print("\n" + "="*60)
    print("基金数据查询工具")
    print("="*60)
    print("\n请选择查询功能：")
    print("1. 基金年初至今（YTD）收益率")
    print("2. 基金最近30天收益率")
    print("3. 基金完整信息查询")
    print("4. 基金业绩分析（过去12个月）")
    print("5. 基金持仓查询")
    print("6. 自定义查询")
    print("0. 退出")
    print("\n" + "="*60)
    
    choice = input("\n请输入选项（0-6）: ").strip()
    
    if choice == "0":
        print("退出程序。")
        return
    
    # 获取基金代码
    fund_codes_input = input("请输入基金代码（多个代码用逗号分隔）: ").strip()
    fund_codes = [code.strip() for code in fund_codes_input.split(",")]
    
    # 选择数据源
    print("\n选择数据源：")
    print("1. sqlite（本地数据库，快速）")
    print("2. db（生产数据库，最新）")
    print("3. excel（本地Excel文件）")
    source_choice = input("请选择数据源（默认1）: ").strip() or "1"
    source_map = {"1": "sqlite", "2": "db", "3": "excel"}
    source = source_map.get(source_choice, "sqlite")
    
    # 执行查询
    if choice == "1":
        query_fund_ytd_return(fund_codes, source)
    elif choice == "2":
        query_fund_recent_return(fund_codes, 30, source)
    elif choice == "3":
        for code in fund_codes:
            query_fund_info_complete(code, source)
    elif choice == "4":
        for code in fund_codes:
            query_fund_performance_analysis(code, 12, source)
    elif choice == "5":
        for code in fund_codes:
            query_fund_holdings(code, source)
    elif choice == "6":
        print("\n自定义查询功能待实现...")
    else:
        print("无效的选项！")


# ============================================================================
# 示例用法
# ============================================================================

if __name__ == "__main__":
    # 如果是直接运行，启动交互式菜单
    if len(sys.argv) == 1:
        main()
    else:
        # 支持命令行参数快速查询
        # 用法示例：
        # .venv\Scripts\python.exe fund_query.py ytd 377240
        # .venv\Scripts\python.exe fund_query.py recent 377240 30
        
        command = sys.argv[1] if len(sys.argv) > 1 else None
        
        if command == "ytd" and len(sys.argv) >= 3:
            fund_codes = sys.argv[2:]
            query_fund_ytd_return(fund_codes)
        elif command == "recent" and len(sys.argv) >= 4:
            fund_codes = [sys.argv[2]]
            days = int(sys.argv[3])
            query_fund_recent_return(fund_codes, days)
        elif command == "info" and len(sys.argv) >= 3:
            fund_code = sys.argv[2]
            query_fund_info_complete(fund_code)
        elif command == "performance" and len(sys.argv) >= 3:
            fund_code = sys.argv[2]
            months = int(sys.argv[3]) if len(sys.argv) >= 4 else 12
            query_fund_performance_analysis(fund_code, months)
        elif command == "holdings" and len(sys.argv) >= 3:
            fund_code = sys.argv[2]
            query_fund_holdings(fund_code)
        elif command == "period" and len(sys.argv) >= 5:
            fund_codes = [sys.argv[2]]
            start_date = sys.argv[3]
            end_date = sys.argv[4]
            query_fund_period_return(fund_codes, start_date, end_date)
        else:
            print("使用方法：")
            print("  交互式菜单：.venv/Scripts/python.exe fund_query.py")
            print("  快速查询YTD：.venv/Scripts/python.exe fund_query.py ytd 377240")
            print("  查询最近N天：.venv/Scripts/python.exe fund_query.py recent 377240 30")
            print("  查询基金信息：.venv/Scripts/python.exe fund_query.py info 377240")
            print("  业绩分析：.venv/Scripts/python.exe fund_query.py performance 377240 12")
            print("  持仓查询：.venv/Scripts/python.exe fund_query.py holdings 377240")
            print("  区间收益：.venv/Scripts/python.exe fund_query.py period 377240 2024-01-01 2024-01-31")
