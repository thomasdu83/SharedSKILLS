"""
股票数据查询脚本

提供股票相关的数据查询功能，直接使用 data_management 核心模块。

使用方法：
    .venv\\Scripts\\python.exe stock_query.py

功能列表：
    1. 股票风格因子查询
    2. 股票行业分类查询
    3. 股票市值数据查询
    4. 股票行情查询
    5. 股票除权除息查询
    6. 股票股本数据查询
    7. 股票Barra因子查询
    8. 股票周期收益率查询
"""

import sys

# 强制 UTF-8 编码，解决 Windows 终端乱码问题
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
import pandas as pd

# 导入配置，确保路径正确
from main_config import add_project_path_to_sys
add_project_path_to_sys()

# 导入 data_management 核心模块
from data_management.core import StockData, SqliteSource, DBSource, ExcelSource


# ============================================================================
# 辅助函数
# ============================================================================

def _get_stock_data(source: str):
    """获取 StockData 实例"""
    if source == "sqlite":
        return StockData(SqliteSource(update=False))
    elif source == "db":
        return StockData(DBSource(update=False))
    elif source == "excel":
        return StockData(ExcelSource(update=False))
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

def query_stock_latest_info(stock_codes: list[str], source: str = "sqlite"):
    """
    查询股票最新信息（行业分类 + 市值）
    
    Args:
        stock_codes: 股票代码列表，如 ["600519", "000858"]
        source: 数据源，默认 "sqlite"
    
    Returns:
        dict: 包含行业和市值 DataFrame 的字典
    """
    print(f"\n{'='*60}")
    print(f"查询股票最新信息")
    print(f"股票代码: {', '.join(stock_codes)}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    today = datetime.now().strftime("%Y-%m-%d")
    stock_data = _get_stock_data(source)
    result = {}
    
    # 1. 行业分类
    try:
        df_industry = stock_data.stock_industry(stock_codes, today)
        if df_industry is not None and not df_industry.empty:
            print(_format_to_markdown(df_industry, "行业分类"))
            result['industry'] = df_industry
    except Exception as e:
        print(f"⚠️ 获取行业分类失败: {e}")
    
    # 2. 市值数据
    try:
        df_cap = stock_data.stock_cap(stock_codes, today, today)
        if df_cap is not None and not df_cap.empty:
            print(_format_to_markdown(df_cap, "市值数据"))
            result['cap'] = df_cap
    except Exception as e:
        print(f"⚠️ 获取市值数据失败: {e}")
    
    return result


def query_stock_price_history(stock_codes: list[str], days: int = 90, source: str = "sqlite"):
    """
    查询股票价格历史（最近N天行情）
    
    Args:
        stock_codes: 股票代码列表
        days: 查询天数，默认90天
        source: 数据源
    
    Returns:
        pd.DataFrame: 行情数据
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"查询股票价格历史（最近 {days} 天）")
    print(f"股票代码: {', '.join(stock_codes)}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    stock_data = _get_stock_data(source)
    df = stock_data.stock_quote(stock_codes, start_date, end_date)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    print(_format_to_markdown(df, "股票行情"))
    return df


def query_stock_style_analysis(stock_codes: list[str], months: int = 12, source: str = "sqlite"):
    """
    查询股票风格分析（风格因子 + Barra因子）
    
    Args:
        stock_codes: 股票代码列表
        months: 分析月数，默认12个月
        source: 数据源
    
    Returns:
        dict: 包含风格因子和Barra因子的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"股票风格分析")
    print(f"股票代码: {', '.join(stock_codes)}")
    print(f"分析周期: {months} 个月")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    stock_data = _get_stock_data(source)
    result = {}
    
    # 1. 风格因子
    try:
        df_style = stock_data.stock_style(stock_codes, start_date, end_date)
        if df_style is not None and not df_style.empty:
            print(_format_to_markdown(df_style, "风格因子"))
            result['style'] = df_style
    except Exception as e:
        print(f"⚠️ 获取风格因子失败: {e}")
    
    # 2. Barra因子
    try:
        df_barra = stock_data.stock_barra_factor(stock_codes, start_date, end_date)
        if df_barra is not None and not df_barra.empty:
            print(_format_to_markdown(df_barra, "Barra因子"))
            result['barra'] = df_barra
    except Exception as e:
        print(f"⚠️ 获取Barra因子失败: {e}")
    
    return result


def query_stock_return_analysis(stock_codes: list[str], months: int = 12, source: str = "sqlite"):
    """
    查询股票收益率分析（多周期收益率）
    
    Args:
        stock_codes: 股票代码列表
        months: 分析月数，默认12个月
        source: 数据源
    
    Returns:
        dict: 包含多周期收益率的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"股票收益率分析")
    print(f"股票代码: {', '.join(stock_codes)}")
    print(f"分析周期: {months} 个月")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    stock_data = _get_stock_data(source)
    result = {}
    
    # 多周期收益率
    for period in ['1M', '3M', '6M', '1Y']:
        try:
            df = stock_data.stock_periodic_return(stock_codes, start_date, end_date, period)
            if df is not None and not df.empty:
                print(_format_to_markdown(df, f"{period} 周期收益率"))
                result[f'return_{period}'] = df
        except Exception as e:
            print(f"⚠️ 获取 {period} 周期收益率失败: {e}")
    
    return result


def query_stock_corporate_actions(stock_codes: list[str], years: int = 2, source: str = "sqlite"):
    """
    查询股票公司行为（除权除息 + 股本变化）
    
    Args:
        stock_codes: 股票代码列表
        years: 查询年数，默认2年
        source: 数据源
    
    Returns:
        dict: 包含除权除息和股本数据的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"股票公司行为查询")
    print(f"股票代码: {', '.join(stock_codes)}")
    print(f"查询时间: 最近 {years} 年")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=years*365)).strftime("%Y-%m-%d")
    
    stock_data = _get_stock_data(source)
    result = {}
    
    # 1. 除权除息事件
    try:
        df_dr_xr = stock_data.stock_dr_xr_event(stock_codes, start_date, end_date)
        if df_dr_xr is not None and not df_dr_xr.empty:
            print(_format_to_markdown(df_dr_xr, "除权除息事件"))
            result['dr_xr'] = df_dr_xr
    except Exception as e:
        print(f"⚠️ 获取除权除息事件失败: {e}")
    
    # 2. 股本变化
    try:
        df_shares = stock_data.stock_shares(stock_codes, start_date, end_date)
        if df_shares is not None and not df_shares.empty:
            print(_format_to_markdown(df_shares, "股本数据"))
            result['shares'] = df_shares
    except Exception as e:
        print(f"⚠️ 获取股本数据失败: {e}")
    
    return result


# ============================================================================
# 主函数 - 提供交互式菜单
# ============================================================================

def main():
    """
    主函数 - 提供交互式查询菜单
    """
    print("\n" + "="*60)
    print("股票数据查询工具")
    print("="*60)
    print("\n请选择查询功能：")
    print("1. 股票最新信息（行业+市值）")
    print("2. 股票价格历史（最近90天）")
    print("3. 股票风格分析（12个月）")
    print("4. 股票收益率分析（12个月）")
    print("5. 股票公司行为（最近2年）")
    print("0. 退出")
    print("\n" + "="*60)
    
    choice = input("\n请输入选项（0-5）: ").strip()
    
    if choice == "0":
        print("退出程序。")
        return
    
    # 获取股票代码
    stock_codes_input = input("请输入股票代码（多个代码用逗号分隔）: ").strip()
    stock_codes = [code.strip() for code in stock_codes_input.split(",")]
    
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
        query_stock_latest_info(stock_codes, source)
    elif choice == "2":
        query_stock_price_history(stock_codes, 90, source)
    elif choice == "3":
        query_stock_style_analysis(stock_codes, 12, source)
    elif choice == "4":
        query_stock_return_analysis(stock_codes, 12, source)
    elif choice == "5":
        query_stock_corporate_actions(stock_codes, 2, source)
    else:
        print("无效的选项！")


if __name__ == "__main__":
    # 如果是直接运行，启动交互式菜单
    if len(sys.argv) == 1:
        main()
    else:
        # 支持命令行参数快速查询
        command = sys.argv[1] if len(sys.argv) > 1 else None
        
        if command == "info" and len(sys.argv) >= 3:
            stock_codes = sys.argv[2:]
            query_stock_latest_info(stock_codes)
        elif command == "price" and len(sys.argv) >= 3:
            stock_codes = [sys.argv[2]]
            days = int(sys.argv[3]) if len(sys.argv) >= 4 else 90
            query_stock_price_history(stock_codes, days)
        elif command == "style" and len(sys.argv) >= 3:
            stock_codes = sys.argv[2:]
            query_stock_style_analysis(stock_codes)
        elif command == "return" and len(sys.argv) >= 3:
            stock_codes = sys.argv[2:]
            query_stock_return_analysis(stock_codes)
        elif command == "actions" and len(sys.argv) >= 3:
            stock_codes = sys.argv[2:]
            query_stock_corporate_actions(stock_codes)
        else:
            print("使用方法：")
            print("  交互式菜单：.venv\\Scripts\\python.exe stock_query.py")
            print("  查询股票信息：.venv\\Scripts\\python.exe stock_query.py info 600519")
            print("  价格历史：.venv\\Scripts\\python.exe stock_query.py price 600519 90")
            print("  风格分析：.venv\\Scripts\\python.exe stock_query.py style 600519")
            print("  收益率分析：.venv\\Scripts\\python.exe stock_query.py return 600519")
            print("  公司行为：.venv\\Scripts\\python.exe stock_query.py actions 600519")
