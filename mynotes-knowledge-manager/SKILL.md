---
name: mynotes-knowledge-manager
description: Use when the user asks to manage, ingest, deposit,沉淀,整理,归档,处理 Inbox/intake, create or update Obsidian notes, build an AI knowledge base, maintain MOC maps, place source materials, or query/reuse knowledge inside F:\Thomas\MyNotes. Use for MyNotes-specific human+AI knowledge workflows involving PDFs, DOCX files, Markdown notes, temporary thoughts, research reports, investment notes, and QuantSystem link placeholders.
---

# MyNotes Knowledge Manager

## Overview

Use this skill to help the user manage `F:\Thomas\MyNotes` as an Obsidian-compatible human+AI knowledge base. The core contract is: AI drafts, routes, links, and asks review questions; the user validates important knowledge and confirms any original-material move or deletion.

## Load References As Needed

- Read `references/path-policy.md` before routing notes, suggesting destinations, or handling source files.
- Read `references/note-schema.md` before creating or updating intake notes, knowledge notes, project hubs, or frontmatter.
- Read `references/human-review-gate.md` before marking a note as validated, moving original materials, or finalizing investment-sensitive knowledge.
- Read `references/moc-policy.md` before creating or updating any MOC.
- Read `references/quant-system-linking.md` when a source mentions code, data, models, backtests, portfolio construction, or `F:\Thomas\QuantSystem`.

## Standard Workflow

1. Locate the source material or note. If the filename is ambiguous, list candidates and ask the user to choose.
2. Inspect vault context by filenames first with `rg --files`; read only relevant notes/templates needed for routing or merge decisions.
3. Classify the material by role: temporary inbox item, reusable knowledge, source/reference, active research project, archive-only material, or journal thought.
4. Create or update an intake note when processing new raw material. If the source is in `000 Inbox`, place the intake beside it using `<source-stem>_ai-intake.md`.
5. Create or update the stable note in the recommended MyNotes location. Prefer updating an existing topic note over creating parallel summaries.
6. Use document-level evidence by default: populate `source_files` with links to source documents. Do not require page/table/quote-level evidence unless the user asks.
7. When the source contains a mechanism, model, algorithm, or economic logic that is hard to understand, add a plain-language explanation layer in the stable note. Prefer short intuitive descriptions, concrete scenarios, or analogies that clarify what the mechanism is really saying in practice.
8. Pause for the chat-based human review gate before marking `stage: validated`, moving original materials, deleting duplicates, or finalizing investment/ODD/manager/fund conclusions.
9. After approval, update frontmatter, links, MOC entries when warranted, and any confirmed source-material placement.
10. Finish with a concise report: created/updated notes, unresolved review points, original-material status, and suggested next action.

## Mandatory Rules

- User-specified destination wins over default routing unless it would break vault safety.
- Never move, rename, delete, overwrite, or de-duplicate original source materials without explicit user confirmation in the current conversation.
- For cross-topic materials, default to a single original-file home plus links from other topic notes or MOCs. Do not duplicate original files across themes unless the user explicitly asks or there is a clearly separate operating need.
- Do not mark investment conclusions, manager/product judgments, ODD risk calls, or QuantSystem-affecting notes as `validated` until the user answers the review gate.
- Keep MyNotes human-readable and Obsidian-compatible. Prefer Markdown, frontmatter, wikilinks, and stable relative vault paths.
- For difficult methods, mechanisms, or abstract frameworks, prefer a three-layer explanation when useful: formal definition, intuitive example, and plain-language explanation. Do not force all three when the material is simple.
- Do not make every folder a MOC. Create MOCs only at global, important-domain, or important-topic levels when they improve retrieval.
- Treat `000 Inbox` as a buffer, not a permanent source library.
- Treat QuantSystem as the place for code, data, backtests, models, and runnable outputs. MyNotes records the research interpretation and links to QuantSystem paths.
- Exclude extraction caches, OCR scratch files, rendered previews, Office temp files, sync conflicts, and unreferenced attachments from knowledge indexing.

## Routing Defaults

When the user does not provide a destination, decide in this order:

1. User explicit instruction.
2. Material role.
3. Domain and existing nearby notes.
4. Whether the material should become a project.

Default placements:

- `000 Inbox` - temporary capture and intake notes.
- `100 Projects` - active research topics with explicit objective, deliverables, data, code, or implementation path.
- `200 Areas` - durable domain knowledge, frameworks, investment research conclusions, and ongoing responsibility areas.
- `300 Resources` - reusable external references, methods, source cards, and source library files.
- `400 Archive` - historical, completed, stale, or audit-only materials.
- `500 Journal` - temporary thinking and dated reflections before possible promotion.
- `900 Assets` - templates, queries, scripts, and non-knowledge operational assets.

## Review Gate

Ask a small number of concrete questions in chat. Typical questions:

- Is the core conclusion accurate?
- Is the recommended destination acceptable?
- Should this become durable knowledge, reference-only material, or a project?
- May this note be marked `stage: validated`?
- May the original source file be moved to the suggested stable location?

If the user skips validation, keep `stage: synthesized`, set `human_review_required: true`, and make clear that the note is usable as draft context but not as high-confidence knowledge.

## Query And Reuse

When the user asks to search, reuse, or answer from MyNotes:

- Prefer `stage: validated` and `stage: synthesized` notes over raw extracts.
- State whether the answer is based on validated knowledge, draft notes, or raw sources.
- If conflicting notes exist, surface the conflict instead of choosing silently.
- For investment-sensitive answers, ask whether the user wants a quick answer or a reviewed answer.

## Common Phrases

Use this skill for requests like:

- "把这篇研报沉淀到 MyNotes"
- "处理 Inbox 里的这份 PDF"
- "帮我建立 AI 知识库"
- "这篇文档应该归档到哪里"
- "更新基金投资的 MOC"
- "把这个临时思考升格成长期知识"
- "这篇材料是否应该成为课题研究"
- "查询 MyNotes 里关于固收基金评价的知识"
