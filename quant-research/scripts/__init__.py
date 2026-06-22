"""
Quant Research Scripts Package

将 quant_mcp 项目的功能封装为便于使用的查询脚本。

主要模块：
- fund_query: 基金数据查询
- stock_query: 股票数据查询
- index_query: 指数数据查询
- basic_query: 基础数据查询
- quick_query: 快速查询工具（推荐）

使用方法：
    # 方式1：直接运行脚本
    .venv\Scripts\python.exe quick_query.py fund_ytd 377240
    
    # 方式2：导入使用
    from .quick_query import fund_ytd, fund_compare
    fund_ytd(["377240"])
"""

__version__ = "1.0.0"
__author__ = "Thomas"
__all__ = [
    "fund_query",
    "stock_query",
    "index_query",
    "basic_query",
    "quick_query",
]
