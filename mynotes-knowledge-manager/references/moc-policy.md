# MOC Policy

MOC means map of content: a navigation and synthesis layer, not a folder index.

## Where To Create MOCs

Use three levels only:

| Level | Location |
|---|---|
| Global | `F:\Thomas\MyNotes\00_MOC_MyNotes知识地图.md` |
| Important domain | Near the domain root, e.g. `200 Areas/210 资产配置/215 基金投资/00_MOC_基金投资.md` |
| Important topic | Near a mature topic with repeated use and multiple stable notes. |

Projects use `00_ProjectHub.md`, not MOC.

## When To Create Or Update A MOC

Create or update a MOC only when at least one condition is true:

- The topic has several stable notes and is likely to grow.
- The user repeatedly searches or works in the topic.
- The topic bridges multiple folders and needs a deliberate navigation layer.
- A new note changes the conceptual map of an important domain.

Do not create a MOC merely because a folder exists.

## What A MOC Should Contain

Use concise sections:

```markdown
# 00_MOC_<topic>

## Core Questions

## Key Frameworks

## Important Notes

## Active Projects

## Source Libraries

## Open Questions
```

Keep MOCs link-dense and short. They should help retrieval, not duplicate full note content.

## Update Rules

- Add links to validated and high-value synthesized notes.
- Mark draft links clearly when `human_review_required: true`.
- Surface conflicts or stale conclusions in one short line.
- Avoid copying long summaries from child notes.
