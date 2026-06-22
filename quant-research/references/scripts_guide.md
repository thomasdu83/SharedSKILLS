# 脚本指南与参考

本文件合并了以下三份文档，作为统一入口：
- `references/script_reference.md`
- `scripts/GUIDE_ADD_FUNCTIONS.md`
- `scripts/GUIDE_DATA_CALCULATION.md`

## 数据源选择策略

### 数据源对比

| 数据源     | 适用场景                                 | 优点                   | 缺点                         |
| ---------- | ---------------------------------------- | ---------------------- | ---------------------------- |
| **sqlite** | 日常查询、历史分析、回测、大多数研究场景 | 速度快、离线可用、稳定 | 数据可能滞后1-2天            |
| **db**     | 需要最新数据、实时分析、近期交易确认     | 数据最全最新           | 需要网络、速度较慢、可能超时 |
| **excel**  | 数据导出、手动编辑、分享给非技术人员     | 便于分享、可离线编辑   | 功能有限、数据量受限         |

### 决策规则

1. **默认使用 `sqlite`**（90% 场景）
   - 用户未特别说明时
   - 历史数据分析、业绩回顾
   - 回测、策略研究

2. **使用 `db`** 当：
   - 用户明确要求"最新数据"或"实时数据"
   - 涉及最近1-2天的交易数据
   - sqlite 查询返回空或数据明显过时

3. **使用 `excel`** 当：
   - 用户需要导出数据给其他人
   - 需要手动编辑或补充数据
   - 特殊报表格式需求

### 代码示例

```python
from data_management.core import FundData, SqliteSource, DBSource, ExcelSource

# 默认（sqlite）
fund_data = FundData(SqliteSource(update=False))

# 需要最新数据（db）
fund_data = FundData(DBSource(update=False))

# 导出用途（excel）
fund_data = FundData(ExcelSource(update=False))
```

## 查询脚本使用

### 快速查询工具示例

#### 基金查询

```bash
# 基金年初至今收益
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py fund_ytd 377240

# 对比多只基金
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py fund_compare 377240,000001

# 查询基金详情
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py fund_detail 377240
```

#### 指数查询

```bash
# 查询指数表现
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py index_ytd 000300,000905
```

#### 股票查询

```bash
# 查询股票信息
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py stock_info 600519
```

#### 查看帮助

```bash
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py help
```

### 完整功能脚本

如果需要更复杂的查询，使用功能完整的脚本：

```bash
# 基金查询（交互式菜单）
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\fund_query.py

# 股票查询（交互式菜单）
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\stock_query.py

# 指数查询（交互式菜单）
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\index_query.py
```

命令行快捷方式：

```bash
# 基金业绩分析（12个月）
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\fund_query.py performance 377240 12

# 股票风格分析
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\stock_query.py style 600519

# 指数对比
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\index_query.py compare 000300,000905
```

### 传统方式（备用）

当预置脚本不满足需求时，可以创建临时脚本：

```python
# query_script.py
from main_config import add_project_path_to_sys
add_project_path_to_sys()

from data_management.core import FundData, SqliteSource

fund_data = FundData(SqliteSource(update=False))
df = fund_data.fund_ret(
    fund_codes=["377240"],
    start_date="2024-01-01",
    end_date="2024-12-31"
)
print(df.to_markdown(index=False))  # 打印 Markdown 格式
# df 是 DataFrame，可直接用于计算
```

运行命令：`.venv\Scripts\python.exe query_script.py`

### 常见错误与解决方案

| 错误                                                     | 原因                     | 解决方案                        |
| -------------------------------------------------------- | ------------------------ | ------------------------------- |
| `ModuleNotFoundError: No module named 'data_management'` | 使用了系统 Python        | 使用 `.venv\Scripts\python.exe` |
| `ModuleNotFoundError: No module named 'sqlalchemy'`      | 缺少依赖或未激活虚拟环境 | 使用虚拟环境 Python             |
| PowerShell `&&` 错误                                     | PowerShell 不支持 `&&`   | 分步执行或使用分号 `;`          |

### 快捷命令参考

```bash
# 使用预置脚本（推荐）
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py <命令> <参数>

# 创建临时脚本（备用）
.venv\Scripts\python.exe query_fund.py

# 查看虚拟环境 Python 版本
.venv\Scripts\python.exe --version

# 查看已安装的包
.venv\Scripts\pip.exe list
```

## 新增函数开发指南

本指南介绍如何在 `quant-research/scripts` 中添加新的查询函数。

### 架构说明

所有脚本**直接使用 `data_management` 核心模块**，与 `quant_mcp` 完全隔离。

```
data_management.core
    ├── FundData      # 基金数据
    ├── StockData     # 股票数据
    ├── IndexData     # 指数数据
    ├── BasicData     # 基础数据
    ├── SqliteSource  # SQLite 数据源
    ├── DBSource      # 数据库数据源
    └── ExcelSource   # Excel 数据源
```

### 添加新函数的步骤

#### 1. 确定函数位置

根据数据类型选择对应的脚本：

| 数据类型 | 脚本文件 | 数据类 |
|---------|---------|--------|
| 基金相关 | `fund_query.py` | `FundData` |
| 股票相关 | `stock_query.py` | `StockData` |
| 指数相关 | `index_query.py` | `IndexData` |
| 基础数据 | `basic_query.py` | `BasicData` |
| 快捷功能 | `quick_query.py` | 多种 |

#### 2. 查找可用方法

在 `data_management.core` 中查找数据类的可用方法：

```python
# FundData 常用方法
fund_data.fund_ret()           # 基金收益率
fund_data.fund_quote()         # 基金净值
fund_data.fund_id()            # 基金ID信息
fund_data.fund_pm()            # 基金经理
fund_data.fund_scale()         # 基金规模
fund_data.fund_stock()         # 基金持仓
fund_data.fund_asset()         # 资产配置
fund_data.fund_periodic_return()  # 周期收益率

# StockData 常用方法
stock_data.stock_quote()       # 股票行情
stock_data.stock_industry()    # 行业分类
stock_data.stock_cap()         # 市值数据
stock_data.stock_style()       # 风格因子
stock_data.stock_barra_factor() # Barra因子
stock_data.stock_periodic_return() # 周期收益率

# IndexData 常用方法
index_data.index_list()        # 指数列表
index_data.index_quote()       # 指数行情
index_data.index_periodic_return() # 周期收益率
```

#### 3. 编写新函数

标准模板：

```python
def query_新功能名称(参数列表, source: str = "sqlite"):
    """
    功能说明
    
    Args:
        参数说明
        source: 数据源，默认 "sqlite"
    
    Returns:
        pd.DataFrame: 返回数据
    """
    # 打印查询信息
    print(f"\n{'='*60}")
    print(f"查询标题")
    print(f"参数信息: ...")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    # 获取数据实例
    data_obj = _get_xxx_data(source)  # 使用对应的辅助函数
    
    # 调用数据方法
    df = data_obj.xxx_method(参数...)
    
    # 处理结果
    if df is None or df.empty:
        print("⚠️ 未找到数据")
        return None
    
    # 打印 Markdown 格式
    print(_format_to_markdown(df, "标题"))
    
    # 返回 DataFrame（用于计算）
    return df
```

实际示例：

```python
def query_fund_drawdown(fund_codes: list[str], months: int = 12, source: str = "sqlite"):
    """
    查询基金最大回撤
    
    Args:
        fund_codes: 基金代码列表
        months: 分析月数
        source: 数据源
    
    Returns:
        pd.DataFrame: 回撤数据
    """
    print(f"\n{'='*60}")
    print(f"查询基金最大回撤")
    print(f"基金代码: {', '.join(fund_codes)}")
    print(f"分析周期: {months} 个月")
    print(f"数据源: {source}")
    print(f"{'='*60}\n")
    
    fund_data = _get_fund_data(source)
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    # 获取净值数据
    df_quote = fund_data.fund_quote(fund_codes, start_date, end_date)
    
    if df_quote is None or df_quote.empty:
        print("⚠️ 未找到数据")
        return None
    
    # 计算最大回撤
    results = []
    for code in fund_codes:
        df_fund = df_quote[df_quote['fund_code'] == code].copy()
        if df_fund.empty:
            continue
        
        df_fund = df_fund.sort_values('trade_date')
        df_fund['cummax'] = df_fund['nav'].cummax()
        df_fund['drawdown'] = (df_fund['nav'] - df_fund['cummax']) / df_fund['cummax']
        max_drawdown = df_fund['drawdown'].min()
        
        results.append({
            'fund_code': code,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': f"{max_drawdown:.2%}"
        })
    
    df_result = pd.DataFrame(results)
    
    print(_format_to_markdown(df_result, "最大回撤"))
    return df_result
```

#### 4. 添加到菜单（可选）

在 `main()` 函数的交互式菜单中添加新选项：

```python
def main():
    # ...
    print("7. 基金最大回撤")  # 添加新选项
    # ...
    
    if choice == "7":
        query_fund_drawdown(fund_codes, source=source)
```

#### 5. 添加命令行支持（可选）

在 `if __name__ == "__main__"` 部分添加命令行参数解析：

```python
elif command == "drawdown" and len(sys.argv) >= 3:
    fund_codes = sys.argv[2:]
    query_fund_drawdown(fund_codes)
```

#### 6. 添加到 quick_query.py（可选）

如果是常用功能，添加到 `quick_query.py` 的 `COMMANDS` 字典：

```python
COMMANDS = {
    # ... 现有命令 ...
    "fund_drawdown": {
        "func": fund_drawdown,
        "desc": "查询基金最大回撤",
        "usage": "quick_query.py fund_drawdown <基金代码>",
        "example": "quick_query.py fund_drawdown 377240",
    },
}
```

### 辅助函数

所有脚本都包含以下辅助函数：

```python
def _get_xxx_data(source: str):
    """获取数据实例"""
    if source == "sqlite":
        return XxxData(SqliteSource(update=False))
    elif source == "db":
        return XxxData(DBSource(update=False))
    elif source == "excel":
        return XxxData(ExcelSource(update=False))
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
```

### 最佳实践

#### 1. 返回值

- **始终返回 DataFrame**：便于后续计算
- **同时打印 Markdown**：便于人工查看

#### 2. 错误处理

```python
try:
    df = fund_data.some_method(...)
    if df is not None and not df.empty:
        print(_format_to_markdown(df, "标题"))
        result['key'] = df
except Exception as e:
    print(f"⚠️ 获取数据失败: {e}")
```

#### 3. 日期处理

```python
from datetime import datetime, timedelta

today = datetime.now().strftime("%Y-%m-%d")
year_start = f"{datetime.now().year}-01-01"
last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
```

#### 4. 数据格式化

```python
# 百分比格式
df['ret_pct'] = df['ret'].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")

# 日期格式
df['date_fmt'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

# 数值格式
df['value_fmt'] = df['value'].apply(lambda x: f"{x:,.2f}")
```

### 测试新函数

```bash
# 运行脚本测试
.venv\Scripts\python.exe fund_query.py

# 或直接调用函数测试
.venv\Scripts\python.exe -c "
from fund_query import query_fund_drawdown
query_fund_drawdown(['377240'], 12)
"
```

### 注意事项

1. **必须使用虚拟环境**：`.venv\Scripts\python.exe`
2. **导入顺序**：先导入 `main_config`，再导入 `data_management`
3. **参数验证**：对输入参数进行基本验证
4. **异常处理**：使用 try-except 捕获可能的错误
5. **文档更新**：新增功能后更新 `scripts/README.md`

## 数据计算指南

本指南介绍如何使用 `quant-research/scripts` 返回的 DataFrame 进行数据计算。

### 架构优势

所有脚本直接使用 `data_management` 核心模块，返回原生 Pandas DataFrame：

- ✅ **可直接计算**：无需解析 Markdown 字符串
- ✅ **类型明确**：数值类型保持原样
- ✅ **链式操作**：支持 Pandas 所有操作
- ✅ **高效处理**：避免字符串转换开销

### 基本用法

#### 1. 直接获取 DataFrame

```python
from data_management.core import FundData, SqliteSource

# 创建数据实例
fund_data = FundData(SqliteSource(update=False))

# 查询数据 - 返回 DataFrame
df = fund_data.fund_ret(["377240", "000001"], "2025-01-01", "2025-12-31")

# 直接使用
print(df.head())
print(df.dtypes)
```

#### 2. 使用脚本函数

```python
from scripts.quick_query import fund_ytd, fund_compare

# 查询 YTD 收益 - 返回 DataFrame
df = fund_ytd(["377240"])

# 对比基金 - 返回 dict[str, DataFrame]
result = fund_compare(["377240", "000001"])
df_ret = result['return']
df_info = result['info']
```

### 常用计算示例

#### 1. 收益率计算

```python
from data_management.core import FundData, SqliteSource
from datetime import datetime, timedelta

fund_data = FundData(SqliteSource(update=False))

# 获取多只基金收益率
fund_codes = ["377240", "000001", "110011"]
df = fund_data.fund_ret(fund_codes, "2025-01-01", "2025-12-31")

if df is not None and 'ret' in df.columns:
    # 基础统计
    print(f"平均收益率: {df['ret'].mean():.4f}")
    print(f"最大收益率: {df['ret'].max():.4f}")
    print(f"最小收益率: {df['ret'].min():.4f}")
    print(f"收益率标准差: {df['ret'].std():.4f}")
    
    # 排名
    df_ranked = df.sort_values('ret', ascending=False)
    print("\n收益排名:")
    print(df_ranked)
```

#### 2. 基金对比分析

```python
def compare_funds_detailed(fund_codes: list, start_date: str, end_date: str):
    """详细对比多只基金"""
    from data_management.core import FundData, SqliteSource
    import pandas as pd
    
    fund_data = FundData(SqliteSource(update=False))
    
    results = []
    for code in fund_codes:
        # 获取净值数据
        df = fund_data.fund_quote([code], start_date, end_date)
        if df is None or df.empty:
            continue
        
        df = df.sort_values('trade_date')
        
        # 计算指标
        total_return = (df['nav'].iloc[-1] / df['nav'].iloc[0]) - 1
        daily_ret = df['nav'].pct_change()
        volatility = daily_ret.std() * np.sqrt(252)
        
        # 最大回撤
        cummax = df['nav'].cummax()
        drawdown = (df['nav'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        results.append({
            'fund_code': code,
            'total_return': total_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe': (total_return - 0.03) / volatility if volatility > 0 else 0
        })
    
    df_result = pd.DataFrame(results)
    
    # 格式化显示
    df_display = df_result.copy()
    df_display['total_return'] = df_display['total_return'].apply(lambda x: f"{x:.2%}")
    df_display['volatility'] = df_display['volatility'].apply(lambda x: f"{x:.2%}")
    df_display['max_drawdown'] = df_display['max_drawdown'].apply(lambda x: f"{x:.2%}")
    df_display['sharpe'] = df_display['sharpe'].apply(lambda x: f"{x:.2f}")
    
    print(df_display.to_markdown(index=False))
    
    return df_result

# 使用
df = compare_funds_detailed(["377240", "000001"], "2024-01-01", "2025-01-19")
```

#### 3. 行业持仓分析

```python
def analyze_fund_holdings(fund_code: str, report_date: str):
    """分析基金行业持仓"""
    from data_management.core import FundData, StockData, SqliteSource
    
    source = SqliteSource(update=False)
    fund_data = FundData(source)
    stock_data = StockData(source)
    
    # 获取基金持仓
    df_holdings = fund_data.fund_stock([fund_code], report_date, report_date)
    
    if df_holdings is None or df_holdings.empty:
        print("未找到持仓数据")
        return None
    
    # 获取股票行业信息
    stock_codes = df_holdings['stock_code'].unique().tolist()
    df_industry = stock_data.stock_industry(stock_codes, report_date)
    
    if df_industry is None:
        return df_holdings
    
    # 合并数据
    df_merged = df_holdings.merge(
        df_industry[['stock_code', 'industry']],
        on='stock_code',
        how='left'
    )
    
    # 按行业汇总
    df_summary = df_merged.groupby('industry')['weight'].sum().reset_index()
    df_summary = df_summary.sort_values('weight', ascending=False)
    
    print("\n【行业持仓分布】")
    print(df_summary.to_markdown(index=False))
    
    return df_summary

# 使用
analyze_fund_holdings("377240", "2024-06-30")
```

### 数据处理技巧

#### 1. 日期处理

```python
import pandas as pd

# 字符串转日期
df['date'] = pd.to_datetime(df['date'])

# 日期格式化
df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

# 筛选日期范围
mask = (df['date'] >= '2024-01-01') & (df['date'] <= '2024-12-31')
df_filtered = df[mask]

# 按月/季度重采样
df_monthly = df.set_index('date').resample('M').last()
```

#### 2. 数据聚合

```python
# 按基金分组计算
df_grouped = df.groupby('fund_code').agg({
    'ret': ['mean', 'std', 'min', 'max'],
    'nav': 'last'
})

# 排名
df['rank'] = df['ret'].rank(ascending=False)

# 分位数
df['quantile'] = pd.qcut(df['ret'], q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
```

#### 3. 合并数据

```python
# 合并基金信息和收益率
df_merged = df_ret.merge(df_info, on='fund_code', how='left')

# 添加基准收益
df['excess_ret'] = df['ret'] - df['benchmark_ret']
```

### 输出格式化

#### 1. 百分比格式

```python
df['ret_pct'] = df['ret'].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
```

#### 2. 数值格式

```python
df['value_fmt'] = df['value'].apply(lambda x: f"{x:,.2f}")
```

#### 3. Markdown 输出

```python
def _format_to_markdown(df, title=None):
    if df is None or df.empty:
        return "未找到数据"
    result = ""
    if title:
        result += f"\n【{title}】\n"
    result += df.to_markdown(index=False)
    return result

print(_format_to_markdown(df, "分析结果"))
```

### 最佳实践

1. **保留原始数据**：计算时使用 `df.copy()` 避免修改原数据
2. **处理空值**：使用 `pd.notna()` 检查空值
3. **类型检查**：确保数值列是正确的类型
4. **日期标准化**：统一使用 `YYYY-MM-DD` 格式
5. **错误处理**：使用 try-except 捕获异常

---

**最后更新**：2026-01-19
