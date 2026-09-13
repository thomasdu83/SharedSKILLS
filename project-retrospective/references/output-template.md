# Project Retrospective Template

Use this template to reconstruct the project from the conversation process first, then decide what should be kept as reusable knowledge.

## Output template

### 0. 交付要求
- 先判定 `retro_level`：`micro-retro` / `project-retro` / `meta-retro`，再决定产物范围
- `micro-retro` 只产出最小记录：事实、原因、动作和是否值得保留；不强制完整项目文档
- `project-retro` / `meta-retro` 必须产出完整项目复盘文档
- 必须产出共享 skill 回写建议（仅 `project-retro` / `meta-retro`）
- 回写建议与实际修改分开：默认先提案，只有授权后才应用
- 模板创建不是默认动作；只有在项目具备稳定共性且用户明确确认后，才进入模板化分支
- “Skill 值得复用”和“项目值得模板化”是两个独立判断

### 1. 项目结论
- 一句话结论
- 是否达成目标
- 最值得记住的结果

### 1A. micro-retro 最小记录（仅 `micro-retro`）
- 发生了什么事实：
- 根因或触发条件：
- 已采取/建议采取的动作：
- 是否值得登记：是 / 否 / 待确认
- 若登记：初始状态只能是 `observed` 或 `proposed`

### 2. 过程时间线
- 起点：用户最初想解决什么
- 中段：需求如何被连续反馈改写
- 转折：哪些提议被否掉、哪些被保留
- 收口：最终方案怎么稳定下来

### 3. 关键交互与决策演化
- 用户真正关心的点
- 哪些要求从“可选”变成“硬约束”
- 哪些细节是反复被强调后才稳定下来的
- 哪些结论来自对话过程，而不是静态文件

### 4. 排障与验证链路
- 表象是什么
- 先查了哪一层
- 哪些原因被排除
- 根因是什么
- 最终怎么验证修复

### 5. 成功经验
- 哪些做法有效
- 哪些设计可以复用
- 哪些是跨项目稳定模式

### 6. 失败 / 风险
- 主要问题
- 触发原因
- 可避免的红线

### 7. 可复用规则
- 只写会改变未来行为的规则
- 写成可执行的检查项
- 优先抽象成“以后遇到同类场景就怎么做”
- 兼顾“工作法、设计原则、排障顺序、交付习惯”四类稳定经验

### 8. 不建议沉淀为 skill 或模板的细节
- 项目特有数字
- 单次环境约束
- 一次性权衡
- 只对当前项目成立的命名或路径

### 9. 模板化判断
- 是否值得模板化：是 / 否 / 待确认
- 判断理由：
- 哪些结构已经稳定：
- 哪些部分仍然过于项目特定：
- 是否需要先询问用户是否建立模板：是（默认） / 否

### 10. 下次同类项目检查清单
- 先还原对话过程
- 先找反复出现的偏好
- 先分清事实和推断
- 先判断是否值得升级为 skill

### 11. 回写到共享 skill
- 目标 skill：`F:\Thomas\SharedSKILLS\...`
- 变更类型：新增 / 修改 / 删除
- 建议写入的具体条目：
- 状态：observed / proposed / trial / approved / applied / deprecated / reverted（默认 `proposed`，不因复盘完成而自动 `applied`）
- 是否满足 Skill 晋级条件：是 / 否（逐条对照）
- 是否足够稳定，值得沉淀：是 / 否 / 待确认
- 负责人：
- 复核日期：
- 备注：

### 12. 模板提案（仅在用户确认后）
- 模板 ID：
- 模板定位：
- 适用范围：
- 不适用范围：
- 应抽取的共性骨架：
- 必须留在具体项目中的主题逻辑：

### 13. 模板产物目录约定（仅在用户确认后）
- `docs/templates/<template-id>/README.md`
- `docs/templates/<template-id>/template-spec.md`
- `docs/templates/<template-id>/template-checklist.md`
- `docs/templates/<template-id>/config.example.yaml` 或 `preregistration.example.yaml`
- `docs/templates/<template-id>/report-outline.example.md`
- 若项目尚未成熟到可直接建模板目录，则只保留模板提案，不创建目录

### 14. 证据清单（五类证据）
复盘结论必须标注证据类型，禁止只靠对话上下文证明执行或投资结果：

- `conversation_evidence`：用户明确确认、拒绝、反复反馈
- `run_evidence`：命令、退出码、测试、运行日志、文件与 schema 检查
- `research_evidence`：PIT、覆盖、样本外、稳健性、成本容量、复现证据
- `decision_evidence`：判断快照、目标权重、实际权重、交易记录、人工覆盖、投委会决议
- `outcome_evidence`：实现收益、风险暴露、成本、归因、基准比较、预测校准

### 15. 影响评估
判断“写入哪里”之前先填影响字段，避免只写总结却不评估收益：

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

### 16. 经验分流（去向）
| 经验类型 | 推荐去向 |
|---|---|
| 一次性事实、决定和项目背景 | 项目复盘文档 |
| 稳定的触发条件、工作顺序和停止条件 | Skill |
| 稳定的输入输出结构 | 模板 / schema |
| 必须确定性执行的检查 | 脚本 / 验证器 |
| 投资原则、风险门槛和审批要求 | rules / policy |
| 模型参数、责任人和退役条件 | model card / registry |
| 项目特有路径、字段和临时修复 | 保留在项目内部 |

### 17. 经验生命周期
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

- `observed`：单次出现，仅记录，不进入 Skill。
- `proposed`：已形成回写提案，等待授权。
- `trial`：在受限范围试运行。
- `approved`：经复核批准。
- `applied`：已写入共享 Skill。
- `deprecated`：被后续证据证明无效或已过时。
- `reverted`：应用后因副作用回滚。

规则必须允许 `deprecated` 和 `reverted`。

### 18. 登记文件同步
- 登记文件：`../experience-registry.yaml`
- 本轮登记的 `experience_id`：
- 初始状态：`observed` / `proposed`
- `registry_sync`：`written` / `blocked` / `not_applicable`
- 校验命令：`python ../experience-registry-validator.py --registry ../experience-registry.yaml`
- 校验退出码：
- 若校验失败：完整错误、候选登记内容与下一步修复动作：

## Write-back abstraction rule

Before writing back, rewrite any candidate into a domain-neutral rule.

- Bad: list concrete page names, button labels, module names, file paths, or one-off fields.
- Good: express the stable behavior behind them as a reusable pattern.
- Prefer verbs and relations: separate, group, isolate, preview, fail fast, freeze, split, or route by context.
- If a point cannot be generalized without naming the current project, keep it local instead of writing it back.

## Promote-to-skill rule

Create or update a reusable skill only when the pattern is:
- repeated across projects,
- stable enough to guide future behavior, and
- not tied to one data source, one UI, or one-off deadline pressure.

Skill 晋级条件（一条经验只有在以下条件同时满足时，才从 `observed` 晋级为 `proposed`）：

1. 在两个独立任务中重复出现，或修复过一次重大错误，或明显减少返工；
2. 能写成“触发条件 → 动作 → 停止条件”；
3. 至少有一个正例和一个反例；
4. 已检查与现有规则的冲突；
5. 不依赖具体项目路径、页面名称、按钮名称或临时数据源；
6. 有负责人和复核日期。

进入 `approved` / `applied` 前还必须通过现有规则冲突检查与行为回归。规则必须允许 `deprecated` 和 `reverted`。

## Template promotion rule

Promote a retrospective into a project template only when:
- future sibling projects are likely,
- the skeleton is more reusable than the topic logic,
- config / entrypoints / output structure are already stable,
- and the user explicitly confirms that template creation is desired.
