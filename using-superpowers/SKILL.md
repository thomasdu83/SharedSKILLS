---
name: using-superpowers
description: 当用户明确询问 Superpowers 或 skills 的使用方式、需要排查 skill 路由、或正在维护 .trae/skills 与 .trae/rules 时使用
---

# Using Superpowers

这个 skill 只用于处理技能系统本身，不再作为每轮对话的默认前置步骤。

## 何时使用

- 用户明确询问 Superpowers 或某个 skill 应该怎么用
- 需要排查某个 skill 为什么触发 / 没触发
- 需要修改 `.trae/rules/` 或 `.trae/skills/`
- 需要审计 skills 层的 token 开销或路由策略

## 何时不要使用

- 日常编码、排查、审查、文档处理
- 已有更具体 domain skill 可直接处理的任务
- 仅仅因为“可能有帮助”而想预加载技能系统说明

## 工作方式

1. 先确认当前任务是不是“关于技能系统本身”。
2. 只读取和当前问题直接相关的规则文件或 skill 文件。
3. 如需继续下钻，只打开具体目标 skill，不级联加载多个元 skill。
4. 优先做最小改动，避免为了流程而增加上下文成本。

## 优先级

- 用户指令和仓库规则优先于本 skill。
- 更具体的领域 skill 优先于本元 skill。

## Token 纪律

- 把上下文窗口当成共享预算，不使用“1% 可能性也强制触发”的策略。
- 优先明确匹配，避免推测式触发。
- 若需要长期保留某类说明，优先写成短路由 + 按需引用，而不是在入口文件中展开细节。
