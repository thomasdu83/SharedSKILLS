# MyNotes Path Policy

Vault root:

```text
F:\Thomas\MyNotes
```

## Default Decision Order

1. Honor the user's explicit destination.
2. Classify the material role.
3. Match the domain and nearby existing notes.
4. Decide whether the material deserves a project.

Use this practical test: place the note where the user is most likely to look for it six months later.

## Area Responsibilities

| Location | Use for |
|---|---|
| `000 Inbox` | Temporary capture, unprocessed source files, and intake notes. |
| `100 Projects` | Active research topics with objectives, deliverables, data, code, or implementation. |
| `200 Areas` | Durable domain knowledge, frameworks, ongoing research areas, and investment conclusions. |
| `300 Resources` | Reusable external references, methods, source cards, and source library materials. |
| `400 Archive` | Historical, completed, stale, or audit-only materials. |
| `500 Journal` | Temporary dated thinking before promotion. |
| `900 Assets` | Templates, Dataview queries, scripts, and operational assets. |

## Source Material Placement

`000 Inbox` is not permanent storage. After AI creates intake and draft knowledge notes, suggest one stable destination:

| Source type | Suggested stable location |
|---|---|
| Project material | `100 Projects/<project>/Sources/` |
| General reusable source | `300 Resources/Source Library/<domain>/<year>/` |
| Audit/history-only source | `400 Archive/ResourcesArchive/<year>/` |
| Temporary extraction/OCR/cache | Exclude from knowledge base and clean when safe. |

Never move, rename, delete, overwrite, or de-duplicate original source materials without explicit user confirmation in the current conversation.

## Cross-Topic Material Rule

When one document belongs to multiple topics, default to a single original-file location instead of keeping parallel copies in multiple theme folders.

- Choose the primary home by stable retrieval: where the user is most likely to look for the original file six months later.
- In other topic notes, use Markdown links, `source_files`, reference sections, or MOCs to point to the original.
- Duplicate the original file only when the user explicitly requests it or when there is a clearly separate operating workflow that needs an independent local copy.

## Default Domain Hints

| Content | Likely destination |
|---|---|
| Fund investment, FOF, manager research, fixed-income funds | `200 Areas/210 资产配置/215 基金投资/` |
| Macro, asset allocation, cross-asset frameworks | `200 Areas/210 资产配置/` |
| AI workflows, prompts, knowledge system design | `200 Areas/230 AI研究/` or `900 Assets/` when operational. |
| Stable methods, skills, reusable research techniques | `300 Resources/` |
| Code, data, backtests, models, running systems | Link to `F:\Thomas\QuantSystem`; do not store as MyNotes knowledge notes. |

## Intake Retention

- Ordinary intake logs can be deleted after about one month once the stable note exists and the source file is placed.
- Important investment, ODD, decision, or audit-related intake logs can be archived under `400 Archive/ResourcesArchive/AI Intake Logs/<year>/`.
- Intake is a processing log, not the final knowledge layer.

## Exclusion Rules

Do not index or preserve as knowledge:

- `.obsidian`, `.trash`, `.stfolder`
- `__codex_extract`, `__pdf_pages`, `__pdf_previews`, `__tmp_pdf_preview`, `__pycache__`
- OCR scratch files, rendered preview images, temporary HTML
- `~$*` Office temporary files
- `sync-conflict`, `.old`, `.log`, `.rels`, `.xml`, `.xsd`
- Unreferenced attachments or extracted intermediate text
