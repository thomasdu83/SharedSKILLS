# 计算与性能优化参考

QuantSystem 计算层的详细规范，包含 **Pivot-Align-Calc 三步法**、**向量化操作**、**并行处理**与**性能基准**。

---

## 0. 性能优化顺序

性能优化必须先定位，再改代码。默认顺序：

1. **打点拆分**：先把总耗时拆到 `module/label_type -> stage`，至少区分取数、样本构造、特征计算、标签/信号映射、审计和写盘。
2. **判断瓶颈类型**：区分本地计算、远端数据访问、存储写出和日志/序列化开销。
3. **消灭同一运行日重复工作**：优先处理同一 `effective_end_date` / `tradingday` 下重复读取、重复构造 universe、重复加载风格快照或持仓快照。
4. **优化结构性膨胀**：避免显式构造 `asset x category x date` 这类乘法膨胀网格，优先基于观测面板聚合。
5. **再做向量化改写**：把收益、加权收益、累计收益、分组统计中的 `groupby.apply` 改为 `agg`、`transform`、`sum`、`cumprod` 等。
6. **最后评估并行或数据访问层改造**：只有当本地热点清楚且契约稳定时，才考虑并行；若瓶颈已转为远端接口，停止本地微调。

不要先猜瓶颈。写库、并行和 pandas 细节都可能不是主矛盾。
没有 `stage` 级耗时证据，不允许进入并行改造或大面积 `groupby.apply` 改写。

### 打点字段

性能日志建议至少包含：

```yaml
run_id:
module:
label_type:
stage:
effective_end_date:
rows:
entities:
elapsed_seconds:
data_source:
remote_call_count:
cache_hit:
output_path:
```

阶段命名保持稳定，便于跨轮比较：`load_data`、`build_universe`、`load_features`、`compute`、`map_label`、`audit`、`write_output`。

### 终止条件

满足以下任一条件时，应结束当前轮本地性能优化，转为复核或重新规划：

- 单轮新增改动提速低于 10%，且绝对收益低于 5 秒；
- 最慢模块已低于事先设定的目标阈值；
- 剩余瓶颈已确认在远端数据访问、接口批量能力或架构层；
- 继续优化需要改变标签定义、时点口径、输出契约或默认数据源。

正确性、时点一致性和输出契约优先级高于提速。

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

`ffill()` 不是默认正确答案。只有当业务语义允许“上一条已知值继续有效”时才可使用；持仓、分类、标签和可见性数据必须先确认是否允许跨日延续。

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

## 1.1 时间安全检查

对标签、信号、回测和风控计算，性能优化不能替代时点核查。至少执行以下检查：

- 统一时间列的类型、精度、时区和自然日/交易日语义；
- `pivot` 前检查 `(time_key, entity_key)` 是否重复，重复键必须先解释；
- `merge_asof` 使用明确的 `on`、`by`、`direction` 和 `tolerance`；
- `merge_asof` 两侧先按时间键排序，再按实体键排序，并检查时间列单调性；
- 禁止只按实体键优先排序，例如 `sort_values([entity_key, time_key])` 后直接 `merge_asof`；
- rolling 窗口明确 `closed`、`min_periods`，需要预测时使用 `shift` 隔离当前或未来信息；
- 对每次填充、丢弃和截断记录行数变化。

```python
def prepare_asof_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    time_col: str,
    by_col: str,
    tolerance: pd.Timedelta | None = None,
) -> pd.DataFrame:
    """准备一个按历史可见性执行的 as-of join。"""
    left = left.copy()
    right = right.copy()
    left[time_col] = pd.to_datetime(left[time_col]).dt.normalize()
    right[time_col] = pd.to_datetime(right[time_col]).dt.normalize()

    left = left.sort_values([time_col, by_col])
    right = right.sort_values([time_col, by_col])

    if not left[time_col].is_monotonic_increasing:
        raise ValueError("left time key is not sorted")
    if not right[time_col].is_monotonic_increasing:
        raise ValueError("right time key is not sorted")

    return pd.merge_asof(
        left,
        right,
        on=time_col,
        by=by_col,
        direction="backward",
        tolerance=tolerance,
    )
```

`direction="forward"`、无 `tolerance` 的宽松匹配、对未来日期的 `ffill()`，都必须有业务解释和测试证据。
测试应覆盖“每个实体内部有序但全局时间键不单调”的失败场景。

---

## 2. 向量化优先（Performance First）

### 向量化 vs 循环

```python
# ✓ 正确 - 向量化
returns = nav_df.groupby('fundcode')['adjnav'].pct_change()

# ✓ 正确 - 聚合和累计计算
weighted_ret = (df["weight"] * df["return"]).groupby(df["tradingday"]).sum()
cumulative = (1 + weighted_ret).cumprod()

# ✗ 错误 - 循环（性能差几十倍）
for fund in fund_list:
    fund_data = nav_df[nav_df['fundcode'] == fund]
    returns = fund_data['adjnav'].pct_change()

# ✗ 错误 - 可聚合计算写成 apply(lambda ...)
result = df.groupby("tradingday").apply(
    lambda x: (x["weight"] * x["return"]).sum()
)
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

## 5. 结构性算法优化

优先寻找数据量被乘法放大的地方，而不是只调小参数。

常见风险：

- 显式构造 `fund x industry x date`、`asset x factor x date`、`portfolio x holding x date` 全量网格；
- 先做笛卡尔积再过滤；
- 每个标签重复构造同一个 universe；
- 每个模块重复读取同一运行日的宽表、持仓、风格快照或分类快照。

更稳的做法：

- 基于真实观测面板聚合；
- 只在业务确需补齐空组合时补网格；
- 缺失期由统计口径处理，并在审计中记录覆盖；
- 把共享输入提升为同一运行内的只读快照。

---

## 6. 缓存策略

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

### 进程内缓存

同一运行内重复读取同一 `effective_end_date`、universe、宽表或特征快照时，优先使用进程内缓存。缓存键必须包含：

- 日期或日期区间；
- 数据源类型和输入版本；
- `input_version`、`snapshot_id` 或 `schema_version`；
- universe / label_type / strategy_id 等会影响结果的业务参数；
- 是否强制刷新。

进程内缓存只解决同一次运行的重复工作，不替代持久化数据契约。缓存命中、失效和清理应写入日志。

### 失效策略

缓存必须能失效：

- 上游 SQLite/Parquet/DB 快照被写入或刷新时，清理相关缓存；
- 配置、阈值、字段映射或 universe 定义改变时，缓存键必须变化；
- 回补历史日期时，不得复用当前日期缓存；
- 发生覆盖不足、字段缺失或版本不匹配时，不得用旧缓存继续算。

“缓存提速但结果变脏”比不缓存更危险。

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

## 7. 性能监控与日志

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

性能基准只用于识别回归和热点，不应作为改变金融口径的理由。优化前先定位热点，优化后重新执行结果一致性和时点测试。

### 优化后定向验证

每轮性能优化后至少核查：

- 受影响模块的单元测试或最小回归测试；
- 优化前后输出行数、实体数、日期范围和关键分布；
- 关键标签/信号样本的一致性，尤其是严格规则、fallback 和空结果模块；
- 项目对应的静态检查，例如 `ruff`、`mypy` 或类型/契约检查；
- 优化前后的 stage 耗时对比，确认收益来自预期瓶颈。

### 瓶颈分类

- `write_output` 多数情况下不是第一优化对象；若日志显示写出为 `0.00s ~ 0.01s`，不要把优化重点放在 SQLite/Parquet 写入。
- 远端数据访问慢时，优先考虑接口批量化、请求复用、本地历史快照或数据访问层缓存，而不是继续抠 pandas。
- 本地计算慢时，优先看结构性膨胀和 `groupby.apply`，再考虑并行。
- 日志必须能解释性能改善来自哪里：少取数、少重复、少行数、向量化、缓存命中，还是并行。

---

## 8. 完整示例：组合收益计算

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

## 9. 风险平价权重计算

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
