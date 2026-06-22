# 查询型 Skill 升级为投研报告生成 Agent 方案（Excel/Word）

## 1. 目标

将当前以“信息查询”为主的 `wisdom-manager-product-research`，升级为可直接产出投研报告的 Agent，支持：

- 自动完成管理人/产品信息检索与归并
- 生成结构化结论（核心观点、风险点、证据链）
- 一键导出 `Word(.docx)` 与 `Excel(.xlsx)` 报告文件

目标形态：`检索 -> 分析 -> 成稿 -> 导出`，而不是“检索结果拼接”。

## 2. 当前能力与差距

当前仓库能力：

- `SKILL.md` 以接口调用流程为核心（manager/product/fallback）
- `references/api.md` 提供查询类 API 说明
- `evals/evals.json` 偏查询正确性

主要差距：

- 缺少“报告任务编排”与“报告结构模板”
- 缺少统一中间数据模型（无法稳定映射到 Word/Excel）
- 缺少文件导出工具与落盘规范
- 缺少“结论可追溯”与“报告质量校验”环节

## 3. 目标 Agent 架构（建议）

采用四层架构，减少后续扩展成本：

1. 任务编排层（Orchestrator）  
识别任务类型：管理人尽调、产品要素分析、对比研究、定制筛选报告。

2. 数据采集层（已有 API 复用）  
沿用 `search_managers/get_manager_detail/list_manager_products/search_products/get_product_detail/get_product_terms/get_product_nav`，仅在必要处补充批量接口。

3. 分析归纳层（新增）  
统一产出报告中间结构（JSON），包含指标、结论、证据、风险提示。

4. 文档生成层（新增）  
基于模板输出 `docx/xlsx`，并返回本地文件路径供后续分发。

## 4. Skill 改造建议

## 4.1 从“查询动作”改为“报告任务”

建议在 `SKILL.md` 中新增任务入口（意图级）：

- `generate_manager_report`
- `generate_product_report`
- `generate_comparison_report`
- `export_report_docx`
- `export_report_xlsx`

仍保留原查询动作，但仅作为子步骤，不再直接作为最终产物。

## 4.2 新的执行主流程

建议主流程：

1. 明确报告对象与范围（管理人/产品/时间窗/筛选条件）
2. 调用查询 API 收集数据
3. 归一到报告中间结构 `ReportContext`
4. 生成结论与风险提示（必须引用数据证据）
5. 生成 Word/Excel
6. 返回摘要 + 附件路径

## 4.3 输出约束升级

在 `SKILL.md` 增加以下硬约束：

- 结论必须可追溯到字段或接口返回
- 报告必须包含“数据截至日期”
- 文件导出成功时必须返回：
  - `local_file_path`
  - `filename`
  - `file_size_bytes`
  - `generated_at`

## 5. 报告中间模型（关键）

建议新增统一模型（逻辑结构）：

```json
{
  "report_meta": {
    "report_type": "manager|product|comparison",
    "title": "string",
    "as_of_date": "YYYY-MM-DD",
    "generated_at": "YYYY-MM-DD HH:mm:ss"
  },
  "subject": {
    "manager_id": 0,
    "product_id": 0,
    "fund_code": "string"
  },
  "facts": {
    "manager_profile": {},
    "product_profile": {},
    "nav_summary": {},
    "terms_summary": {}
  },
  "analysis": {
    "highlights": [],
    "risks": [],
    "open_questions": []
  },
  "evidence": [
    {
      "source_api": "get_product_detail",
      "field": "strategy_name",
      "value": "中证500指增"
    }
  ]
}
```

价值：

- 统一承接多 API 返回，避免模板耦合接口字段
- Word/Excel 共用一套数据，减少双份逻辑
- 便于评测“结论-证据一致性”

## 6. Word/Excel 生成方案

## 6.1 目录与产物规范

建议约定输出目录：

- `/tmp/openclaw_reports/wisdom-manager-product-research/`

命名规范：

- Word：`report_{type}_{subject}_{yyyymmdd}.docx`
- Excel：`report_{type}_{subject}_{yyyymmdd}.xlsx`

## 6.2 Word 模板建议（docx）

推荐固定章节：

- 执行摘要
- 主体信息（管理人/产品）
- 策略与赛道画像
- 关键指标与净值表现（如可得）
- 风险揭示
- 数据来源与口径说明

实现方式建议：模板驱动（占位符渲染），避免纯字符串拼接。

## 6.3 Excel 模板建议（xlsx）

推荐 Sheet：

- `Summary`：核心结论与评级
- `ManagerOrProductFacts`：基础字段明细
- `NAV`：时间序列（如有）
- `Evidence`：结论对应证据映射

实现方式建议：固定列头 + 数据校验，保证可二次加工。

## 7. API/工具扩展建议（最小可用）

第一阶段尽量不改后端主接口，仅新增导出工具：

- `generate_report_context`：将多接口结果归并为 `ReportContext`
- `render_report_docx`：输入 `ReportContext` 输出 `.docx`
- `render_report_xlsx`：输入 `ReportContext` 输出 `.xlsx`

第二阶段按需要补充批量接口（可选）：

- `batch_get_product_detail`
- `batch_get_product_terms_summary`
- `batch_get_product_nav`

## 8. 仓库改造清单

建议修改/新增以下文件：

- 修改 `SKILL.md`：新增报告任务流与导出规则
- 修改 `references/api.md`：登记报告导出相关工具
- 修改 `evals/evals.json`：增加报告场景评测（结构完整性、证据一致性、文件成功率）
- 新增 `docs/plans/report-templates-spec.md`（可选）：定义 Word/Excel 模板字段

## 9. 分期落地计划

### Phase 1：报告化编排（先不导出文件）

- 增加 `ReportContext` 归并逻辑
- 让 Agent 输出结构化报告 JSON + Markdown 摘要
- 建立“结论-证据”校验规则

验收：同一输入可稳定输出结构一致的报告 JSON。

### Phase 2：Word/Excel 导出

- 接入 `docx/xlsx` 渲染能力
- 完成文件落盘、命名、元信息回传
- 打通“查询 -> 报告 -> 文件路径返回”

验收：可稳定生成可打开、结构正确的 Word/Excel。

### Phase 3：质量与效率优化

- 批量接口/缓存，降低多产品对比时延
- 增加模板版本管理
- 增加报告回归评测与监控指标

验收：报告成功率、生成时延、字段缺失率达到目标阈值。

## 10. 评测指标建议

- 报告生成成功率（docx/xlsx）
- 结构完整率（必填章节覆盖）
- 结论证据一致率（抽样校验）
- 平均生成时延（P50/P95）
- 字段缺失率（按报告类型统计）

## 11. 风险与应对

- 数据字段缺失导致报告断裂：  
  用 `unknown` 与“待补充”占位策略，避免导出失败。

- 大模型总结偏离原始数据：  
  强制 evidence 映射，未映射结论不入报告。

- 模板频繁改动导致兼容问题：  
  对模板增加 `template_version`，与渲染逻辑做版本绑定。

## 12. 结论

建议采用“先中间模型、后文件导出、再做性能优化”的路径。  
这条路径能最大化复用现有查询 API，并最小化一次性改造风险，较快把 Skill 从“查询助手”升级为“可交付投研报告的 Agent”。
