---
name: archify
description: Use when the user asks to create, convert, or polish a technical diagram such as architecture, workflow, sequence, data-flow, lifecycle/state, or Mermaid input into a validated standalone HTML artifact.
license: MIT
metadata:
  version: "2.17"
  author: tt-a1i
  based_on: Cocoon-AI/architecture-diagram-generator (MIT, v1.0)
---

# Archify

Create a self-contained, interactive HTML diagram from a small typed JSON specification. Static output is the default; enable motion only when the user asks for a demo or presentation.

## When To Use

Use `archify` for:

- system architecture, infrastructure, cloud, security, or service maps
- technical workflows, runbooks, approval flows, or tool-call chains
- API call sequences and request/response lifecycles
- data pipelines, ETL/ELT, and lineage views
- lifecycle or state-transition diagrams
- converting Mermaid into a cleaner validated artifact

Do not use it when the user only wants prose explanation, a checklist, or a page mockup without diagram semantics.

## Type Router

| Type | Use for |
|---|---|
| `architecture` | Components, services, storage, cloud/security boundaries |
| `workflow` | Processes, approvals, tool calls, runbooks |
| `sequence` | API call chains, request lifecycles, async traces |
| `dataflow` | Pipelines, ETL/ELT, lineage, consumers |
| `lifecycle` | State/status transitions, retries, terminals |

When the type is ambiguous, run:

```bash
node bin/archify.mjs guide "<scenario>" --json
```

## Fast Authoring Path

Use this bounded path for ordinary generation.

1. Choose `architecture`, `workflow`, `sequence`, `dataflow`, or `lifecycle` from the request.
2. Read one matching schema in `schemas/`, `schemas/common.schema.json`, and one matching JSON example in `examples/`. For new workflows use `schema_version: 2`; keep `schema_version: 1` only when preserving existing fixed geometry.
3. Write the candidate before inspecting renderer internals. Start with one clear main path, short side branches, sparse labels, and at most 12 primary nodes.
4. Set `meta.quality_profile` to `"showcase"` unless the user explicitly asks for a dense `standard` map.
5. Start with automatic routes and labels. Do not add `via`, `channelX`, `channelY`, or `labelAt` before a diagnostic calls for one.

## Default Authoring Rules

- Preserve semantic labels. Do not delete meaningful relationship wording just to make geometry pass.
- Omit `meta.visual_preset`, `meta.subtitle`, `meta.legend`, and `meta.engineering_profile` unless the user explicitly needs them.
- Use one primary authored language. Set `meta.locale` to `"en"` or `"zh-CN"` only when that matches the authored language.
- Keep exact product names, commands, protocols, API paths, and code identifiers intact.
- Use automatic routing first. Apply at most one diagnosed geometry control per repair.
- For architecture diagrams, prefer one left-to-right spine with short vertical branches.

Read [`references/authoring-contract.md`](references/authoring-contract.md) for geometry rules, spacing math, language handling, repository evidence, and mode-specific placement.

## Validation Loop

Validate after every candidate edit and immediately before handoff:

```bash
node bin/archify.mjs validate <type> <candidate.json> --quality showcase --json
```

A showcase pass must report all 9 artifact checks with 0 composition errors and 0 warnings. A passing final validation freezes the candidate: never edit it afterward.

If a workflow v2 needs geometry diagnosis, run:

```bash
node bin/archify.mjs validate workflow <candidate.json> --layout-json
```

## Delivery

For a delivered HTML, `deliver` is the final acceptance command:

```bash
node bin/archify.mjs deliver <type> <candidate.json> <output.html> --quality showcase --json
```

A non-zero exit can never be described as success. A failed delivery preserves any previous output, so do not run `visual-check` on that path.

After delivery, collect browser evidence from the exact trusted artifact:

```bash
node bin/archify.mjs visual-check <output.html> --json
```

Keep the three claims separate:

- `deliver` proves deterministic artifact checks
- `visual-check` proves automated browser evidence
- perceptual visual review requires a human or image-capable reviewer

Read [`references/delivery-contract.md`](references/delivery-contract.md) for the canonical receipt and review rules.

## Update Awareness

After the first candidate exists, run the packaged checker once:

```bash
node scripts/check-update.mjs --json
```

For acknowledgement:

```bash
node scripts/check-update.mjs --ack "<eventKey>" --json
```

For CLI usage help:

```bash
node scripts/check-update.mjs --help
```

If the command cannot run or returns `silent`, continue without mentioning the check. If it returns `update_available`, show one compact notice in the user's language, then acknowledge the returned `eventKey`.

Do not read renderer internals before the first candidate. Inspect implementation only for unsupported internal diagnostics or after two focused repairs fail.

## Mermaid Input

Read Mermaid for topology and meaning, then author fresh Archify JSON; do not mechanically render Mermaid styling.

- `flowchart` / `graph` -> `workflow`, or `architecture` for a component map
- `sequenceDiagram` -> `sequence`
- `stateDiagram` -> `lifecycle`

## References

Read only the reference you need:

- [`references/authoring-contract.md`](references/authoring-contract.md): geometry, language, layout, repository evidence
- [`references/delivery-contract.md`](references/delivery-contract.md): delivery receipts, browser evidence, visual review
- [`references/repair-cookbook.md`](references/repair-cookbook.md): common diagnostics and first-choice fixes
- [`references/brand-marks.md`](references/brand-marks.md): only when the user supplies an unknown official product URL
- [`references/viewer-runtime.md`](references/viewer-runtime.md): only when the user explicitly asks about viewer features

For an active desktop authoring loop only:

```bash
node bin/archify.mjs preview <type> <input>.json <output>.html --quality showcase
```

Never start preview by default.

## Output

Return the checked HTML path, diagram type, validation summary, specification/artifact receipt, browser-evidence status, and truthful visual-review status. Do not claim success for a non-zero command or claim visual inspection you did not perform.
