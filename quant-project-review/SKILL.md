---
name: quant-project-review
description: Use when the user asks how far a QuantSystem project has progressed, what stage it is in, whether it has drifted from its original goal, or what the next smallest milestone should be.
---

# Quant Project Review

用于评估 QuantSystem 项目的进度、阶段、偏航风险和下一步最小闭环，而不是直接推进实现。

## 何时使用

- 用户问“现在做到哪了”“完成了多少”“离初始目标还有多远”
- 用户问“有没有走偏”“现在做的事还对不对”
- 用户想知道项目当前属于 `idea`、`research`、`candidate`、`production` 还是 `monitor_only`
- 用户想知道下一步最小且最重要的里程碑是什么

## 评估原则

- 先重建或确认项目的**初始目标**
- 再判断当前**真实阶段**
- 只根据真实产出、真实链路、真实验证来判断进度
- 不用“工作量很多”代替“目标接近完成”
- 如果没有明确初始目标，先从需求、计划文档、`project.yaml`、主输出物中推断，并明确说明这是推断

## 四个核心维度

1. **目标完成度**：最初承诺的核心能力实现了多少
2. **主链路完成度**：从输入数据到策略/模型输出的闭环打通了多少
3. **验证完成度**：测试、回测、校验、口径确认做到了多少
4. **偏航程度**：最近工作有多少直接服务初始目标，有多少已经变成旁支扩展

详细评分口径见 `references/review-rubric.md`。

## 工作流

1. 锁定初始目标
2. 识别当前阶段
3. 盘点已完成产出
4. 映射主链路状态
5. 检查验证覆盖
6. 判断是否偏航
7. 给出下一步最小闭环建议

可优先查看的证据来源见 `references/evidence-sources.md`。

## 输出要求

- 用固定结构输出，避免泛泛而谈
- 结论必须区分“已完成”“正在推进”“尚未开始”
- 偏航判断必须给出证据，而不是只给感觉
- 下一步建议必须是**最小闭环动作**，不是大而空的路线图

输出模板见 `references/output-template.md`。
