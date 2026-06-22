# `search_managers` / `search_products` 检索改造方案

## 1. 目标

为 Agentic Protocol 的私募查询助手提供更清晰、可扩展的检索工具：

- 管理人查询使用单一主入口，减少工具歧义
- 支持关键词 + 向量的混合检索（hybrid）
- 将 `races/strategies` 从"管理人硬标签"改为"产品标签 + 管理人派生画像"
- **在既有路径上直接升级**：不新增 `*_v2` 路由，不采用「先兼容上线再切换」的迁移方式

## 2. 当前问题

基于现有实现（`fof-research-agent`）：

- 管理人检索入口曾存在能力重叠，工具层对 Agent 不友好
- `search_managers` 本质是 `content` 关键词匹配 + 若干过滤，语义召回不足
- `races/strategies` 来源是产品标签，但当前直接作为管理人索引过滤条件，语义层级不一致
- `search_products` 目前强依赖 `product_name`，不利于"按策略/赛道/费率找候选产品"

## 3. 工具层目标形态

### 3.1 管理人检索（直接升级现有接口）

`GET /fofresearchsvr/ai/search_managers`

在**同一路径**上替换实现为 hybrid 检索，参数与返回按本节约定收敛。

#### Skill 暴露参数（Agent 可用）

- `query` `string`：自然语言查询（可选）
- `manager_name` `string`：管理人名称（可选）
- `personnel_name` `string`：核心人员（可选）
- `product_name` `string`：产品名（可选）
- `top_k` `int`：返回条数（默认 `10`）

> **注意**：`strategy_names`/`race_names` 不作为管理人查询参数，原因：
> 1. 这是**产品级分类**，不是管理人标签，语义层级不匹配
> 2. 属于内部分类术语，存在语义模糊，非行业标准分类
>
> 如需按策略/赛道筛选，Agent 应将意图写入 `query`（如"做中证500增强的管理人"），由后端通过向量召回 + `manager_strategy_exposure` 派生画像自动处理。

#### 后端内部参数（用于测试对比，Skill 不暴露）

- `search_mode` `enum`：`auto|lexical|vector|hybrid`（默认 `auto`，后端自动选择最优策略）
- `min_score` `float`：最低分阈值（默认 `0.3`，低于此分数的结果不返回）
- `include_debug` `bool`：返回打分解释（默认 `false`）

#### 参数融合策略

当 `query` 与结构化参数（`manager_name/personnel_name/product_name`）同时存在时：

- 结构化参数作为**硬过滤条件**，优先保证精确匹配
- `query` 参与语义召回与重排，提升相关性排序

#### 约束

- 至少一个条件非空：`query/manager_name/personnel_name/product_name`

返回建议：

- `manager_id`
- `manager_name`
- `match_score`
- `match_reasons`（如：`name_exact`, `personnel_hit`, `vector_semantic`, `strategy_exposure_match`）
- `evidence_snippets`（可选，短证据）
- `strategy_exposure`（派生统计，如：`{"中证500指增":0.35, "量化选股":0.22}`）

### 3.2 接口收敛策略

- **`/search_managers`**：按本节实现直接升级；移除对 `strategies`/`races` 的依赖（若历史调用仍传参，可忽略或合并进内部 `query` 拼接用于过渡期，以实际兼容策略为准）。

## 4. 检索架构（Hybrid）

`search_managers` 内部建议分三层：

1. 召回层  
`lexical recall`（ES BM25 + 结构化条件）并行 `vector recall`（embedding ANN）

2. 过滤/特征层  
人名、机构名、产品名、产品策略/赛道映射、尽调覆盖等特征提取

3. 重排层  
`final_score = w1*lexical + w2*vector + w3*rule_boost - penalties`

### 4.1 推荐默认权重（可配置）

- `w1=0.45`（lexical）
- `w2=0.35`（vector）
- `w3=0.20`（rule_boost）

建议支持按场景动态配置权重，便于后续 AB 测试。

### 4.2 Embedding 模型选型

中文金融领域推荐以下模型（按优先级）：

| 模型 | 维度 | 特点 |
|------|------|------|
| BGE-large-zh-v1.5 | 1024 | 中文通用效果好，社区活跃 |
| m3e-large | 1024 | 中文语义理解强，适合检索场景 |
| text2vec-large-chinese | 1024 | 备选，推理速度快 |

如已有向量服务，优先复用；如新建，推荐 BGE 系列。

### 4.3 `auto` 模式路由逻辑（后端实现）

- 有明确 `manager_name/personnel_name`：优先 lexical，再混合补召回
- 纯自然语言描述（仅 `query`）：hybrid
- query 很短（<5 字符）且为标准名词：lexical

## 5. 标签分层策略（关键）

### 5.1 当前问题分析

当前 `due_es_svr.py` 中 `races/strategies` 使用 ES `terms` 精确匹配：

```python
must.append(Q("terms", strategyNames=strategies))
must.append(Q("terms", raceNames=races))
```

存在问题：

| 问题 | 说明 |
|------|------|
| **术语不一致** | 用户说"500增强"，标签是"中证500指数增强"；用户说"量化多头"，标签是"股票多头" |
| **语义层级错配** | `races/strategies` 是产品级标签，直接作为管理人硬过滤会漏召回多产品线管理人 |
| **漏召回严重** | 精确匹配导致用户稍有表述差异就返回空结果 |

### 5.2 数据语义调整

- `races/strategies` 作为产品标签，仅保留在产品域
- 管理人域新增派生字段：`manager_strategy_exposure`, `manager_race_exposure`
- 派生口径：基于旗下产品的数量占比/规模占比（先实现数量占比）

派生数据示例：

```json
{
  "manager_id": 12345,
  "manager_strategy_exposure": {
    "中证500指数增强": 0.40,
    "量化选股": 0.35,
    "市场中性": 0.25
  },
  "manager_race_exposure": {
    "500指增": 0.40,
    "量化多头": 0.60
  }
}
```

### 5.3 查询语义改造

**升级后的 `search_managers` 不再接收 `strategy_names/race_names` 参数**，原因：

1. 这是**产品级分类**，不是管理人标签，语义层级不匹配
2. 属于内部分类术语，存在语义模糊，非行业标准分类

策略/赛道意图的处理方式：

1. **用户意图通过 `query` 表达**：如"找做中证500增强的管理人"
2. **后端自动处理**：向量召回 + 同义词扩展 + `manager_strategy_exposure` 重排
3. **无需 Agent 传递结构化参数**：避免术语不一致导致的漏召回

### 5.4 术语同义词表

维护策略/赛道同义词映射，查询时自动扩展：

```json
{
  "500增强": ["中证500指数增强", "中证500指增", "500指增", "沪深500增强"],
  "量化多头": ["股票多头", "量化选股", "主观多头"],
  "1000指增": ["中证1000指数增强", "中证1000增强", "1000增强"],
  "市场中性": ["股票中性", "量化中性", "阿尔法策略"]
}
```

实现方式：

- 维护同义词表（JSON/数据库）
- 查询时：用户输入 → 同义词扩展 → 参与召回与重排
- 定期根据实际查询日志补充同义词

### 5.5 match_reasons 置信度

返回的 `strategy_exposure_match` 增加置信度等级：

| 置信度 | 条件 | 说明 |
|--------|------|------|
| `high` | exposure >= 0.3 | 该策略为管理人主营方向 |
| `medium` | 0.1 <= exposure < 0.3 | 有布局但非主营 |
| `low` | 0 < exposure < 0.1 | 仅有少量产品涉及 |

返回示例：

```json
{
  "match_reasons": [
    {"type": "strategy_exposure_match", "strategy": "中证500指增", "exposure": 0.40, "confidence": "high"}
  ]
}
```

## 6. `search_products` 联动调整（同步改造）

当前 `search_products` 的 `product_name` 为必填，不利于条件检索。在**同一路径**上直接升级：

`GET /fofresearchsvr/ai/search_products`

#### Skill 暴露参数（Agent 可用）

- `query` `string`：产品自然语言关键词（可选）
- `product_name` `string`（可选）
- `manager_name` `string`（可选）
- `backend_fee` `float`（可选，后续接入结构化费率）
- `exclude_unknown_fee` `bool`（默认 `true`）
- `top_k` `int`（默认 `10`）

> **注意**：与 `search_managers` 保持一致，`strategy_names`/`race_names` 不作为 Skill 暴露参数。
> 策略/赛道意图通过 `query` 表达（如"中证500增强产品"），由后端向量召回处理。

#### 后端内部参数（用于测试对比，Skill 不暴露）

- `search_mode` `enum`：`auto|lexical|vector|hybrid`（默认 `auto`）
- `min_score` `float`：最低分阈值（默认 `0.3`）
- `strategy_names` `string|string[]`（精确过滤，仅供测试/运营）
- `race_names` `string|string[]`（精确过滤，仅供测试/运营）

#### 约束

- 至少一个条件非空，不再强制 `product_name`

#### 返回建议

- `product_id`, `product_name`, `manager_name`, `fund_code`
- `strategy_name`, `race_name`（作为产品属性返回，供展示用）
- `match_score`, `match_reasons`
- 若接入费率：`perf_fee_type`, `perf_fee_rate_max`, `fee_confidence`

## 7. 实现步骤（后端）

1. **数据准备**
   - 新增/补齐 manager 向量索引（推荐 BGE-large-zh-v1.5）
   - 离线产出 `manager_strategy_exposure` 与 `manager_race_exposure`
   - 初始化策略/赛道同义词表

2. **同义词服务**
   - 维护同义词映射表（JSON 或数据库）
   - 实现查询时同义词扩展接口
   - 建立同义词更新机制（根据查询日志定期补充）

3. **Service 层改造**
   - 在 `search_managers` / `search_products` 上直接实现 hybrid 与参数收敛（Skill 不暴露 `strategy_names/race_names`）
   - 语义查询通过 `query`，后端自动处理术语映射
   - 支持 `search_mode` 路由与并行召回

4. **ES/向量查询封装**
   - 在 `DueESSvr` 增加 lexical 查询与 ANN 查询封装
   - **移除管理人检索路径上 `races/strategies` 的 `terms` 硬过滤**
   - 统一返回可重排的候选格式

5. **重排与解释**
   - 加入融合打分公式
   - 生成 `match_reasons`（含置信度等级）
   - 实现 `strategy_exposure_match` 计算

6. **Skill 文档更新**
   - 更新 `references/api.md`：仅暴露 Skill 可用参数
   - 更新 `SKILL.md` 的推荐流程
   - `search_mode`/`min_score` 不写入 Skill 文档

7. **Evals 补充**
   - 新增"非标准表达检索"样例（如"500增强" → "中证500指数增强"）
   - 新增"策略同义词检索"样例
   - 新增"管理人-产品联动筛选"样例

## 8. 迁移策略

- **不引入 `search_managers_v2` / `search_products_v2`**：在现有 `search_managers`、`search_products` 上直接替换实现。
- **不采用「兼容上线、双轨并行」**：一次发布即切换为新语义与参数约定（按团队流程可做灰度或 feature flag，但**不保留长期并行的 v2 路由**）。

## 9. 指标与验收

核心指标：

- Top1 命中率
- Top3 召回率
- 空结果率
- 平均响应时延
- 非标准术语查询成功率（如"中证500增强""量化选股增强"等同义表达）

验收标准建议：

- Top1 命中率较现网提升 >= 15%
- 空结果率下降 >= 20%
- P95 时延满足服务SLO

## 10. 风险与规避

- 风险：向量召回带来噪声  
  规避：设置 `min_score` + lexical 必须命中至少一类实体特征（可配置）

- 风险：标签派生延迟导致画像过期  
  规避：每日增量任务 + 全量周更

- 风险：直接替换接口导致存量调用方异常  
  规避：发布前核对调用方清单，并给出明确迁移说明与窗口期

- 风险：技能文档与线上接口不一致  
  规避：接口上线同版本更新 `api.md` 与 evals
