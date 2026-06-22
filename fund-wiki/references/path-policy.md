# Fund Wiki Path Policy

## Project Root

Default bundled engine:

```text
F:\Thomas\QuantSystem\.trae\skills\fund-wiki\engine
```

Override with:

```text
FPW_PROJECT_ROOT
FUND_PROFILE_WIKI_PROJECT_ROOT
```

Development source project can remain at:

```text
F:\Thomas\Labs\fund_profile_wiki
```

The skill will use it only when explicitly requested through `--project-root`, `FPW_PROJECT_ROOT`, or `FPW_ALLOW_DEV_PROJECT_FALLBACK=1`.

## Raw Material Roots

Candidates are checked in this order:

1. Explicit `--raw-root`
2. `FPW_RAW_ROOT`
3. `FPW_DD_ROOT`
4. `W:\投顾信息（PPT、尽调反馈表等）`
5. `Z:\投顾信息（PPT、尽调反馈表等）`
6. `\\10.168.20.10\投顾信息（PPT、尽调反馈表等）`

These roots are read-only. Never write generated output into them.

## Docs Root

Candidates are checked in this order:

1. Explicit `--docs-root`
2. `FPW_DOCS_ROOT`
3. `FUND_PROFILE_WIKI_DOCS_ROOT`
4. `Y:\投顾管理人研究\fund_profile_wiki_docs`
5. `\\10.168.20.10\资产-投资研究\投顾管理人研究\fund_profile_wiki_docs`

Local development fallback is available only when explicitly enabled:

```text
F:\Thomas\Labs\fund_profile_wiki_docs
```

Use `--allow-local-docs-fallback` or `FPW_ALLOW_LOCAL_DOCS_FALLBACK=1`.

## Network Drive Rules

- Use `Test-Path` or the bundled scripts to verify reachability before doing expensive work.
- Avoid deep wildcard scanning on SMB roots from Trae workspace tools.
- Manager discovery scans only first-level folders under the raw root.
- `fund_profile_wiki_docs\source_snapshots` is reserved and should remain unused in normal deposit runs; originals remain unchanged at the raw-material root.

Default deposit runs do not create source snapshots. They write source traceability records to:

```text
Y:\投顾管理人研究\fund_profile_wiki_docs\run_logs\source_manifest.jsonl
```

Use `--snapshot none` when even manifest records should not be written.

## Environment Files

Scripts load `.env` files without overriding already-set environment variables. Candidate order:

1. Explicit `--env-file`
2. `FPW_ENV_FILE` / `FUND_WIKI_ENV_FILE`
3. `fund-wiki\.env`
4. `F:\Thomas\QuantSystem\.env`
5. `F:\Thomas\QuantSystem\domains\macro\external-report-macro-score\src\.env`
6. current working directory `.env`

For team sharing, prefer `fund-wiki\.env` or `FUND_WIKI_ENV_FILE` over relying on a domain-specific project `.env`.
