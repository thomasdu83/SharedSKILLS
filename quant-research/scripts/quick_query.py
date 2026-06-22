"""
快速查询工具 - 命令行入口

本脚本是统一的命令行入口，调用各核心脚本的函数。
核心业务逻辑在：fund_query.py, index_query.py, stock_query.py

使用方法：
    .venv\\Scripts\\python.exe quick_query.py <命令> <参数...>

示例：
    .venv\\Scripts\\python.exe quick_query.py fund_ytd 377240
    .venv\\Scripts\\python.exe quick_query.py fund_period 377240 2024-01-01 2024-01-31
    .venv\\Scripts\\python.exe quick_query.py index_ytd 000300,000905
    .venv\\Scripts\\python.exe quick_query.py stock_info 600519
"""

import sys

# 强制 UTF-8 编码，解决 Windows 终端乱码问题
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 导入配置，确保路径正确
from main_config import add_project_path_to_sys
add_project_path_to_sys()

# ============================================================================
# 导入核心脚本的函数（分层架构）
# ============================================================================

# 基金相关
from fund_query import (
    query_fund_ytd_return,
    query_fund_recent_return,
    query_fund_period_return,
    query_fund_info_complete,
    query_fund_performance_analysis,
)

# 指数相关
from index_query import (
    query_index_ytd_quote,
    query_index_recent_quote,
    compare_index_performance,
)

# 股票相关
from stock_query import (
    query_stock_latest_info,
    query_stock_price_history,
)


# ============================================================================
# 包装函数 - 命令行入口（调用核心脚本）
# ============================================================================

def fund_ytd(fund_codes: list[str], source: str = "sqlite"):
    """查询基金年初至今（YTD）收益 - 调用 fund_query"""
    return query_fund_ytd_return(fund_codes, source)


def fund_recent(fund_codes: list[str], days: int = 30, source: str = "sqlite"):
    """查询基金最近N天收益 - 调用 fund_query"""
    return query_fund_recent_return(fund_codes, days, source)


def fund_period(fund_codes: list[str], start_date: str, end_date: str, source: str = "sqlite"):
    """查询基金指定日期范围收益率 - 调用 fund_query"""
    return query_fund_period_return(fund_codes, start_date, end_date, source)


def fund_detail(fund_code: str, source: str = "sqlite"):
    """查询基金详细信息 - 调用 fund_query"""
    return query_fund_info_complete(fund_code, source)


def fund_compare(fund_codes: list[str], source: str = "sqlite"):
    """对比多只基金今年表现 - 调用 fund_query"""
    # 使用业绩分析函数对比多只基金
    results = {}
    for code in fund_codes:
        results[code] = query_fund_ytd_return([code], source)
    return results


def index_ytd(index_codes: list[str], source: str = "sqlite"):
    """查询指数年初至今表现 - 调用 index_query"""
    return query_index_ytd_quote(index_codes, source)


def index_compare(index_codes: list[str], source: str = "sqlite"):
    """对比多个指数表现 - 调用 index_query"""
    return compare_index_performance(index_codes, 12, source)


def stock_info(stock_codes: list[str], source: str = "sqlite"):
    """查询股票基本信息 - 调用 stock_query"""
    return query_stock_latest_info(stock_codes, source)


def stock_price(stock_codes: list[str], days: int = 90, source: str = "sqlite"):
    """查询股票价格走势 - 调用 stock_query"""
    return query_stock_price_history(stock_codes, days, source)


# ============================================================================
# 命令映射表
# ============================================================================

COMMANDS = {
    # 基金命令
    "fund_ytd": {
        "func": fund_ytd,
        "desc": "查询基金年初至今收益",
        "usage": "quick_query.py fund_ytd <基金代码1>[,<基金代码2>,...]",
        "example": "quick_query.py fund_ytd 377240",
    },
    "fund_recent": {
        "func": fund_recent,
        "desc": "查询基金最近N天收益",
        "usage": "quick_query.py fund_recent <基金代码1>[,<基金代码2>,...] [天数]",
        "example": "quick_query.py fund_recent 377240 30",
    },
    "fund_period": {
        "func": fund_period,
        "desc": "查询基金指定日期范围收益率",
        "usage": "quick_query.py fund_period <基金代码> <开始日期> <结束日期>",
        "example": "quick_query.py fund_period 377240 2024-01-01 2024-01-31",
    },
    "fund_detail": {
        "func": fund_detail,
        "desc": "查询基金详细信息",
        "usage": "quick_query.py fund_detail <基金代码>",
        "example": "quick_query.py fund_detail 377240",
    },
    "fund_compare": {
        "func": fund_compare,
        "desc": "对比多只基金今年表现",
        "usage": "quick_query.py fund_compare <基金代码1>,<基金代码2>[,...]",
        "example": "quick_query.py fund_compare 377240,000001",
    },
    # 指数命令
    "index_ytd": {
        "func": index_ytd,
        "desc": "查询指数年初至今表现",
        "usage": "quick_query.py index_ytd <指数代码1>[,<指数代码2>,...]",
        "example": "quick_query.py index_ytd 000300,000905",
    },
    "index_compare": {
        "func": index_compare,
        "desc": "对比多个指数表现",
        "usage": "quick_query.py index_compare <指数代码1>,<指数代码2>[,...]",
        "example": "quick_query.py index_compare 000300,000905",
    },
    # 股票命令
    "stock_info": {
        "func": stock_info,
        "desc": "查询股票基本信息",
        "usage": "quick_query.py stock_info <股票代码1>[,<股票代码2>,...]",
        "example": "quick_query.py stock_info 600519",
    },
    "stock_price": {
        "func": stock_price,
        "desc": "查询股票价格走势",
        "usage": "quick_query.py stock_price <股票代码1>[,<股票代码2>,...] [天数]",
        "example": "quick_query.py stock_price 600519 90",
    },
}


# ============================================================================
# 主函数 - 命令行解析
# ============================================================================

def show_help():
    """显示帮助信息"""
    print("\n" + "="*60)
    print("快速查询工具 - 帮助信息")
    print("="*60)
    print("\n可用命令：\n")
    
    # 按类别分组显示
    categories = {
        "基金": ["fund_ytd", "fund_recent", "fund_period", "fund_detail", "fund_compare"],
        "指数": ["index_ytd", "index_compare"],
        "股票": ["stock_info", "stock_price"],
    }
    
    for category, cmds in categories.items():
        print(f"【{category}】")
        for cmd in cmds:
            if cmd in COMMANDS:
                info = COMMANDS[cmd]
                print(f"  {cmd}")
                print(f"    描述: {info['desc']}")
                print(f"    用法: {info['usage']}")
                print(f"    示例: {info['example']}")
        print()
    
    print("="*60)
    print("\n数据源：默认 sqlite（本地数据库，快速）")
    print("="*60)


def main():
    """主函数 - 解析命令行参数并调用对应函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command in ["help", "-h", "--help"]:
        show_help()
        return
    
    if command not in COMMANDS:
        print(f"\n❌ 错误：未知命令 '{command}'")
        print("使用 'help' 查看可用命令")
        return
    
    # 解析 --source 参数
    source = "sqlite"  # 默认数据源
    args = sys.argv[2:]  # 去掉脚本名和命令
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] == "--source" and i + 1 < len(args):
            source = args[i + 1]
            i += 2
        elif args[i].startswith("--source="):
            source = args[i].split("=", 1)[1]
            i += 1
        else:
            filtered_args.append(args[i])
            i += 1
    
    # 检查参数
    if len(filtered_args) < 1:
        print(f"\n❌ 错误：缺少参数")
        print(f"用法: {COMMANDS[command]['usage']}")
        return
    
    # 获取代码列表（用逗号分隔）
    codes_str = filtered_args[0]
    codes = [code.strip() for code in codes_str.split(",")]
    
    # 执行命令
    try:
        func = COMMANDS[command]["func"]
        
        if command == "fund_period":
            # fund_period 需要 开始日期 和 结束日期
            if len(filtered_args) < 3:
                print(f"\n❌ 错误：fund_period 需要开始日期和结束日期")
                print(f"用法: {COMMANDS[command]['usage']}")
                return
            start_date = filtered_args[1]
            end_date = filtered_args[2]
            func(codes, start_date, end_date, source)
        elif command in ["fund_recent", "stock_price"]:
            # 获取可选的天数参数
            days = 30 if command == "fund_recent" else 90
            if len(filtered_args) >= 2:
                try:
                    days = int(filtered_args[1])
                except ValueError:
                    print(f"\n⚠️ 警告：参数 '{filtered_args[1]}' 不是数字，使用默认值 {days}")
            func(codes, days, source)
        elif command == "fund_detail":
            func(codes[0], source)  # fund_detail 只接受单个基金代码
        else:
            func(codes, source)
            
    except Exception as e:
        print(f"\n❌ 执行出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
