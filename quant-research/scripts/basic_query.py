"""
基础数据查询脚本

提供基础数据相关的查询功能，直接使用 data_management 核心模块。

使用方法：
    .venv\Scripts\python.exe basic_query.py

功能列表：
    1. 证券主表查询
    2. 日期矩阵查询
    3. 基金半年度日期查询
    4. 基金季度日期查询
"""

import sys
from datetime import datetime
import pandas as pd

# 导入配置，确保路径正确
from main_config import add_project_path_to_sys
add_project_path_to_sys()

# 导入 data_management 核心模块
from data_management.core import BasicData, SqliteSource, DBSource, ExcelSource


# ============================================================================
# 辅助函数
# ============================================================================

def _get_basic_data(source: str):
    """获取 BasicData 实例"""
    if source == "sqlite":
        return BasicData(SqliteSource(update=False))
    elif source == "db":
        return BasicData(DBSource(update=False))
    elif source == "excel":
        return BasicData(ExcelSource(update=False))
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

def query_secu_main(source: str = "sqlite"):
    """
    查询证券主表数据
    
    Args:
        source: 数据源，默认 "sqlite"
    
    Returns:
        pd.DataFrame: 证券主表数据
    """
    print(f"\n{'='*60}")
    print(f"查询证券主表")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    basic_data = _get_basic_data(source)
    df = basic_data.secu_main()
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    print(_format_to_markdown(df, "证券主表"))
    return df


def query_trading_calendar(date_type: str = "D", source: str = "sqlite"):
    """
    查询交易日历（日期矩阵）
    
    Args:
        date_type: 日期类型，支持 'D'（日）、'W'（周）、'M'（月）、'Q'（季度）、'Y'（年）
        source: 数据源，默认 "sqlite"
    
    Returns:
        pd.DataFrame: 日期矩阵数据
    """
    print(f"\n{'='*60}")
    print(f"查询交易日历")
    print(f"日期类型: {date_type}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    basic_data = _get_basic_data(source)
    df = basic_data.date_mat(date_type)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    print(_format_to_markdown(df, f"交易日历 ({date_type})"))
    return df


def query_fund_reporting_dates(source: str = "sqlite"):
    """
    查询基金报告期日期（半年报 + 季报）
    
    Args:
        source: 数据源，默认 "sqlite"
    
    Returns:
        dict: 包含半年报和季报日期的 DataFrame 字典
    """
    print(f"\n{'='*60}")
    print(f"查询基金报告期日期")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    basic_data = _get_basic_data(source)
    result = {}
    
    # 1. 半年报日期
    try:
        df_semi = basic_data.fund_date_semi()
        if df_semi is not None and not df_semi.empty:
            print(_format_to_markdown(df_semi, "基金半年报日期"))
            result['semi'] = df_semi
    except Exception as e:
        print(f"⚠️ 获取基金半年报日期失败: {e}")
    
    # 2. 季报日期
    try:
        df_quarter = basic_data.fund_date_quarter()
        if df_quarter is not None and not df_quarter.empty:
            print(_format_to_markdown(df_quarter, "基金季报日期"))
            result['quarter'] = df_quarter
    except Exception as e:
        print(f"⚠️ 获取基金季报日期失败: {e}")
    
    return result


def query_recent_trading_days(date_type: str = "D", limit: int = 20, source: str = "sqlite"):
    """
    查询最近的交易日（只显示最近的N天）
    
    Args:
        date_type: 日期类型
        limit: 显示数量
        source: 数据源
    
    Returns:
        pd.DataFrame: 最近交易日数据
    """
    print(f"\n{'='*60}")
    print(f"查询最近 {limit} 个交易日")
    print(f"日期类型: {date_type}")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    basic_data = _get_basic_data(source)
    df = basic_data.date_mat(date_type)
    
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    # 取最近的 N 条记录
    df_recent = df.tail(limit)
    
    print(_format_to_markdown(df_recent, f"最近 {limit} 个交易日"))
    return df_recent


# ============================================================================
# 主函数 - 提供交互式菜单
# ============================================================================

def main():
    """
    主函数 - 提供交互式查询菜单
    """
    print("\n" + "="*60)
    print("基础数据查询工具")
    print("="*60)
    print("\n请选择查询功能：")
    print("1. 证券主表")
    print("2. 交易日历（日频）")
    print("3. 交易日历（周频）")
    print("4. 交易日历（月频）")
    print("5. 基金报告期日期")
    print("6. 最近交易日（最近20天）")
    print("0. 退出")
    print("\n" + "="*60)
    
    choice = input("\n请输入选项（0-6）: ").strip()
    
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
        query_secu_main(source)
    elif choice == "2":
        query_trading_calendar("D", source)
    elif choice == "3":
        query_trading_calendar("W", source)
    elif choice == "4":
        query_trading_calendar("M", source)
    elif choice == "5":
        query_fund_reporting_dates(source)
    elif choice == "6":
        query_recent_trading_days("D", 20, source)
    else:
        print("无效的选项！")


if __name__ == "__main__":
    # 如果是直接运行，启动交互式菜单
    if len(sys.argv) == 1:
        main()
    else:
        # 支持命令行参数快速查询
        command = sys.argv[1] if len(sys.argv) > 1 else None
        
        if command == "secu":
            query_secu_main()
        elif command == "calendar":
            date_type = sys.argv[2] if len(sys.argv) >= 3 else "D"
            query_trading_calendar(date_type)
        elif command == "fund_dates":
            query_fund_reporting_dates()
        elif command == "recent":
            date_type = sys.argv[2] if len(sys.argv) >= 3 else "D"
            limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 20
            query_recent_trading_days(date_type, limit)
        else:
            print("使用方法：")
            print("  交互式菜单：.venv\\Scripts\\python.exe basic_query.py")
            print("  证券主表：.venv\\Scripts\\python.exe basic_query.py secu")
            print("  交易日历：.venv\\Scripts\\python.exe basic_query.py calendar D")
            print("  基金报告期：.venv\\Scripts\\python.exe basic_query.py fund_dates")
            print("  最近交易日：.venv\\Scripts\\python.exe basic_query.py recent D 20")
