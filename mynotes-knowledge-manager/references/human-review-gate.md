# Human Review Gate

Human review is a lightweight chat checkpoint, not a formal approval system inside Obsidian.

## Why Review

Review prevents AI from turning a plausible summary into a durable false memory. It is especially important for investment conclusions, manager/product judgments, ODD risk calls, and anything that may affect QuantSystem assumptions or outputs.

## When Required

Require chat-based review before:

- Marking `stage: validated`.
- Moving, renaming, deleting, or de-duplicating original source files.
- Finalizing investment conclusions, fund/manager assessments, ODD judgments, or model-impacting claims.
- Creating a new project or binding a note to a QuantSystem path.
- Updating a high-level MOC conclusion, not just adding a link.

## How To Review In Chat

Ask only the few questions needed to unblock the next operation. Use concrete questions such as:

1. Is the core conclusion accurate?
2. Is the recommended destination acceptable?
3. Should this be durable knowledge, reference-only material, or a project?
4. May I mark this note as `stage: validated`?
5. May I move the original source file to the suggested stable location?

For investment-sensitive material, add:

- Are there caveats or constraints that must stay attached to the conclusion?
- Is this only research context, or can it support future decisions?

## If The User Confirms

- Update `stage` to `validated` only for the reviewed note.
- Set `human_review_required: false` when all required checks are complete.
- Set `last_reviewed` to the current date.
- Move or archive original material only if the user explicitly approved that action.

## If The User Does Not Review

It is acceptable to leave the note unreviewed:

```yaml
stage: synthesized
human_review_required: true
confidence: medium
```

Tell the user that the note is usable as draft context, but should not be treated as high-confidence knowledge.

## Light Update And Expiry

Use light review fields only for time-sensitive knowledge:

```yaml
last_reviewed:
review_after:
stale: false
```

Suggested defaults:

- Inbox older than 7 days: remind.
- Extracted but unsynthesized older than 14 days: remind.
- Synthesized but unreviewed older than 30 days: remind.
- Market views, macro conclusions, fund evaluations: review in 3-6 months.
- Methods and skill documents: review yearly or when used.
