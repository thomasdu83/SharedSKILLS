# Existing Project Audit Checklist

Use this when the user has an existing project with source documents, papers, research reports, algorithm documents, code, reports, or frontend output. Audit before changing code unless asked to fix immediately.

## Audit Inputs

Look for:

- source PDFs, reports, memos, documents, or notes
- algorithm or methodology documents
- data dictionaries and configuration files
- notebooks and scripts
- report outputs
- frontend source and built artifacts
- tests and run instructions

## Consistency Matrix

Build a source-to-project matrix:

| Layer | Expected From Source | Project Implementation | Gap | Priority |
|---|---|---|---|---|
| Research question | | | | |
| Data universe | | | | |
| Variables | | | | |
| Timing and lags | | | | |
| Model logic | | | | |
| Portfolio rules | | | | |
| Costs and constraints | | | | |
| Report output | | | | |
| Frontend interaction | | | | |

## Review Areas

Check:

- algorithm document accurately reflects the source
- code accurately implements the algorithm document
- report accurately describes code output
- frontend accurately presents report conclusions
- data schema is documented and stable
- sample data and real data use the same structure
- frontend states and controls map to real calculations
- tests cover date alignment, lags, output schemas, and core interactions

## Priority Labels

Use:

- **P0**: wrong investment conclusion, future data leakage, broken core workflow, or unusable system
- **P1**: misleading output, major interaction flaw, untested core logic, or data contract mismatch
- **P2**: maintainability, reporting clarity, missing documentation, or incomplete edge-state handling
- **P3**: polish, layout improvement, minor copy, or non-critical refinement

## Output

Produce:

- project completeness score
- source-algorithm-code-display consistency findings
- prioritized remediation list
- quick wins
- larger refactor candidates
- missing tests and validation tasks
- recommendation: continue, revise, rebuild, or pause
