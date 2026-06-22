# 业绩报酬字段结构化与后端收费筛选方案

## 1. 背景与目标

当前数据库中的“业绩报酬”是非结构化字符串，存在固定比例、超额计提、分档计提、分份额计提等多种写法，无法直接用于稳定筛选。

目标是将文本统一解析为结构化字段，支持以下检索：

- 不收后端
- 后端很低（小于等于阈值）
- 指增/量选等策略条件 + 后端约束的组合筛选

## 2. 结构化字段设计

建议新增字段（可落在产品维表或衍生索引表）：

- `perf_fee_raw` `text`：原始业绩报酬文本
- `perf_fee_has_charge` `bool`：是否收业绩报酬
- `perf_fee_type` `enum`：`none/fixed/excess/tiered/share_class/unknown`
- `perf_fee_rate_min` `decimal(6,3)`：最小计提比例（单位：%）
- `perf_fee_rate_max` `decimal(6,3)`：最大计提比例（单位：%）
- `perf_fee_is_excess_only` `bool`：是否仅超额部分计提
- `perf_fee_confidence` `decimal(4,3)`：解析置信度（0-1）
- `perf_fee_parse_version` `string`：解析规则版本，支持回溯与重跑

## 3. perf_fee_type 枚举语义

- `none`：不收业绩报酬（如“不计提业绩报酬”）
- `fixed`：单一固定比例计提（如“20%”“【20】%”）
- `excess`：仅对超额/超出部分计提（如“超额计提20%”）
- `tiered`：按收益区间分档计提（如“0-60%按30%，60-100%按35%”）
- `share_class`：按份额类别（A/B/C类）区分比例，可叠加分档
- `unknown`：无法可靠解析或信息缺失（如仅有 Y1/Y2 未给数值）

## 4. 文本解析规则

解析流程：标准化 -> 规则匹配 -> 结果落库 -> 低置信度回查。

### 4.1 标准化

- 全角转半角，统一 `%`
- 去掉 `【】`、多余空格、换行
- 中文数字/符号归一（如“百分之二十”->`20%`）

### 4.2 规则优先级（从高到低）

1. `不计提|无业绩报酬|不收取业绩报酬` -> `none`
2. `超额|超出部分|超过.*部分.*计提` + 百分比 -> `excess`
3. 多个区间词（`至|以上|以下|区间`）且多比例 -> `tiered`
4. 份额词（`A类|B类|C类|份额`）+ 比例 -> `share_class`
5. 单一比例（仅一个 `%`）-> `fixed`
6. 其他 -> `unknown`

### 4.3 数值抽取

- 抽取所有百分比作为 `rates[]`
- `perf_fee_rate_min=min(rates)`，`perf_fee_rate_max=max(rates)`
- `none` 强制 `min=max=0`
- `unknown` 可置空或在可提取时仅回填 `min/max`，同时降低 `confidence`

## 5. 示例归一（基于当前样例）

1) “0-60%按30%，60-100%按35%，100%以上按40%” -> `tiered`，`min=30`，`max=40`  
2) “20%” -> `fixed`，`min=max=20`  
3) “不计提业绩报酬” -> `none`，`min=max=0`  
4) “超额计提20%” -> `excess`，`min=max=20`  
5) “A类 Y1/Y2，B类...”且数值缺失 -> `unknown`（若有15/25等可抽取则 `share_class`）  
6) “对超出部分提取13%的业绩报酬” -> `excess`，`min=max=13`  
7) “【20】%” -> `fixed`，`min=max=20`

## 6. 筛选口径（产品检索）

### 6.1 不收后端

`perf_fee_has_charge=false OR perf_fee_rate_max=0`

### 6.2 后端很低（<=X%）

`perf_fee_rate_max <= X`

### 6.3 复杂条款处理

- 默认使用 `rate_max` 作为保守口径，避免误把高费率产品归入“低后端”
- `unknown` 默认剔除（`exclude_unknown_fee=true`）

## 7. 接口/工具改造建议

### 7.1 扩展产品搜索接口

在 `search_products`（或新增聚合检索接口）支持：

- `strategy_names[]`
- `race_names[]`
- `backend_fee_max`
- `backend_fee_type`（`performance_fee` / `all_backend_fee`）
- `exclude_unknown_fee`（默认 `true`）
- `sort_by=backend_fee_asc`

### 7.2 新增批量要素摘要接口（推荐）

`batch_get_product_terms_summary(product_ids/fund_codes[])`：

- 批量返回 `perf_fee_type/min/max/confidence/raw`
- 避免 N 次 `get_product_terms` 导致时延高和不稳定

## 8. 落地步骤

1. 增加结构化字段（表结构或索引映射）  
2. 实现文本解析器（规则 + 正则 + 置信度）  
3. 跑一次全量回填，保存 `parse_version`  
4. 增加增量任务（产品要素更新触发重解析）  
5. 扩展搜索接口与排序  
6. 补充回归用例（不收后端、低后端、复杂条款、unknown）  

## 9. 风险与治理

- 文本多样性高，需维护规则版本并可回溯
- `unknown` 需要运营/研究侧兜底复核
- 对“超额计提”条款，建议后续补充阈值字段（如门槛收益、基准、高水位）以提升精度

