# Related Skills

Use this reference when multiple investment or quant skills could apply. The goal is clear sequencing, not duplication.

## Primary Role of This Skill

`investment-paper-replication` is the orchestrator for source-to-delivery work:

- understand the source
- define replication or adaptation scope
- create the Delivery Preview
- choose report, frontend, audit, or system delivery
- keep investment validation and acceptance testing visible

## Skill Boundaries

| Skill | Primary Role | Use When | Avoid Using It For |
|---|---|---|---|
| `investment-paper-replication` | Source-to-delivery orchestration | Paper/report/memo/idea to replication plan, audit, report, prototype, or system | Pure prose polishing without replication or delivery planning |
| `fund-wiki-research` | FOHF research synthesis | fund-wiki evidence, comparable pools, strategy taxonomy, manager/product research, fund facts plus research judgments | Raw material ingestion or direct business API lookup |
| `zmdata-data-api` | Documented ZM data API usage | Current data retrieval, interface parameters, ID mappings, code snippets, API-backed fact checks | Investment narrative or production system architecture |
| `quant-develop` | Quant system engineering | Production modules, data pipelines, backtests, portfolio construction, configs, tests | Deciding the investment narrative or delivery preview |
| `research-report-writer` | Research prose and structure | Drafting, rewriting, tightening thesis, improving narrative flow and professional tone | Verifying data, implementing algorithms, or accepting frontend interactions |

## Recommended Sequences

### Source to Report

1. `investment-paper-replication`: source intake, replication spec, Delivery Preview.
2. Analysis or minimal replication.
3. `research-report-writer`: refine thesis, structure, language, and analytical flow.
4. `investment-paper-replication`: final review against assumptions, evidence, and investment validation.

### Source to System

1. `investment-paper-replication`: source intake, replication spec, delivery preview, acceptance criteria.
2. `fund-wiki-research` if fund-wiki evidence, FOHF entities, comparable pools, or manager/product research judgments need verification.
3. `zmdata-data-api` if documented current data APIs or ID mappings are required.
4. `quant-develop`: implement production modules under engineering rules.
5. `investment-paper-replication`: verify final output against source, preview, and acceptance tests.

### Existing Project Audit

1. `investment-paper-replication`: source-algorithm-code-display consistency audit.
2. `quant-develop`: inspect and fix engineering defects after priorities are known.
3. `research-report-writer`: improve report prose after factual and analytical issues are resolved.

## Conflict Resolution

- If the task begins from a source document and asks what to build or deliver, this skill leads.
- If the task asks whether fund/strategy research evidence is factually grounded in fund-wiki, `fund-wiki-research` leads.
- If the task asks to implement or refactor confirmed quant code, `quant-develop` leads.
- If the task asks to rewrite or polish report prose, `research-report-writer` leads.

When in doubt, use this skill to define the delivery scope, then call the narrower specialist skill for its stage.
