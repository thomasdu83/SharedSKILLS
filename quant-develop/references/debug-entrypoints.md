# Debug 入口脚本规范

## 目标

当用户要求“对某个函数、生成器、运行入口或模块做 debug”时，优先在目标项目的 `debug/` 目录下创建一个**最小可执行入口脚本**，用于 Trae / IDE 断点调试，而不是临时改生产入口或把调试逻辑塞进业务代码。

该类脚本的第一目标是：

- 让断点尽快打到目标位置
- 让关键中间变量可直接观察
- 让脚本能够脱离测试框架独立启动

## 何时创建

创建 `debug` 入口脚本的典型场景：

- 需要逐步观察某个 `generate()` / `run()` / `build_*()` 过程
- 需要检查原始输入、中间表和最终输出的规模异常
- 需要在 IDE 中对私有方法打断点
- 正式运行入口过重，不适合直接调试
- 需要复现实例化、数据访问、路径注入等真实运行上下文

不适合创建 `debug` 入口脚本的场景：

- 只是一次性查看某个 Parquet / SQLite 文件
- 只需要写一个临时 SQL / DataFrame 对账脚本
- 只需运行现成入口并观察日志，无需断点

## 默认放置位置

默认放在目标项目的 `debug/` 目录，例如：

- `domains/fund/fund-label-research/debug/`
- `domains/fund/etf-research-workbench/debug/`

命名建议：

- `debug_<generator_name>.py`
- `debug_<entrypoint_name>.py`
- `debug_<task_name>.py`

## 核心原则

### 1. 最小入口

保持脚本尽可能小：

- 不默认加 `argparse`
- 不默认加复杂配置系统
- 不默认加自动对账逻辑
- 不默认接入重型日志

只保留最小必要输入，例如一个：

- `run_date`
- `xdate`
- `fund_code`
- `project_id`

### 2. 路径稳定

脚本需要能直接运行，避免因为工作目录不同而导入失败。

通常要做：

- 注入项目根目录到 `sys.path`
- 必要时注入仓库根目录到 `sys.path`
- 若仓库里存在与标准库同名的包（例如 `platform`），做最小冲突处理

### 3. 断点优先

调试入口脚本不是给用户看的，它首先是给 IDE 断点服务的。

因此要：

- 将关键中间变量显式命名
- 把长链路拆成几个可单独观察的步骤
- 尽量避免把所有逻辑包进一层黑盒函数

### 4. 不污染生产逻辑

- 不要为了调试去修改生产入口的正常行为
- 不要在业务类里加入仅供 debug 使用的分支
- 不要让调试脚本反向成为生产依赖

## 默认结构

推荐使用以下结构：

```python
from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (PROJECT_ROOT, REPO_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# 如有与标准库同名的仓库包，在这里做最小兼容处理
# sys.modules.pop("platform", None)

from src.xxx import TargetClass


XDATE = "2026-04-16"


def main() -> dict[str, object]:
    target = TargetClass(...)

    raw_a = target.load_a(XDATE)
    raw_b = target.load_b(XDATE)
    step_1 = target._build_step_1(raw_a, XDATE)
    step_2 = target._build_step_2(raw_b, XDATE)
    outputs = target.generate(None, XDATE)

    debug_context = {
        "target": target,
        "raw_a": raw_a,
        "raw_b": raw_b,
        "step_1": step_1,
        "step_2": step_2,
        "outputs": outputs,
    }
    return debug_context


if __name__ == "__main__":
    DEBUG_CONTEXT = main()
```

## 变量暴露规范

优先暴露以下几类变量：

- **实例对象**
  - `generator`
  - `runner`
  - `service`
- **原始输入**
  - `fund_info`
  - `fund_type`
  - `raw_df`
- **中间结果**
  - `subject_info`
  - `complete_labels`
  - `merged_df`
- **最终输出**
  - `outputs`
  - `final_df`

命名要求：

- 使用业务语义命名
- 避免 `df1`、`tmp2`、`x` 这类无意义名字

## 何时拆分步骤

### 适合逐段拆开的情况

- 生成器内部有多个 `_build_*()` 步骤
- 需要判断是哪一步开始行数异常
- 需要观察多个输入源的规模差异

### 适合只包一层 `main()` 的情况

- 只是想给 `run_batch()`、`run_research()` 之类正式入口打断点
- 主入口内部已经足够清晰
- 不需要提前把内部步骤拆出来

例如：

- `etf-research-workbench/debug/debug_run_batch.py`
  - 适合轻量封装正式入口
- `fund-label-research/debug/debug_base_profile_generator.py`
  - 适合逐段拆开关键内部方法

## 输出规范

默认只保留轻量输出：

- 行数
- 表名
- 关键标签分布

例如：

```python
print(
    {
        "fund_info_rows": len(fund_info),
        "fund_type_rows": len(fund_type),
        "output_tables": list(outputs.keys()),
    }
)
```

这样做的目的是：

- 不打断点时也能快速确认脚本跑到哪里
- 不把控制台污染成大段 DataFrame 输出

## 常见错误

### 1. 路径注入不完整

症状：

- 直接运行脚本时报 `ModuleNotFoundError`

处理：

- 检查是否同时加入了项目根目录和仓库根目录

### 2. 仓库包名与标准库冲突

症状：

- 明明存在 `platform/` 目录，但导入到的是 Python 标准库 `platform`

处理：

- 在导入前最小化处理模块缓存，例如：

```python
sys.modules.pop("platform", None)
```

### 3. 变量全部藏在函数内部

症状：

- 断点到了以后看不到关键中间结果

处理：

- 显式保留中间变量
- 最后返回 `DEBUG_CONTEXT`

### 4. 入口做得过重

症状：

- 调试脚本变成了第二套运行系统

处理：

- 去掉 CLI、日志框架、自动报表、自动对账等非必要部分

## 选择建议

当用户只说“帮我对某个函数或模块做 debug”时，默认采用以下策略：

1. 在项目 `debug/` 目录创建入口脚本
2. 先判断是：
   - 轻量包正式入口
   - 还是逐段拆解内部步骤
3. 保持脚本最小化
4. 优先保证断点体验，而不是功能完备

## 与 `quant-develop` 的关系

这不是独立产品能力，而是量化项目开发中的辅助工作流。

因此：

- 主技能正文只保留简短触发说明
- 详细规则放在本参考文件
- 只有当用户明确提到“debug 入口”“断点调试”“调试脚本”时，再按本规范执行
