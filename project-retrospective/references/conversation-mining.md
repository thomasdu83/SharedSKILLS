# Conversation Mining for Project Retrospectives

Use this reference when the project is spread across a long chat and the final answer must reflect the actual implementation journey, not just the ending state.

## Scope（本文件只挖掘 conversation_evidence）

本文件只负责从对话中提取 `conversation_evidence`，用于回答“用户想解决什么、为何改变范围”。它不能单独证明代码是否跑通、研究结论是否成立、投资行为是否改变或判断后来是否有效。

五类证据的分工如下，其余四类证据在本文件中不展开：

- `conversation_evidence`：本文件提取的对象。
- `run_evidence`：来自命令、退出码、测试、运行日志、文件与 schema 检查。
- `research_evidence`：来自 PIT、覆盖、样本外、稳健性、成本容量与复现证据。
- `decision_evidence`：来自判断快照、目标权重、实际权重、交易记录、人工覆盖与投委会决议。
- `outcome_evidence`：来自实现收益、风险暴露、成本、归因、基准比较与预测校准。

## What to extract first

1. Initial problem statement.
2. Every explicit user correction or narrowing of scope.
3. Every rejected option and the reason it was rejected.
4. Every requirement that became non-negotiable.
5. The final stable design.

## Turning points to look for

Treat these as decision pivots:

- the user changes the target outcome;
- the user removes a feature or simplifies scope;
- the user insists on a different interaction pattern;
- a bug or screenshot reveals the current design does not match intent;
- the user confirms one option and later reverses it;
- a later requirement makes an earlier design obsolete.

## Conversation evidence priority

From strongest to weakest (within `conversation_evidence` only):

1. explicit user confirmations;
2. explicit user rejections;
3. repeated user feedback across turns;
4. observed bugs or screenshots tied to the request;
5. final static files and config;
6. inferred intent.

## How to synthesize

- Build a short timeline: start, turns, convergence, final landing.
- Separate “what happened” from “why it mattered”.
- Distinguish one-off implementation detail from stable project rule.
- Record the interaction pattern if it changed the design: simplification, deletion, move-down in hierarchy, or splitting one control into two.
- When a bug or visualization issue appears, extract the diagnostic sequence explicitly: symptom → data check → algorithm check → rendering check → browser/environment check → verification.
- When a requirement is repeatedly narrowed, summarize the net effect as a design principle, not as a feature list.

## What becomes reusable

Promote only patterns that are:

- repeated across turns or projects;
- stable enough to change future behavior;
- not tied to one path, button label, or temporary workaround.
- generalizable without naming the current project’s pages, buttons, fields, or folders.

## How to rewrite for shared skill write-back

Rewrite concrete observations into reusable rules before sending them to `F:\Thomas\SharedSKILLS`.

- Convert object lists into behavior rules.
- Convert page names into role names.
- Convert button names into action patterns.
- Convert file paths into storage or authority roles.
- If the rewritten sentence still reads like a project-specific note, keep it local instead of writing it back.
- Treat page modules, tabs, cards, and sections as local UI labels unless they encode a durable behavioral rule.

Example:

- Local observation: “某些管理页面和研究页面要分开。”
- Reusable rule: “把管理动作和分析动作分离，并把分析能力放到对应对象上下文里。”

## What should stay local

Keep these out of long-lived skill guidance:

- exact file paths;
- one-time UI wording;
- transient debug output;
- single-project naming decisions;
- fixes that only matter in one environment.

## Output tip

When the dialogue is long, write the retrospective in this order:

1. timeline;
2. decision changes;
3. stable rules;
4. write-back targets in `F:\Thomas\SharedSKILLS`.
