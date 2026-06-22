# 管理人与产品研究接口文档（Skill 调用版）

本文档用于给外部 Skill 直接调用 `fof-research-agent` 的私募管理人 / 产品研究接口。

## 1. 基础信息

- 服务地址示例: `http://10.168.20.62:7000`
- 服务前缀: `/fofresearchsvr/ai`
- 返回包装格式:

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

说明:

- `code=0` 表示成功
- `code=-1` 表示失败
- 除下载类接口外，统一返回 JSON

## 2. 工具接口总览

| 工具名 | Method | Path | 说明 |
| --- | --- | --- | --- |
| search_managers | GET | `/fofresearchsvr/ai/search_managers` | 管理人检索统一入口，支持精确过滤 + `query` 自然语言 / 关键词检索 |
| get_manager_detail | GET | `/fofresearchsvr/ai/get_manager_detail` | 管理人详情 |
| list_manager_products | GET | `/fofresearchsvr/ai/list_manager_products` | 管理人旗下产品列表 |
| list_manager_materials | GET | `/fofresearchsvr/ai/list_manager_materials` | 管理人资料列表 |
| download_manager_material | GET | `/fofresearchsvr/ai/download_manager_material` | 下载指定管理人资料 |
| search_products | GET | `/fofresearchsvr/ai/search_products` | 产品候选查询，支持名称、管理人、策略、赛道、业绩报酬筛选 |
| get_product_detail | GET | `/fofresearchsvr/ai/get_product_detail` | 按 `product_id` 查询产品基础信息 |
| get_product_terms | GET | `/fofresearchsvr/ai/get_product_terms` | 按 `fund_code` 查询产品要素 |
| get_product_contract | GET | `/fofresearchsvr/ai/get_product_contract` | 按 `fund_code` 或 `product_id` 下载合同文件 |
| get_product_nav | GET | `/fofresearchsvr/ai/get_product_nav` | 产品净值序列 |

## 3. 详细接口定义

### 3.1 `search_managers`

- Method: `GET`
- Path: `/fofresearchsvr/ai/search_managers`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| query | string | 否 | 自然语言查询、关键词、英文短语、策略描述等 |
| manager_name | string | 否 | 精确匹配管理人名称 |
| personnel_name | string | 否 | 核心人员姓名 |
| product_name | string | 否 | 产品名称 |

说明:

- 至少提供一个查询条件: `query / manager_name / personnel_name / product_name`
- 精确机构名 / 人员名优先用硬过滤参数
- 关键词、全文、英文机构名、自然语言意图优先用 `query`
- Skill 层仅对外暴露 `query` 作为自然语言检索入口，不暴露 `top_k / search_mode / min_score / include_debug`

### 3.2 `get_manager_detail`

- Method: `GET`
- Path: `/fofresearchsvr/ai/get_manager_detail`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| manager_id | int | 是 | 管理人 ID |

### 3.3 `list_manager_products`

- Method: `GET`
- Path: `/fofresearchsvr/ai/list_manager_products`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| manager_id | int | 是 | 管理人 ID |

- 返回数组元素结构:

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| fund_name | string | 产品名称 |
| fund_id | int/string | 产品 ID |
| fund_code | string | 基金代码 |
| race_name | string | 赛道 |
| strategy_name | string | 策略 |

### 3.4 `search_products`

- Method: `GET`
- Path: `/fofresearchsvr/ai/search_products`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| product_name | string | 否 | 产品名称或关键词 |
| manager_name | string | 否 | 管理人名称 |
| strategy_name | string | 否 | 策略名称 |
| race_name | string | 否 | 赛道名称 |
| performance_fee | string | 否 | 业绩报酬 / 后端费率条件 |

说明:

- 接口不再要求 `product_name` 必填
- 至少提供一个有效条件；当前后端最稳的是 `product_name` / `manager_name` / `performance_fee`
- 适合以下场景:
  - 按产品名找候选产品
  - 按管理人 + 产品条件缩小候选
  - 按策略 / 赛道 / 业绩报酬做产品筛选

- 返回数组元素结构:

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| product_name | string | 产品名称 |
| manager_name | string | 管理人名称 |
| product_id | int/string | 产品 ID |
| fund_code | string | 产品编码 |
| race_name | string | 赛道 |
| strategy_name | string | 策略 |
| performance_fee | string | 业绩报酬 |
| fund_manager | string | 基金经理 |

### 3.5 `list_manager_materials`

- Method: `GET`
- Path: `/fofresearchsvr/ai/list_manager_materials`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| manager_id | int | 是 | 管理人 ID |

### 3.6 `download_manager_material`

- Method: `GET`
- Path: `/fofresearchsvr/ai/download_manager_material`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file_path_reality | string | 是 | 资料文件真实路径 |

### 3.7 `get_product_detail`

- Method: `GET`
- Path: `/fofresearchsvr/ai/get_product_detail`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| product_id | int | 是 | 产品 ID |

### 3.8 `get_product_terms`

- Method: `GET`
- Path: `/fofresearchsvr/ai/get_product_terms`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| fund_code | string | 否 | 产品编码 |

说明:

- 当前 Skill 使用时按 `fund_code` 调用
- 当用户说“产品编码”时，映射为 `fund_code`

### 3.9 `get_product_contract`

- Method: `GET`
- Path: `/fofresearchsvr/ai/get_product_contract`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| product_id | int | 否 | 产品 ID |
| fund_code | string | 否 | 产品编码 |

说明:

- `product_id` 和 `fund_code` 至少传一个
- 若同时都有，优先 `fund_code`
- 返回文件流下载（`pdf/doc/docx`）
- 未命中时返回 `404`

Skill 落地要求:

- 收到文件流后立刻写入本地临时目录: `/tmp/openclaw_downloads/wisdom-manager-product-research/`
- 文件名优先使用响应头 `Content-Disposition` 中的原始文件名
- 最终结果中返回:
  - `local_file_path`
  - `filename`
  - `content_type`
  - `file_size_bytes`

### 3.10 `get_product_nav`

- Method: `GET`
- Path: `/fofresearchsvr/ai/get_product_nav`
- Query 参数:

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| product_id | int | 是 | 产品 ID |

## 4. 推荐编排

### 4.1 管理人问题

1. `search_managers`
2. `get_manager_detail`
3. `list_manager_products`
4. 如需管理人资料目录，调用 `list_manager_materials`
5. 如需下载指定资料文件，调用 `download_manager_material`

### 4.2 产品问题

1. 若用户已提供产品编码，直接用 `fund_code` 调用 `get_product_terms` 或 `get_product_contract`
2. 若用户仅提供产品名或筛选条件，先 `search_products`
3. 从候选中确认唯一 `product_id`
4. 再根据用户需求调用:
   - `get_product_detail`
   - `get_product_terms`
   - `get_product_contract`
   - `get_product_nav`

### 4.3 兜底

主查询无结果时，改用 `search_managers(query=<keyword or natural-language intent>)`

## 5. 快速联调示例

```bash
# 1) 管理人关键词 / 自然语言检索
curl -G "http://10.168.20.62:7000/fofresearchsvr/ai/search_managers" \
  --data-urlencode "query=在Two Sigma 任职过的人员"

# 2) 精确机构名检索
curl -G "http://10.168.20.62:7000/fofresearchsvr/ai/search_managers" \
  --data-urlencode "manager_name=上海磐松私募基金管理有限公司"

# 3) 列出管理人旗下产品
curl -G "http://10.168.20.62:7000/fofresearchsvr/ai/list_manager_products" \
  --data-urlencode "manager_id=357912"

# 4) 按条件筛产品
curl -G "http://10.168.20.62:7000/fofresearchsvr/ai/search_products" \
  --data-urlencode "manager_name=上海幻方量化投资管理有限公司" \
  --data-urlencode "strategy_name=指数增强"

# 5) 查产品要素
curl -G "http://10.168.20.62:7000/fofresearchsvr/ai/get_product_terms" \
  --data-urlencode "fund_code=SXQ364"

# 6) 下载产品合同
curl -G "http://10.168.20.62:7000/fofresearchsvr/ai/get_product_contract" \
  --data-urlencode "fund_code=SXQ364" \
  -OJ
```
