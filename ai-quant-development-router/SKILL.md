---
name: ai-quant-development-router
description: Use when creating or materially extending a quantitative strategy, model, factor, label, signal, backtest, portfolio or risk model, including source-paper implementations; exclude explanations, one-off calculations, page-only edits and isolated bugs.
---

# AI Quant Development Router

每阶段只推进一个可运行、可检查、可解释的最小闭环。
本 Skill 统筹新量化开发，不决定模型有效性，也不要求先建完整平台。

| 请求 | 本阶段入口 |
|---|---|
| 新模型、新策略或跨模型/API/前端变更 | 本 Skill |
| 一次性取数、快速验证、研究辅助计算 | `quant-research-coding` |
| 已确认原型的定期运行、共享消费、工程固化 | `quant-develop` |
| 已有结果纯排版、页面局部调整 | `frontend-page-router` |
| 孤立 bug / 只评估项目进度 | `systematic-debugging` / `quant-project-review` |
| 仅审读论文、列可复现性缺口 | `investment-paper-replication` |

## 当前阶段

1. 明确假设、用户和用途、数据/PIT、当前阶段、最小交付与停止条件。
2. 按注册表选 0–2 个辅助 Skill。来源驱动的新模型可选 `investment-paper-replication`；
   页面、调试与验证按阶段选用。交给研究/工程入口后生成新的路由记录，不并列两个总控。
3. **开始方案或实现前必读** [增量开发细则](references/incremental-workflow.md)，
   保留其中的金融语义、验证、预览、阶段和人工确认规则；已有用户授权优先，不重复申请。
4. 每轮给出运行证据，达到本轮闭环后再判断继续、回退、升级或暂停。

## 路由输出

按 `../shared-contracts/route-decision.yaml` 记录 primary_skill、support_skills、
task_class、risk_level、trigger_evidence、excluded_skills、escalation、unresolved。
另列本轮所需契约与停止条件，至少核对 `lifecycle.yaml` 和 `execution.yaml`。
风险按 Level 1–4；数据或验证缺口必须显式留下，不得把研究结果冒充投资有效性。
