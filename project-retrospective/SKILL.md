---
name: project-retrospective
description: Use when the user asks for a project postmortem, 项目复盘, 总结经验, 沉淀规则, 回顾项目, retrospective, lessons learned, micro-retro, 单次任务复盘, meta-retro, 季度经验复盘, or wants to reconstruct a project from a long multi-turn conversation, implementation history, or debugging history, and extract reusable rules, failure patterns, checklists, or skill candidates. Govern the full lesson lifecycle (observed → proposed → trial → approved → applied → deprecated → reverted) instead of producing a one-off summary.
---

# Project Retrospective

## Purpose

Turn a project into reusable knowledge instead of a one-off summary.

## 复盘粒度（先判断，再执行）

不要把所有任务都套用同一种完整复盘。先判定粒度，再决定最小产物：

| 模式 | 触发时机 | 最小产物 | 目的 |
|---|---|---|---|
| `micro-retro` | 单次任务、一次失败、一次返工或明显纠正之后 | 事实、原因、动作、是否值得记录 | 快速捕捉高价值错误，避免小问题被遗忘 |
| `project-retro` | 项目完成、暂停、重大偏航或阶段晋级 | 完整时间线、决策演化、排障链、复用规则与回写提案 | 总结项目级工作法与稳定骨架 |
| `meta-retro` | 多个同类项目或季度级经验评估 | 规则使用次数、失败率、节省时间、冲突规则、应废弃项 | 判断哪些经验真正有效 |

每轮复盘必须返回 `retro_level`（`micro-retro` / `project-retro` / `meta-retro`）。只有 `project-retro` 和 `meta-retro` 才考虑产生共享 Skill 回写提案。

## 证据分层（复盘结论必须标注证据类型）

复盘结论不能只依赖对话上下文。按要回答的问题选择首要证据，并在结论中标注证据类型：

| 要回答的问题 | 首要证据 | 字段 |
|---|---|---|
| 用户想解决什么、为何改变范围 | 用户明确确认、拒绝和反复反馈 | `conversation_evidence` |
| 代码、数据和报告是否按要求完成 | 命令、退出码、测试、运行日志、文件和 schema 检查 | `run_evidence` |
| 研究结论是否在正确样本和成本下成立 | PIT、覆盖、样本外、稳健性、成本容量和复现证据 | `research_evidence` |
| 结论是否改变了投资行为 | 判断快照、目标权重、实际权重、交易记录、人工覆盖和投委会决议 | `decision_evidence` |
| 判断后来是否有效 | 实现收益、风险暴露、成本、归因、基准比较和预测校准 | `outcome_evidence` |

对话证明意图，运行证据证明执行，投资结果证据才支持“这条经验提高了决策质量”。

## 经验影响评估字段

每轮 `project-retro` / `meta-retro` 在判断“写入哪里”之前，先填写影响字段，避免只写总结却不评估是否真的带来收益：

```yaml
efficiency:
  before_estimated_minutes:
  after_estimated_minutes:
  rework_reduced: []
quality:
  errors_prevented: []
  errors_remaining: []
decision_impact:
  changed_research_conclusion: false
  changed_portfolio_action: false
  evidence: []
outcome:
  realized_result:
  attribution: []
  calibration_review:
```

## 经验分流（先判断去向，再决定写哪里）

经验按性质分流，不要默认全部进入 Skill：

| 经验类型 | 推荐去向 |
|---|---|
| 一次性事实、决定和项目背景 | 项目复盘文档 |
| 稳定的触发条件、工作顺序和停止条件 | Skill |
| 稳定的输入输出结构 | 模板 / schema |
| 必须确定性执行的检查 | 脚本 / 验证器 |
| 投资原则、风险门槛和审批要求 | rules / policy |
| 模型参数、责任人和退役条件 | model card / registry |
| 项目特有路径、字段和临时修复 | 保留在项目内部 |

## 经验生命周期

经验进入共享库前后都必须有明确状态，不允许“复盘完成即生效”：

```yaml
status: observed|proposed|trial|approved|applied|deprecated|reverted
evidence_count: 0
source_retros:
  - project_id:
    location:
validation_cases: []
conflicts: []
owner:
review_after:
supersedes:
```

生命周期含义：

- `observed`：单次出现，仅记录，不进入 Skill。
- `proposed`：已形成回写提案，等待授权。
- `trial`：在受限范围试运行。
- `approved`：经复核批准。
- `applied`：已写入共享 Skill。
- `deprecated`：被后续证据证明无效或已过时。
- `reverted`：应用后因副作用回滚。

规则必须允许 `deprecated` 和 `reverted`。如果规则使用后没有减少错误、反而增加追问或误路由，应保留证据并回滚。

## 经验登记文件（可执行账本）

`project-retro` 和 `meta-retro` 的每个共享经验候选都必须对应根目录的
`../experience-registry.yaml` 登记项；`micro-retro` 默认只保留在项目复盘文档，除非用户明确要求登记。
登记项只能使用 `observed` 或 `proposed` 作为本轮初始状态，不能因为复盘完成就写成
`trial`、`approved` 或 `applied`。登记前先把项目特有路径、名称和一次性参数移出
`generalized_rule`，并填写 `experience_id`、`source_retros`、`target_type`、`target_path`、
`evidence_refs`、`validation_cases`、`owner` 和 `review_after`。

写入或更新登记文件后，必须运行：

```text
python ../experience-registry-validator.py --registry ../experience-registry.yaml
```

命令失败时，输出候选登记内容和失败原因，标记 `registry_sync=blocked`，不得声称登记完成。
登记文件是状态记录，不是自动修改共享 Skill 的授权开关；共享 Skill 的实际回写仍需单独授权、变更和回归验证。

## Skill 晋级条件

一条经验只有在以下条件同时满足时，才从 `observed` 晋级为 `proposed`：

1. 在两个独立任务中重复出现，或修复过一次重大错误，或明显减少返工；
2. 能写成“触发条件 → 动作 → 停止条件”；
3. 至少有一个正例和一个反例；
4. 已检查与现有规则的冲突；
5. 不依赖具体项目路径、页面名称、按钮名称或临时数据源；
6. 有负责人和复核日期。

进入 `approved` / `applied` 前还必须通过现有规则冲突检查与行为回归。

## 分离原则（硬约束）

- 复盘完成不等于自动修改共享 Skill；回写必须先形成 proposal，经授权后才应用。
- “Skill 值得复用”和“项目值得模板化”是两个独立判断：一个流程可能值得写入 Skill，但目录结构还不稳定，不应创建模板。
- 不因复盘完成就把 `proposed` 自动推进为 `applied`。

## Required deliverables

The deliverables depend on `retro_level`; do not require a full project package for a `micro-retro`:

- `micro-retro`: a minimal record of facts, cause, corrective action, and whether the observation is worth retaining. It does not produce a shared-skill write-back proposal unless the user explicitly asks for one.
- `project-retro` and `meta-retro`: a standalone retrospective document plus a separate shared-skill write-back proposal identifying reusable rules to add, tighten, or remove in `F:\Thomas\SharedSKILLS`.

For a full retrospective, save the standalone document as Markdown using the project’s existing convention (or `docs/retrospectives/` when no convention exists).

Optionally, the retrospective may also produce a third output:

3. A project template proposal or first-draft template asset set, but only when the project is stable enough to generalize **and** the user explicitly confirms that template creation is desired.

The write-back proposal is not the same as an applied change. Do not modify shared skills during the retrospective unless the user explicitly authorizes the write-back; label each item as `proposed`, `approved`, or `applied`.

## Operating rules

- Determine the retrospective level first (`micro-retro` / `project-retro` / `meta-retro`) and match the deliverable to that level.
- Reconstruct the project by timeline first: initial goal, major turns, rejected paths, final landing.
- Use the conversation context as the primary evidence of how the project evolved; treat static files as supporting evidence, not the whole story.
- Tag every conclusion with its evidence type (`conversation_evidence` / `run_evidence` / `research_evidence` / `decision_evidence` / `outcome_evidence`). Do not claim a decision-quality or outcome-level lesson from conversation evidence alone.
- When the dialogue is long or noisy, load `references/conversation-mining.md` and extract the decision trail before writing conclusions.
- When implementation or debugging is involved, reconstruct the diagnosis path too: symptom, first checks, eliminated causes, root cause, fix, verification.
- Separate facts, inferences, and opinions.
- Capture the interaction pattern: what the user cared about, what changed after feedback, and where the design tightened or drifted.
- Keep project-specific numbers, names, and one-time tradeoffs out of reusable guidance.
- For shared-skill write-back, generalize concrete project nouns into reusable roles and verbs before writing them.
- Promote only stable patterns into rules or skill candidates.
- Mark weak evidence explicitly as “推断” or “待确认”.
- Keep the output short and decision-oriented.
- If a lesson should change how future LLMs work, route it into the relevant skill under `F:\Thomas\SharedSKILLS`.
- Treat project template creation as an explicit optional branch, not as a default retrospective output.
- After completing the retrospective core analysis, explicitly ask the user whether they want to create a project template. Do not silently create one.
- Only recommend template creation when the project has a stable reusable skeleton: repeatable directory shape, stable config center, stable entrypoints, stable report/output pattern, and a clear separation between reusable structure and project-specific logic.
- If the project is too one-off, too unstable, or too theme-specific, say so directly and stop at the retrospective + write-back proposal.
- When template creation is approved, prefer repository-level documentation assets first. Default template asset path: `docs/templates/<template-id>/`.
- Unless the user explicitly asks for runnable scaffolding, template creation should default to design/spec assets, not executable code generators.

## Suggested output shape

每一轮复盘先给 `retro_level` 与 `evidence_manifest`，再按粒度填充对应交付物。详细字段见 `references/output-template.md`。

### 交付物 A：项目复盘文档

1. 项目结论
2. 过程时间线
3. 关键交互与决策演化
4. 排障与验证链路
5. 成功经验
6. 失败 / 风险
7. 可复用规则
8. 不建议沉淀为 skill 的细节
9. 模板化判断
10. 下次同类项目检查清单
11. 证据清单（按 `conversation_evidence` / `run_evidence` / `research_evidence` / `decision_evidence` / `outcome_evidence` 分列）
12. 影响评估（`efficiency` / `quality` / `decision_impact` / `outcome`）
13. 经验分流与生命周期状态（`observed` → `proposed` → `trial` → `approved` → `applied` → `deprecated` → `reverted`）
14. 登记文件同步结果（`registry_path`、`experience_ids`、`registry_sync`、校验命令与退出码）

### 交付物 B：共享 skill 回写建议

15. 回写目标、抽象后的规则、变更类型、理由和状态（状态只能是提案，不因复盘完成而自动应用）

### 交付物 C：项目模板提案或模板资产草案（仅在用户确认后）

16. 模板定位与适用范围
17. 应抽取的通用骨架
18. 必须保留在具体项目中的特有逻辑
19. 模板产物目录约定
20. 模板首批文件清单

## Skill write-back

When the retrospective surfaces reusable behavior, produce a write-back block for the shared skill library:

- target skill in `F:\Thomas\SharedSKILLS`
- what to add, remove, or tighten
- whether it is an update to an existing skill or a candidate for a new one
- why it is stable enough to reuse
- rewrite each candidate as a general rule before writing it back; do not copy page names, button labels, file paths, or one-off field names
- prefer patterns like “separate authority data from derived data”, “keep analysis inside the relevant object context”, or “fail fast on invalid inputs” over project-specific wording
- label every candidate with a lifecycle status (`observed` / `proposed` / `trial` / `approved` / `applied` / `deprecated` / `reverted`) and record `owner` plus `review_after`
- only mark a candidate as `proposed` when it passes all six `Skill 晋级条件`; do not auto-apply

Only write back patterns that are repeated, stable, and not tied to one project’s paths, names, or deadlines.

## Template creation branch

When the retrospective identifies reusable structure, handle template creation with this decision sequence:

1. Finish the retrospective first.
2. State whether the project appears template-worthy, with evidence.
3. Ask the user explicitly whether to create a project template.
4. Only after approval, produce either:
   - a template proposal, or
   - a first-draft template asset set.

### Template-worthiness checks

A project is a good template candidate only when most of the following are true:

- it is not a one-off project;
- future sibling projects are likely;
- the directory shape is already stable;
- the config center is already stable;
- the runtime entrypoints are already stable;
- the report/output structure is already stable;
- the reusable skeleton can be separated from project-specific indicators, thresholds, or topic logic.

### Template asset directory convention

When template creation is approved, use the repository-level template path:

- `docs/templates/<template-id>/README.md`
- `docs/templates/<template-id>/template-spec.md`
- `docs/templates/<template-id>/template-checklist.md`
- `docs/templates/<template-id>/config.example.yaml` or `preregistration.example.yaml`
- `docs/templates/<template-id>/report-outline.example.md`

If the project is only mature enough for a template proposal, keep the proposal in the retrospective document and do not create the template directory yet.

## Boundary

If the user is asking about progress, stage, drift, or the next milestone, use `quant-project-review` instead. If the user is asking how to implement or fix something, switch to the relevant build/debug skill.

## Reference

Load `references/output-template.md` when you need the exact reporting scaffold or a tighter rule for deciding what should become a reusable skill.
Load `references/conversation-mining.md` when you need a dialogue-first timeline, a decision trail, or a diagnosis trail from a long project chat.
