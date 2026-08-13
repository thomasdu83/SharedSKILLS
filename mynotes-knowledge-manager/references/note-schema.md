# MyNotes Note Schema

Use Obsidian-compatible Markdown with YAML frontmatter and wikilinks.

## Standard Frontmatter

Use this default shape for stable knowledge notes:

```yaml
created:
updated:
area:
domain:
type:
status:
stage:
confidence:
source_files:
related_notes:
related_project:
quant_system_path:
ai_owned:
human_review_required:
last_reviewed:
review_after:
stale: false
tags:
```

Recommended values:

| Field | Values |
|---|---|
| `status` | `inbox`, `processing`, `active`, `filed`, `archived` |
| `stage` | `raw`, `extracted`, `synthesized`, `validated` |
| `confidence` | `low`, `medium`, `high` |
| `type` | `inbox-intake`, `knowledge-note`, `source-card`, `project-hub`, `method`, `decision`, `moc` |

Use document-level evidence by default:

```yaml
source_files:
  - "[[source-file.pdf]]"
```

Do not add page, table, or quote-level evidence unless the user asks or the conclusion is unusually sensitive.

## Intake Note

Create an intake note for new raw material, especially material in `000 Inbox`.

Default filename:

```text
<source-stem>_ai-intake.md
```

Default sections:

```markdown
# <source title> - AI Intake

## Material Type

## Suggested Destination

## Why This Destination

## Main Takeaways

## Related Existing Notes

## Knowledge Potential

## Human Review Questions

## Source Material Status
```

Keep intake factual and operational. The stable knowledge note carries the reusable conclusion.

## Knowledge Note

Default sections:

```markdown
# <knowledge title>

## Core Idea

## Framework Or Method

## Application

## Limits And Caveats

## Related Notes

## Sources
```

Adjust sections to fit the material. Prefer conclusion-led headings for investment research.

When the note covers a difficult mechanism, algorithm, or abstract framework, add an optional section such as:

```markdown
## Plain-Language Explanation

Explain the mechanism in practical language. Prefer short intuitive scenarios, analogies, or behavior-based descriptions that answer "what is this really saying in the real world?"
```

For method-heavy notes, a useful layered structure is:

1. Formal definition or key formulas
2. Intuitive example or minimal worked example
3. Plain-language explanation

Use only the layers that materially improve understanding; do not add mechanical sections when the topic is already simple.

## Duplicate And Merge Rules

- If no stable topic exists, create a new note.
- If a stable topic exists, update that note instead of creating another parallel summary.
- If the new source conflicts with existing notes, add a "Conflicts Or Open Questions" section.
- If the topic grows beyond one note, suggest a MOC or project hub.
- If the file is a true duplicate, ask the user before deleting or moving any copy.

## Promotion Rules

- Raw material with reusable insight becomes `stage: synthesized`.
- After chat-based human review, it may become `stage: validated`.
- Unreviewed but useful drafts keep `human_review_required: true`.
- Time-sensitive conclusions may include `review_after` and `stale`.
