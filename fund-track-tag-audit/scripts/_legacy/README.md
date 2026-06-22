# Legacy SMB Pipeline (Deprecated)

These scripts were part of the old SMB-based audit pipeline. They have been superseded by the native LLM tool-chain workflow described in `SKILL.md`.

**Do not use these scripts.** The new workflow uses Trae/IDE native tools (Glob, LS, Read, SearchCodebase) directly — no Python SMB client, no local file copying, no text extraction pipeline.

| Script | Role (old) | Replaced By |
|---|---|---|
| `audit_fund_tracks.py` | End-to-end audit orchestrator | SKILL.md Phase 1–6 |
| `collect_manager_files.py` | SMB directory scan + local copy | Glob + LS in workspace |
| `smb_file_utils.py` | smbprotocol/smbclient adapter | N/A (workspace = kernel SMB) |
| `_extractors.py` | PyMuPDF/docx/pptx text extraction | Read tool + pdf/docx/pptx/xlsx skills |
| `check_prereqs.py` | Dependency check | Changed to workspace presence check in SKILL.md Phase 0 |

The only surviving script is `../_vocabulary.py`, which is a lightweight controlled-vocabulary lookup (reads a local markdown file, no network I/O).

These legacy scripts are kept here for reference but are **not invoked** by the current workflow.
