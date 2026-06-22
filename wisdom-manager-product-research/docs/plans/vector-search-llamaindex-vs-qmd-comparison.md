# 向量搜索方案对比：LlamaIndex vs qmd（结合现有后端）

更新时间：2026-04-20

## 1. 结论（先给推荐）

推荐主方案：**LlamaIndex（Python）**。  
不推荐把 **qmd** 作为当前 `fof-research-agent` 主检索底座；可作为“本地知识库/研发侧工具”补充使用。

原因很直接：

- 现有后端已经是 Python/FastAPI，并且已引入 LlamaIndex 相关依赖与代码路径，迁移成本最低。
- 现有 manager/product 查询需要和结构化条件（管理人、产品、人员、策略、赛道、费率）深度耦合，LlamaIndex 更容易做“服务内混合检索”。
- qmd 主线是 Node/Bun + 本地 GGUF 推理栈，工程形态偏 CLI/本地知识库，和现有服务化链路不完全匹配。

## 2. 与当前后端实现的贴合度

`fof-research-agent` 已有事实：

- Python FastAPI 服务，manager 搜索走 ES（`core/utils/due_es_svr.py`）。
- 已有 LlamaIndex 检索实现与测试：
  - `app/data_api_agent/retrieval/build_index.py`
  - `app/data_api_agent/retrieval/search_engine.py`
  - `tests/test_index_search.py`
- 依赖已包含：
  - `llama-index-core==0.14.7`
  - `llama-index-embeddings-huggingface==0.6.1`
- 仓库内还存在 Milvus 向量检索模块（`app/rag/ensemble_retriever/*`），说明服务侧已具备向量化落地基础。

结论：现状是“**LlamaIndex 已在场**”，qmd 属于新增技术栈。

## 3. 对比表

| 维度 | LlamaIndex | qmd |
| --- | --- | --- |
| 与当前技术栈匹配 | 高（Python 原生） | 中低（主线 Node/Bun CLI） |
| 现有代码复用 | 高（已有索引/检索代码） | 低（需新接入层或独立服务） |
| 检索能力 | 支持向量检索、BM25 组件、向量库集成与混合方案 | 内置 BM25+向量+RRF+重排，CLI 能力强 |
| 数据形态适配 | 适合结构化+非结构化混合 | 强于 Markdown 文档知识库 |
| 服务化改造 | 低成本（同进程/同语言） | 成本较高（跨进程或跨语言） |
| 运维复杂度 | 中（Python 依赖管理） | 中高（Node/Bun + 本地模型 + llama.cpp 生态） |
| 成熟度（与你们场景） | 高（你们项目内已落地） | 中（主仓活跃，但你们服务尚未接入；Python 版仍 Alpha） |

## 4. 为什么不是 qmd 主方案

qmd 本身很强，但当前阶段不适合作为主底座：

1. **形态错位**  
qmd 官方定位更偏本地搜索引擎/CLI/MCP，默认索引是本地 SQLite 文件，对“线上 API + 结构化业务过滤”需要额外封装。

2. **运行时栈新增**  
要引入 Node/Bun、模型下载与本地推理管理（node-llama-cpp / GGUF），会增加部署与资源复杂度。

3. **Python 版成熟度风险**  
PyPI 上 `qmd`（Python 版）在 2026-04-16 发布 `0.1.2`，分类仍是 `Development Status :: 3 - Alpha`，不建议直接作为核心生产依赖。

## 5. 建议架构（落地到 search_managers_v2）

建议采用：**ES lexical + LlamaIndex vector + 规则重排**。

1. 召回层  
- Lexical：沿用 `due_es_svr.search_org`（名称/人员/产品等精确约束）  
- Vector：新增 manager 语义召回（基于尽调摘要、公司介绍、产品策略描述）

2. 融合层  
- RRF 或加权融合：`score = a*lexical + b*vector + c*rule_boost`
- `strategy_names/race_names` 作为软约束加分，不做强过滤（避免术语不一致漏召回）

3. 返回层  
- 输出 `match_reasons` 与 `evidence_snippets`，增强可解释性

## 6. `search_products` 联动建议

若你们推进 `search_managers_v2`，建议同步加 `search_products_v2`：

- 允许无 `product_name` 的条件检索（策略/赛道/管理人/费率阈值）
- 增加 `search_mode=auto|lexical|vector|hybrid`
- 费率字段走结构化归一（见已有 perf fee 方案文档）

这样 manager/product 两条链路可共享同一套 hybrid 逻辑。

## 7. 何时可以选 qmd

以下场景可以考虑 qmd 作为补充：

- 研究员个人本地知识库搜索（大量 Markdown、会议纪要、笔记）
- 快速搭建本地 Agent 检索工具，不要求和后端结构化检索深度耦合
- 作为“离线辅助检索”而非交易/投研主查询链路

## 8. 实施建议（两周版本）

1. 第 1 周  
- 在 Python 内补 `search_managers_v2` 的 vector recall（复用现有 LlamaIndex/Milvus能力）  
- 加 `match_reasons` 与基础融合排序  

2. 第 2 周  
- 联动 `search_products_v2`  
- 增加评估集（非标准术语、同义词、行业口语）  
- 用 Top1/Top3 命中率与空结果率做灰度验收

## 9. 参考来源

- LlamaIndex 官方仓库（活跃度、版本、仓库信息）：  
  https://github.com/run-llama/llama_index
- LlamaIndex 向量库与集成文档：  
  https://developers.llamaindex.ai/python/framework/module_guides/storing/vector_stores/  
  https://developers.llamaindex.ai/python/framework/community/integrations/vector_stores/  
  https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/  
  https://developers.llamaindex.ai/python/framework-api-reference/retrievers/bm25/
- qmd 官方仓库与 README：  
  https://github.com/tobi/qmd
- qmd（Python 版）PyPI 信息：  
  https://pypi.org/project/qmd/

