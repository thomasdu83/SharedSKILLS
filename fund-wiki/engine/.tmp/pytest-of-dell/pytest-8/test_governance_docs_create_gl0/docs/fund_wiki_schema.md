---
profile_type: FundWikiSchema
updated_at: "2026-06-05"
tags: [FundWiki/Governance]
---

# Fund Wiki Schema

## Core Folders

| Folder | Meaning |
|---|---|
| `source_notes/` | Parsed evidence notes from raw diligence materials. |
| `product_profiles/` | LLM-readable product-level profiles with structured frontmatter. |
| `manager_profiles/` | Manager-level strategy and product summaries. |
| `product_maps/` | Manager product maps for quick overview queries. |
| `risk_flags/` | Risk and constraint summaries by manager/product. |
| `timelines/` | Source-file timeline summaries. |
| `indexes/` | JSONL, SQLite, and relationship indexes for fast retrieval. |
| `reports/` | Build quality and health-check reports. |
| `run_logs/` | Run manifests, source catalogs, locks, and process logs. |

## ProductProfile Fields

| Field | Purpose |
|---|---|
| `manager` | Canonical manager name. |
| `product_name` | Canonical product/profile name. |
| `manager_aliases` | Names used for manager matching. |
| `product_aliases` | Names used for product matching. |
| `strategy_positioning` | One-sentence strategy positioning for LLM retrieval. |
| `product_line` | Normalized product-line labels such as 1000指增, CTA, market neutral. |
| `risk_points` | Risk constraints and concerns, including exposure controls. |
| `key_people_summary` | Personnel background clues such as WorldQuant or Millennium. |
| `evidence_summary` | Short evidence lines supporting the profile. |
| `source_files` / `source_notes` | Traceability back to evidence notes and raw-file names. |

## Relationship Index

`indexes/relations.jsonl` and `indexes/relations.sqlite` flatten important links into subject-predicate-object records, such as manager has product, product has strategy, product has risk point, and product has people background.

Current relation records: 11
