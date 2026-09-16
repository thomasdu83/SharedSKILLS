# Routing Cases

These cases validate when `research-monitor-contracting` should route in, and when a
neighboring skill should remain primary.

## Route In

### Case R1: Research to monitoring contract

**Prompt**

```text
把这几篇行业研究报告中的判断逻辑、证据指标、阈值来源和人工确认项整理成可交给后续监控项目实现的契约。
```

**Expected primary route**

- `research-monitor-contracting`

**Why**

- user explicitly wants a monitoring contract
- task is between research understanding and engineering implementation

### Case R2: Convert research views into monitorable rules

**Prompt**

```text
我不是要摘要，请把这篇策略报告里的观点拆成判断逻辑、规则、证据指标和数据要求。
```

**Expected primary route**

- `research-monitor-contracting`

## Route Elsewhere

### Case O1: Pure summary

**Prompt**

```text
请总结这篇报告的主要结论、证据和风险提示。
```

**Expected primary route**

- direct analysis or `research-report-writer`

**Should not route to**

- `research-monitor-contracting`

### Case O2: Replication and reproducibility review

**Prompt**

```text
请审核这篇论文的方法能否复现，哪些公式、样本区间和成本假设没有交代清楚。
```

**Expected primary route**

- `investment-paper-replication`

**Should not route to**

- `research-monitor-contracting`

### Case O3: QuantSystem implementation

**Prompt**

```text
监控契约已经确认，请把它正式实现到 QuantSystem 项目里。
```

**Expected primary route**

- `quant-develop`

**Should not route to**

- `research-monitor-contracting`

### Case O4: Public data onboarding

**Prompt**

```text
请把这个公开数据源接入平台数据层，并把所需序列写入数据库。
```

**Expected primary route**

- `public-data-collector`

**Should not route to**

- `research-monitor-contracting`

### Case O5: Reader-facing HTML implementation

**Prompt**

```text
把现有监控结果做成一个更适合阅读的静态 HTML 报告。
```

**Expected primary route**

- `frontend-report-page`

**Should not route to**

- `research-monitor-contracting`

## Escalate Before Contracting

### Case E1: Source conflict must be reviewed first

**Prompt**

```text
两篇报告对同一个逻辑的阈值和定义冲突很大，你先判断哪个可信，再整理成监控方案。
```

**Expected primary route**

- `investment-paper-replication` or equivalent source-review path first

**Only after review**

- `research-monitor-contracting`

### Case E2: User requests code immediately without contract

**Prompt**

```text
别整理规则了，直接帮我把这篇报告里的逻辑写成代码。
```

**Expected primary route**

- usually `quant-research-coding` or `quant-develop`, depending on scope

**Why**

- user is explicitly skipping contracting
- this skill should not force itself in when the intent is direct implementation

## Routing Assertions

Before publication, the draft should satisfy all assertions below:

- mentioning a report alone must not trigger this skill
- mentioning indicators alone must not trigger this skill
- mentioning monitoring alone must not trigger this skill
- explicit intent to create a monitoring contract should trigger this skill
- unresolved source contradictions should route to source review before contracting
- already-confirmed contracts should route downstream rather than back into contracting
