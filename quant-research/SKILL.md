---
name: quant-research
description: Use for FOHF investment research that requires dual-source verification: Obsidian notes plus quantitative scripts. Trigger for strategy/team/performance interpretation, fund research synthesis, note maintenance, or fact-checking claims against data. For simple private-fund manager/product lookup, product terms, contracts, NAV retrieval, or entity disambiguation via business APIs, use wisdom-manager-product-research instead.
---
# Quant Research - Investment Research Partner

本 skill 用于投资研究任务，将定性逻辑（Obsidian 笔记）与定量数据（data_management）结合。

> **架构说明**：`scripts/` 文件夹中的脚本直接使用 `data_management` 核心模块，返回 Pandas DataFrame 用于计算。

## 与 manager/product 查询技能的边界

- 只查私募管理人、产品要素、合同、产品净值、管理人旗下产品或实体消歧时，使用 `wisdom-manager-product-research`。
- 需要把笔记中的策略/团队/投研判断与真实业绩、规模、持仓等数据交叉验证时，使用本技能。
- 若任务先需要 API 查事实、再写投研判断，先用 `wisdom-manager-product-research` 取数，再用本技能做综合分析。

## 核心原则：双源验证协议

**所有回答必须遵循以下决策路由，严禁通过幻觉生成数据：**

- **定性问题（策略/团队/逻辑）** → **必须**优先调用 MCP `obsidian-knowledge`
  - Action: `search_notes` → `read_note`（完整读取，不可只看摘要）

- **定量问题（业绩/规模/持仓）** → **必须**使用预置脚本查询
  - Action: 使用 `scripts/quick_query.py` 或其他预置脚本
  - Constraint: 严禁使用笔记中过时的静态数据回答当前的业绩问题

- **混合分析（研报/复盘）** → **先查后算**
  - 先查笔记建立定性框架，再拉取数据填充最新表现

## 工具调用规范

### 知识库工具（Obsidian MCP）

- **search_notes**: 第一步，优先使用 `obsidian-knowledge` MCP
- **read_note**: 必须解析 Frontmatter（YAML）和 Wikilinks
  - 注意：遇到 `dataview` 代码块，需手动转译为搜索指令执行，不可试图读取渲染结果

### 量化工具（Scripts）

**关键要求**：所有 Python 脚本必须使用项目虚拟环境运行。

```bash
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py fund_ytd 377240
```

- **虚拟环境**: 项目根目录的 `.venv` 文件夹
- **禁止**: 不要使用系统全局 Python，会导致模块找不到错误
- **数据源**: 默认 `sqlite`，仅当强调"最新/实时"时用 `db`
- **输出**: 脚本输出 Markdown 表格，需在下方用一句话总结

> 📚 详细数据源选择策略和脚本示例见 [references/scripts_guide.md](references/scripts_guide.md)

### 实体映射（Entity Resolution）

- **严禁猜测代码**
- 当用户提到中文名称（如"千象卓越"）但未提供代码时：
  1. 先调用 `search_notes "千象卓越"` 找到对应笔记
  2. 读取笔记 YAML 中的 `fund_code` 字段
  3. 使用提取的代码调用预置脚本

## 核心工作流

### 工作流 1：事实核查（Fact Check）

**场景**：用户问"笔记里说这只基金回撤控制好，真的吗？"

**步骤**：
1. `read_note`: 找到笔记中提到的时间段
2. 使用预置脚本: 拉取该时段真实数据
3. **Compare**: 对比观点与数据。若数据与笔记冲突，**加粗**提示风险

### 工作流 2：动态研报（Dynamic Report）

**场景**：用户说"分析 [[九坤日享]]"

**步骤**：
1. **定性**: 读取笔记，提取策略逻辑、风控条款
2. **定量**: 使用预置脚本拉取今年以来业绩、最大回撤
3. **合成**: 撰写报告，定性部分引用 `[[笔记]]`，定量部分插入数据表格
4. **存档**: 执行下方「文件保存检查清单」

### 工作流 3：内容维护（Maintenance）

**场景**：创建或更新投资笔记

**步骤**：
- **新建笔记**: 自动将正文中的已知实体转为 `[[Wikilinks]]`
- **补全元数据**: 若笔记 YAML 缺失 `fund_code`，主动查询并建议补全

## 文件保存检查清单（强制执行）

**在执行笔记保存或生成长文档前，必须自我审查以下 5 点：**

1. **路径强制**: 目标必须是 `knowledge/Research/30_Synthesis_Notes/My_Insights/`
   - 禁止保存到 `Diligence` 或 `Entities` 等原始资料文件夹
2. **Tags 必填**: 必须询问用户 `tags`。若无回复，默认为 `tags: [my_insights]`
3. **YAML 完整**: 必须包含 `title`, `date`, `tags`。若是基金笔记，必须包含 `fund_code`
4. **Wikilinks**: 正文中所有已知实体必须转换为 `[[ ]]` 格式
5. **命名规范**: `主题描述_YYYY-MM-DD.md`

## 示例场景

**场景 A：业绩查询**

```
用户："千象卓越今年表现怎么样？"
→ search_notes("千象卓越") 
→ read_note 获取 fund_code
→ .venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py fund_ytd 377240
→ 返回表格 + 一句话总结
```

**场景 B：策略分析**

```
用户："这只基金的策略是什么？"
→ search_notes(基金名称)
→ read_note 获取策略描述、团队信息
→ 返回笔记中的定性分析
```

**场景 C：综合研报**

```
用户："写一份 XX 基金的研报"
→ 1. read_note 获取定性信息（策略、团队、风控）
→ 2. 使用预置脚本获取定量数据（收益、回撤、波动）
→ 3. 合成报告（定性+定量）
→ 4. 执行文件保存检查清单
```

## 脚本架构

### 分层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    quick_query.py                           │
│                   （命令行入口层）                            │
│    - 解析命令行参数                                          │
│    - 调用核心脚本函数                                        │
│    - 统一的命令行接口                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓ 调用
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ fund_query   │ index_query  │ stock_query  │ basic_query  │
│   基金核心    │   指数核心    │   股票核心    │   基础数据    │
│              │              │              │              │
│ 可被其他脚本  │ 可被其他脚本  │ 可被其他脚本  │ 可被其他脚本  │
│ 或 Notebook  │ 或 Notebook  │ 或 Notebook  │ 或 Notebook  │
│   复用       │   复用       │   复用       │   复用       │
└──────────────┴──────────────┴──────────────┴──────────────┘
                              ↓ 使用
┌─────────────────────────────────────────────────────────────┐
│                   data_management.core                      │
│                   （数据访问层）                              │
└─────────────────────────────────────────────────────────────┘
```

### 脚本文件分工

| 脚本文件 | 职责 | 核心函数示例 |
|---------|------|------------|
| `fund_query.py` | 基金数据查询 | `query_fund_ytd_return`, `query_fund_period_return` |
| `index_query.py` | 指数数据查询 | `query_index_ytd_quote`, `compare_index_performance` |
| `stock_query.py` | 股票数据查询 | `query_stock_latest_info`, `query_stock_price_history` |
| `basic_query.py` | 基础数据查询 | 日期矩阵、证券主表等 |
| **`quick_query.py`** | **命令行入口** | 解析参数，调用上述核心函数 |

### 使用方式

**方式 1：命令行（推荐）**

```bash
# 查看所有可用命令
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py help

# 基金查询
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py fund_ytd 377240
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py fund_period 377240 2024-01-01 2024-01-31

# 指数查询
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py index_ytd 000300,000905

# 股票查询
.venv\Scripts\python.exe .claude\skills\quant-research\scripts\quick_query.py stock_info 600519
```

**方式 2：在 Python/Notebook 中复用**

```python
# 可以直接导入核心函数使用
from fund_query import query_fund_period_return
df = query_fund_period_return(['377240'], '2024-01-01', '2024-06-30')
# 继续用 df 做分析...
```

### 添加新函数（强制流程）

**⚠️ 禁止直接使用 MCP 工具查询数据！** 当预置脚本不满足需求时，必须：

```
步骤 1: 在核心脚本添加函数
        fund_query.py → query_fund_xxx()

步骤 2: 在 quick_query.py 添加包装函数和注册命令
        def fund_xxx():
            return query_fund_xxx()
        
        COMMANDS["fund_xxx"] = {...}

步骤 3: 使用命令行调用
        .venv\Scripts\python.exe quick_query.py fund_xxx ...
```

参考文档：
- [references/scripts_guide.md](references/scripts_guide.md) - 新增函数与数据计算指南

**脚本规范要求**：
1. 直接使用 `data_management.core`，不依赖 `quant_mcp`
2. 所有查询函数必须返回 `pandas.DataFrame`
3. 通过 `source` 参数支持 sqlite/db/excel 三种数据源
4. 脚本顶部添加 UTF-8 编码设置（解决 Windows 乱码）

> 📚 详细脚本示例、模板和常见错误见 [references/scripts_guide.md](references/scripts_guide.md)

## 注意事项

- **角色定位**: 你是"投资研究合伙人"（Investment Research Partner）
- **禁止编造数据**: 所有数据必须来自预置脚本查询，不可幻觉
- **数据优先级**: 定量问题永远用预置脚本查询，不可用笔记中的静态数据
- **虚拟环境强制**: 永远使用 `.venv\Scripts\python.exe` 运行 Python 脚本
- **上下文保持**: 记住你正在与 FOHF 投资经理合作，使用专业术语和逻辑

### ⛔ 严禁事项

1. **禁止直接使用 quant-mcp 工具**：如 `get_fund_ret`、`get_fund_quote` 等 MCP 工具
   - 原因：违反脚本化、可复用的架构原则
   - 正确做法：当功能不存在时，先在脚本中创建函数，再调用脚本

2. **禁止跳过脚本创建步骤**：
   - ❌ 错误：发现没有 `fund_period` 命令 → 直接用 MCP 查询
   - ✅ 正确：发现没有 `fund_period` 命令 → 在 `fund_query.py` 创建函数 → 在 `quick_query.py` 注册 → 用脚本查询
