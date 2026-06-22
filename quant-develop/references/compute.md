# 计算与性能优化参考

QuantSystem 计算层的详细规范，包含 **Pivot-Align-Calc 三步法**、**向量化操作**、**并行处理**与**性能基准**。

---

## 1. Pivot-Align-Calc 三步法

### 核心工作流

```python
# 1) Pivot：宽表转换
# Index=Date, Columns=EntityID
nav_wide = nav_df.pivot(index='tradingday', columns='fundcode', values='adjnav')

# 2) Align：日期对齐填充
# 对齐到交易日历
nav_aligned = nav_wide.reindex(trading_days)  # 引入缺失日
nav_filled = nav_aligned.ffill()  # 前向填充缺失值

# 3) Calc：向量化计算
# 计算收益率
returns = nav_filled.pct_change()
cumulative = (1 + returns).cumprod()
```

### 日期对齐策略详解

**明确日历类型**:
- 自然日（Calendar Days）
- 交易日（Trading Days）

**填充策略选择**:
- `ffill()` - 前向填充（最常用）
- 保留 `NaN` - 标记缺失
- `dropna()` - 丢弃缺失

```python
def align_to_trading_days(
    df: pd.DataFrame,
    trading_days: pd.DatetimeIndex,
    fill_method: str = "ffill",
) -> pd.DataFrame:
    """将数据对齐到交易日历。
    
    Args:
        df: 宽表数据（Index=Date, Columns=EntityID）
        trading_days: 交易日序列
        fill_method: 填充方式 ["ffill", "nan", "drop"]
    
    Returns:
        对齐后的DataFrame
    
    Raises:
        ValueError: 不支持的填充方式
    """
    df_aligned = df.reindex(trading_days)
    
    if fill_method == "ffill":
        return df_aligned.ffill()
    elif fill_method == "nan":
        return df_aligned
    elif fill_method == "drop":
        return df_aligned.dropna()
    else:
        raise ValueError(f"Unknown fill_method: {fill_method}")
```

---

## 2. 向量化优先（Performance First）

### 向量化 vs 循环

```python
# ✓ 正确 - 向量化
returns = nav_df.groupby('fundcode')['adjnav'].pct_change()

# ✗ 错误 - 循环（性能差几十倍）
for fund in fund_list:
    fund_data = nav_df[nav_df['fundcode'] == fund]
    returns = fund_data['adjnav'].pct_change()
```

### 允许循环的例外场景

**仅在以下场景**允许循环（需注释说明）:

#### 1. 状态依赖的日级回测/模拟

```python
def simulate_daily_rebalance(nav_df: pd.DataFrame, weight_df: pd.DataFrame):
    """逐日模拟再平衡，状态依赖必须循环。
    
    说明: 每日组合价值依赖前一日状态，无法向量化。
    循环规模: ~250 交易日/年 × 5年 = 1250次迭代
    """
    portfolio_value = initial_value
    for date in trading_days:
        # 基于前日状态计算...
        portfolio_value = update(portfolio_value, nav_df.loc[date], ...)
```

#### 2. 方案/配置级别循环（循环体本身很重）

```python
def process_schemes(scheme_list: list[dict]):
    """处理方案列表。
    
    说明: 每个方案 < 20个，循环体耗时远大于循环开销。
    循环规模: 20个方案，单方案耗时~5s
    """
    for scheme in scheme_list:  # <= 20 schemes
        result = process_scheme(scheme)
```

---

## 3. 多进程并行（Scheme/Task Level）

### 标准并行模板

```python
from concurrent.futures import ProcessPoolExecutor
from typing import Any
import logging

logger = logging.getLogger(__name__)

# Worker必须是模块级函数（非@staticmethod）
def worker_process_scheme(params: dict[str, Any]) -> dict[str, Any]:
    """独立Worker，接收可序列化参数。
    
    Args:
        params: 序列化参数包 {"scheme_id": "...", "config": {...}}
    
    Returns:
        处理结果字典
    """
    # 在进程内部创建资源，避免跨进程共享
    builder = SchemeBuilder(params["config"])
    result = builder.run()
    return {"scheme_id": params["scheme_id"], "result": result}


def run_parallel(
    scheme_configs: list[dict],
    n_workers: int | None = None,
) -> list[dict]:
    """并行处理多个方案。
    
    Args:
        scheme_configs: 方案配置列表
        n_workers: 进程数，None时使用全部CPU核心
    
    Returns:
        处理结果列表
    """
    params_list = [
        {"scheme_id": cfg["scheme_id"], "config": cfg}
        for cfg in scheme_configs
    ]
    
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(worker_process_scheme, params_list))
    
    logger.info("Parallel completed: %d schemes", len(results))
    return results
```

### Worker 设计规范

**必须遵守**:
- 必须是**模块级函数**（非 `@staticmethod`）
- 参数必须是**可序列化**的（dict/tuple/str 等）
- 进程内独立**创建所有资源**（数据库连接、文件句柄等）

**反模式**:
```python
# ✗ 错误 - 实例方法不可作为worker
class Processor:
    def process(self, scheme):  # 无法pickle
        ...
executor.map(self.process, schemes)  # 会失败

# ✗ 错误 - 传递不可序列化对象
class DataSource:
    def __init__(self, connection):
        self.conn = connection  # 数据库连接不可序列化
executor.map(worker, [data_source] * 10)  # 会失败
```

---

## 4. 并行写入隔离

### 每个Worker写独立表/文件

**原则**: 并行写入时**每个进程写独立目标**，主进程合并。

```python
def worker_save_scheme(params: dict) -> dict:
    """Worker：计算并保存到独立表。"""
    scheme_id = params["scheme_id"]
    result = compute(params)
    
    # 每个方案写独立表
    table_name = f"scheme_{scheme_id}_result"
    db.write(result, table_name)
    
    return {"scheme_id": scheme_id, "table": table_name}


def merge_results(worker_results: list[dict]):
    """主进程：合并各Worker结果。"""
    for res in worker_results:
        table = res["table"]
        df = db.read(table)
        # 合并逻辑...
```

**反模式**:
```python
# ✗ 错误 - 多进程写同一张表（竞争条件）
def worker_append(params):
    result = compute(params)
    db.append(result, "shared_table")  # 可能数据丢失或锁死
```

---

## 5. 缓存策略

### Pickle 本地缓存

```python
from pathlib import Path
import pickle
import logging

logger = logging.getLogger(__name__)

def load_with_cache(
    cache_path: Path,
    loader_func: callable,
    force_reload: bool = False,
) -> pd.DataFrame:
    """带缓存的数据加载。
    
    Args:
        cache_path: 缓存文件路径
        loader_func: 原始加载函数
        force_reload: 是否强制重新加载
    
    Returns:
        加载的DataFrame
    """
    if not force_reload and cache_path.exists():
        logger.info("Loading from cache: %s", cache_path)
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    
    logger.info("Loading from source...")
    data = loader_func()
    
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(data, f)
    logger.info("Cached to: %s", cache_path)
    
    return data
```

### SQLite 增量更新

```python
def upsert_to_sqlite(
    df: pd.DataFrame,
    table_name: str,
    unique_constraints: list[str],
    db_path: Path,
):
    """增量更新到SQLite（幂等操作）。
    
    Args:
        df: 要写入的数据
        table_name: 表名
        unique_constraints: 唯一约束列
        db_path: 数据库路径
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    
    # 创建表（如不存在）
    df.head(0).to_sql(table_name, conn, if_exists="ignore", index=False)
    
    # 创建唯一索引
    idx_name = f"idx_{table_name}_{'_'.join(unique_constraints)}"
    cols = ", ".join(unique_constraints)
    conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {idx_name} ON {table_name}({cols})")
    
    # INSERT OR REPLACE
    df.to_sql(table_name, conn, if_exists="append", index=False, method="multi")
    
    conn.commit()
    conn.close()
```

---

## 6. 性能监控与日志

### 计算耗时日志

```python
import time
import logging

logger = logging.getLogger(__name__)

def compute_with_logging(df: pd.DataFrame, n_entities: int):
    """带性能日志的计算函数。"""
    start_time = time.time()
    
    # 核心计算
    result = df.groupby('entity').apply(expensive_calc)
    
    elapsed = time.time() - start_time
    logger.info(
        "Compute completed | entities=%d | rows=%d | elapsed=%.2fs",
        n_entities, len(df), elapsed
    )
    
    # 性能预警
    if elapsed > 300 and n_entities < 100:
        logger.warning(
            "Performance issue: %d entities took %.2fs (expected <60s)",
            n_entities, elapsed
        )
    
    return result
```

### 性能基准参考

| 操作 | 典型规模 | 期望耗时 |
|------|---------|---------|
| 单基金净值计算 | 1000日 | <0.1s |
| 100基金组合回测 | 1000日×100 | <5s |
| 单方案完整构建 | 500日×50基金 | <10s |
| 10方案并行构建 | 500日×50基金 | <60s |

---

## 7. 完整示例：组合收益计算

```python
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_portfolio_return(
    nav_df: pd.DataFrame,
    weight_df: pd.DataFrame,
    trading_days: pd.DatetimeIndex,
) -> pd.Series:
    """计算组合收益（Pivot-Align-Calc模式）。
    
    Args:
        nav_df: 净值数据（列: tradingday, fundcode, adjnav）
        weight_df: 权重数据（列: tradingday, fundcode, weight）
        trading_days: 交易日序列
    
    Returns:
        组合日收益序列
    
    Raises:
        ValueError: 权重未归一化
    """
    # 1. Pivot：转为宽表
    nav_wide = nav_df.pivot(
        index='tradingday',
        columns='fundcode',
        values='adjnav'
    )
    weight_wide = weight_df.pivot(
        index='tradingday',
        columns='fundcode',
        values='weight'
    )
    
    # 2. Align：对齐到交易日
    nav_aligned = nav_wide.reindex(trading_days).ffill()
    weight_aligned = weight_wide.reindex(trading_days).ffill()
    
    # 验证权重归一化
    weight_sum = weight_aligned.sum(axis=1)
    if not np.allclose(weight_sum, 1.0, atol=0.01):
        raise ValueError("Weight sum != 1.0")
    
    # 3. Calc：向量化计算
    nav_ret = nav_aligned.pct_change()
    portfolio_ret = (nav_ret * weight_aligned).sum(axis=1)
    
    logger.info(
        "Portfolio return calculated | days=%d | funds=%d",
        len(trading_days), len(nav_wide.columns)
    )
    
    return portfolio_ret
```

---

## 8. 风险平价权重计算

```python
def calculate_risk_parity_weights(
    returns: pd.DataFrame,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> pd.Series:
    """计算风险平价权重。
    
    Args:
        returns: 收益率矩阵（Index=Date, Columns=Asset）
        max_iterations: 最大迭代次数
        tolerance: 收敛容差
    
    Returns:
        权重序列（Index=Asset）
    """
    cov_matrix = returns.cov()
    n_assets = len(cov_matrix)
    
    # 初始等权
    weights = np.ones(n_assets) / n_assets
    
    for _ in range(max_iterations):
        # 边际风险贡献
        portfolio_var = weights @ cov_matrix @ weights
        marginal_risk = cov_matrix @ weights
        risk_contribution = weights * marginal_risk / np.sqrt(portfolio_var)
        
        # 目标：等风险贡献
        target_rc = np.sqrt(portfolio_var) / n_assets
        
        # 调整权重
        weights_new = weights * (target_rc / risk_contribution)
        weights_new = np.clip(weights_new, 0.01, 0.5)  # 约束
        weights_new = weights_new / weights_new.sum()  # 归一化
        
        # 检查收敛
        if np.max(np.abs(weights_new - weights)) < tolerance:
            break
        
        weights = weights_new
    
    return pd.Series(weights, index=cov_matrix.columns)
```
