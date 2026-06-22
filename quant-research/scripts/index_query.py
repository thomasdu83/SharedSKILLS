"""
指数数据查询脚本

提供指数相关的数据查询功能，直接使用 data_management 核心模块。

使用方法：
    .venv\\Scripts\\python.exe index_query.py

功能列表：
    1. 指数列表查询
    2. 指数行情查询
    3. 指数周期收益率查询
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
from data_management.core import IndexData, SqliteSource, DBSource, ExcelSource


# ============================================================================
# 辅助函数
# ============================================================================

def _get_index_data(source: str):
    """获取 IndexData 实例"""
    if source == "sqlite":
        return IndexData(SqliteSource(update=False))
    elif source == "db":
        return IndexData(DBSource(update=False))
    elif source == "excel":
        return IndexData(ExcelSource(update=False))
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

def query_all_index_list(source: str = "sqlite"):
    """
    查询所有指数列表
    
    Args:
        source: 数据源，默认 "sqlite"
    
    Returns:
        pd.DataFrame: 指数列表数据
    """
    print(f"\n{'='*60}")
    print(f"查询指数列表")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    index_data = _get_index_data(source)
    df = index_data.index_list()
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    print(_format_to_markdown(df, "指数列表"))
    return df


def query_index_ytd_quote(index_codes: list[str], source: str = "sqlite"):
    """
    查询指数年初至今（YTD）行情
    
    Args:
        index_codes: 指数代码列表，如 ["000300", "000905"]
        source: 数据源，默认 "sqlite"
    
    Returns:
        pd.DataFrame: 行情数据
    """
    today = datetime.now().strftime("%Y-%m-%d")
    year_start = f"{datetime.now().year}-01-01"
    
    print(f"\n{'='*60}")
    print(f"查询指数年初至今（YTD）行情")
    print(f"指数代码: {', '.join(index_codes)}")
    print(f"时间范围: {year_start} 至 {today}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    index_data = _get_index_data(source)
    df = index_data.index_quote(index_codes, year_start, today)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    print(_format_to_markdown(df, "指数行情"))
    return df


def query_index_recent_quote(index_codes: list[str], days: int = 90, source: str = "sqlite"):
    """
    查询指数最近N天行情
    
    Args:
        index_codes: 指数代码列表
        days: 最近天数，默认90天
        source: 数据源
    
    Returns:
        pd.DataFrame: 行情数据
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"查询指数最近 {days} 天行情")
    print(f"指数代码: {', '.join(index_codes)}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    index_data = _get_index_data(source)
    df = index_data.index_quote(index_codes, start_date, end_date)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    print(_format_to_markdown(df, "指数行情"))
    return df


def query_index_return_analysis(index_codes: list[str], months: int = 12, source: str = "sqlite"):
    """
    查询指数收益率分析（多周期收益率）
    
    Args:
        index_codes: 指数代码列表
        months: 分析月数，默认12个月
        source: 数据源
    
    Returns:
        dict: 包含多周期收益率的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"指数收益率分析")
    print(f"指数代码: {', '.join(index_codes)}")
    print(f"分析周期: {months} 个月")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    index_data = _get_index_data(source)
    result = {}
    
    # 多周期收益率
    for period in ['1M', '3M', '6M', '1Y']:
        try:
            df = index_data.index_periodic_return(index_codes, start_date, end_date, period)
            if df is not None and not df.empty:
                print(_format_to_markdown(df, f"{period} 周期收益率"))
                result[f'return_{period}'] = df
        except Exception as e:
            print(f"⚠️ 获取 {period} 周期收益率失败: {e}")
    
    return result


def compare_index_performance(index_codes: list[str], months: int = 12, source: str = "sqlite"):
    """
    对比多个指数的表现
    
    Args:
        index_codes: 指数代码列表（至少2个）
        months: 对比月数，默认12个月
        source: 数据源
    
    Returns:
        dict: 包含行情和收益率对比的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"指数表现对比")
    print(f"指数代码: {', '.join(index_codes)}")
    print(f"对比周期: {months} 个月")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    index_data = _get_index_data(source)
    result = {}
    
    # 1. 行情对比
    try:
        df_quote = index_data.index_quote(index_codes, start_date, end_date)
        if df_quote is not None and not df_quote.empty:
            print(_format_to_markdown(df_quote, "行情数据"))
            result['quote'] = df_quote
    except Exception as e:
        print(f"⚠️ 获取行情数据失败: {e}")
    
    # 2. 多周期收益率对比
    for period, title in [('1M', '1个月收益率'), ('3M', '3个月收益率'), ('1Y', '年度收益率')]:
        try:
            df = index_data.index_periodic_return(index_codes, start_date, end_date, period)
            if df is not None and not df.empty:
                print(_format_to_markdown(df, title))
                result[f'return_{period.lower()}'] = df
        except Exception as e:
            print(f"⚠️ 获取{title}失败: {e}")
    
    return result


# ============================================================================
# 常用指数代码
# ============================================================================

COMMON_INDEX = {
    "沪深300": "000300",
    "中证500": "000905",
    "中证1000": "000852",
    "创业板指": "399006",
    "科创50": "000688",
    "上证50": "000016",
    "深证成指": "399001",
    "上证指数": "000001",
}


def get_index_code_by_name(name: str) -> str:
    """
    根据指数名称获取代码
    
    Args:
        name: 指数名称
    
    Returns:
        str: 指数代码
    """
    return COMMON_INDEX.get(name, name)


# ============================================================================
# 主函数 - 提供交互式菜单
# ============================================================================

def main():
    """
    主函数 - 提供交互式查询菜单
    """
    print("\n" + "="*60)
    print("指数数据查询工具")
    print("="*60)
    print("\n请选择查询功能：")
    print("1. 查询所有指数列表")
    print("2. 指数年初至今（YTD）行情")
    print("3. 指数最近90天行情")
    print("4. 指数收益率分析（12个月）")
    print("5. 指数表现对比")
    print("0. 退出")
    print("\n" + "="*60)
    print("\n常用指数：")
    for name, code in COMMON_INDEX.items():
        print(f"  {name}: {code}")
    print("="*60)
    
    choice = input("\n请输入选项（0-5）: ").strip()
    
    if choice == "0":
        print("退出程序。")
        return
    
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
        query_all_index_list(source)
    elif choice in ["2", "3", "4", "5"]:
        # 获取指数代码
        index_codes_input = input("请输入指数代码或名称（多个用逗号分隔）: ").strip()
        index_codes = []
        for item in index_codes_input.split(","):
            item = item.strip()
            code = get_index_code_by_name(item)
            index_codes.append(code)
        
        if choice == "2":
            query_index_ytd_quote(index_codes, source)
        elif choice == "3":
            query_index_recent_quote(index_codes, 90, source)
        elif choice == "4":
            query_index_return_analysis(index_codes, 12, source)
        elif choice == "5":
            compare_index_performance(index_codes, 12, source)
    else:
        print("无效的选项！")


if __name__ == "__main__":
    # 如果是直接运行，启动交互式菜单
    if len(sys.argv) == 1:
        main()
    else:
        # 支持命令行参数快速查询
        command = sys.argv[1] if len(sys.argv) > 1 else None
        
        if command == "list":
            query_all_index_list()
        elif command == "ytd" and len(sys.argv) >= 3:
            index_codes = sys.argv[2:]
            query_index_ytd_quote(index_codes)
        elif command == "quote" and len(sys.argv) >= 3:
            index_codes = [sys.argv[2]]
            days = int(sys.argv[3]) if len(sys.argv) >= 4 else 90
            query_index_recent_quote(index_codes, days)
        elif command == "return" and len(sys.argv) >= 3:
            index_codes = sys.argv[2:]
            query_index_return_analysis(index_codes)
        elif command == "compare" and len(sys.argv) >= 4:
            index_codes = sys.argv[2:]
            compare_index_performance(index_codes)
        else:
            print("使用方法：")
            print("  交互式菜单：.venv\\Scripts\\python.exe index_query.py")
            print("  查询指数列表：.venv\\Scripts\\python.exe index_query.py list")
            print("  YTD行情：.venv\\Scripts\\python.exe index_query.py ytd 000300")
            print("  最近行情：.venv\\Scripts\\python.exe index_query.py quote 000300 90")
            print("  收益率分析：.venv\\Scripts\\python.exe index_query.py return 000300")
            print("  指数对比：.venv\\Scripts\\python.exe index_query.py compare 000300 000905")
