---
name: project-retrospective
description: Use when the user asks for a project postmortem, 项目复盘, 总结经验, 沉淀规则, 回顾项目, retrospective, lessons learned, or wants to extract reusable rules, failure patterns, checklists, or skill candidates from a completed or paused project.
---

# Project Retrospective

## Purpose

Turn a project into reusable knowledge instead of a one-off summary.

## Operating rules

- Start from the project goal and final result.
- Separate facts, inferences, and opinions.
- Keep project-specific numbers, names, and one-time tradeoffs out of reusable guidance.
- Promote only stable patterns into rules or skill candidates.
- Mark weak evidence explicitly as “推断” or “待确认”.
- Keep the output short and decision-oriented.
- If a lesson should change how future LLMs work, route it into the relevant skill under `F:\Thomas\SharedSKILLS`.

## Suggested output shape

1. 项目结论
2. 目标与结果
3. 成功经验
4. 失败 / 风险
5. 可复用规则
6. 不建议沉淀为 skill 的细节
7. 下次同类项目检查清单
8. 回写到共享 skill

## Skill write-back

When the retrospective surfaces reusable behavior, produce a write-back block for the shared skill library:

- target skill in `F:\Thomas\SharedSKILLS`
- what to add, remove, or tighten
- whether it is an update to an existing skill or a candidate for a new one
- why it is stable enough to reuse

Only write back patterns that are repeated, stable, and not tied to one project’s paths, names, or deadlines.

## Boundary

If the user is asking about progress, stage, drift, or the next milestone, use `quant-project-review` instead. If the user is asking how to implement or fix something, switch to the relevant build/debug skill.

## Reference

Load `references/output-template.md` when you need the exact reporting scaffold or a tighter rule for deciding what should become a reusable skill.
