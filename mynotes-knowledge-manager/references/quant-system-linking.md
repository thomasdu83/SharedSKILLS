# QuantSystem Linking

QuantSystem is important but should remain a separate execution system.

Default path:

```text
F:\Thomas\QuantSystem
```

## Boundary

| MyNotes | QuantSystem |
|---|---|
| Research questions, source interpretation, conclusions, caveats, decisions, MOC navigation | Code, data pipelines, backtests, portfolio construction, models, configs, runnable outputs |

Do not create or modify QuantSystem projects unless the user explicitly asks. For MyNotes ingestion, only record links or placeholders.

## Fields To Reserve

Use these fields when relevant:

```yaml
related_project:
quant_system_path:
data_version:
run_command:
output_path:
result_summary:
```

## When A Note Becomes A Project

Suggest projectization when a topic has:

- A clear research question.
- Multiple sources, data, or experiments.
- Expected deliverables.
- Code, model, backtest, dashboard, or investment workflow output.
- A need for repeated updates or production use.

If the user agrees, create a MyNotes project hub first. QuantSystem implementation is a separate follow-up unless explicitly requested.

## Minimal Project Hub Link Pattern

```markdown
# <Project Name> ProjectHub

## Objective

## Research Questions

## Sources

## Notes

## Decisions

## QuantSystem Link

- Path:
- Data version:
- Run command:
- Output path:

## Next Actions
```
