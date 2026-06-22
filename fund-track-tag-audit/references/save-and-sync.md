# Save and Sync Workflow

This workflow makes the archived Markdown report the source of truth. The conversation should display only content that has already passed validation and sync, or clearly label unsynced content as a draft.

Before running this workflow, resolve the shared runtime variables used by the skill:

- `$WORKSPACE_ROOT`: current repository root
- `$SKILL_ROOT = Join-Path $WORKSPACE_ROOT ".trae\skills\fund-track-tag-audit"`
- `$REPORT_BUFFER = Join-Path $SKILL_ROOT "latest_report.md"`
- `$PYTHON_EXE`: user-provided interpreter path, else `$WORKSPACE_ROOT\.venv\Scripts\python.exe` if present, else a `python` that can import required packages

## Required Order

1. Generate one Markdown report in the exact `references/output-templates.md` format.
2. Write it to:

```text
$REPORT_BUFFER
```

3. Validate the buffer:

```powershell
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\validate_audit_report.py") $REPORT_BUFFER --strict
```

4. Sync the validated buffer to the final archive path:

```powershell
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\sync_to_y.py") "Y:\投顾管理人研究\fund-track-tag-audit\funds\<YYYYMMDD-HHMMSS_基金简称_策略标签审核>.md"
```

5. Verify the target file exists and can be read. Only then show the report result in the conversation.

## Conversation Display

- Single fund: show a compact conclusion, evidence strength, key field changes, and the saved path first. Show the full six-section report only when it is short or the user needs the full text inline.
- Multiple funds: save every single-fund report; show one compact comparison summary. Save the batch summary only when the user explicitly requests it.
- Historical report reuse: show the saved report path and audit time; do not describe it as a fresh result.

## Failure Handling

- Validation failure: do not sync. Tell the user the report draft failed validation and summarize the validation errors.
- Sync failure: tell the user the report draft is in `latest_report.md` but was not archived. Do not call it the official report.
- Target verification failure: treat it as a sync failure even if `sync_to_y.py` printed success.

## Forbidden Methods

Do not save Chinese Markdown report bodies with `python -c`, PowerShell here-strings, shell pipes, or `Out-File`. These paths have caused quoting or encoding loss under the IDE sandbox. Use the fixed buffer plus `sync_to_y.py` only.
