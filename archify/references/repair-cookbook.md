# Repair cookbook

Use this quick reference after `validate` reports diagnostics. Keep fixes local, change one diagnosed geometry control at a time, and rerun `validate` after every edit.

## `clean-flow/edge-through-node`

Meaning:
- a relationship crosses an unrelated opaque component

First-choice fixes:
- move the blocking component into a clearer corridor
- let automatic routing retry by removing an unnecessary manual `via`
- add a truthful `fromSide` or `toSide`
- if needed, add a short explicit `via` that routes outside the obstacle

Avoid:
- forcing a long detour that creates new crossings
- keeping a route that visually runs through a boundary label or card area

## `clean-flow/endpoint-side-direction`

Meaning:
- the first or final route segment does not honor the authored side contract

First-choice fixes:
- remove the authored side and let automatic routing own both endpoints
- or keep the side and make the first or final segment perpendicular in the correct direction
- if using `via`, ensure the first point leaves the endpoint truthfully

Avoid:
- diagonal first or final segments when `fromSide` or `toSide` is authored
- stacking multiple side overrides on a relationship that does not need them

## `composition/proper-crossing`

Meaning:
- two unrelated relationships cross in a way that reduces readability

First-choice fixes:
- simplify the topology first: remove low-value edges or merge overly detailed nodes
- move one node to create a cleaner corridor
- route the secondary path around the main spine

Avoid:
- solving a crossing by adding several long `via` bends at once

## `composition/label-route-clearance`

Meaning:
- a relationship label is too close to another route

First-choice fixes:
- use the diagnosed `labelAt` when provided
- otherwise move only the label with `labelDx`, `labelDy`, or `labelSegment`
- if the label remains boxed in, widen spacing or adjust the competing route

Avoid:
- deleting meaningful labels as a spacing repair
- moving both the label and the route in the same attempt

## `layout/constraint`

Meaning:
- a label overlaps a component, boundary title, or another layout element

First-choice fixes:
- prefer the diagnostic's suggested `labelAt`
- if no exact point is suggested, move the label above or below the route before moving nodes
- shorten overly verbose label wording only after trying placement changes

Avoid:
- shrinking nodes or fonts to manufacture space

## `composition/micro-segment`

Meaning:
- a routed segment is too short to read cleanly

First-choice fixes:
- remove manual geometry and retry automatic routing
- move the nearest node to open a wider corridor
- if using `via`, spread the turn points farther apart

Avoid:
- adding more bend points into an already tight area

## `composition/desktop-readability`

Meaning:
- the delivered artifact projects node text below the desktop readability floor

Scope:
- the deterministic artifact gate checks a minimum 1440×900 desktop baseline
- `visual-check` then measures broader browser containment at 1440×900, 1600×1000, 1920×1080, and 2048×1320

First-choice fixes:
- shorten node sublabels and contextual copy
- reduce overall `viewBox` width if the topology allows it
- widen or simplify the affected node set
- split the diagram only when the topology is genuinely too dense for one artifact

Avoid:
- reducing typography to make the layout fit
- treating validation success as a substitute for browser readability evidence

## Escalation rule

If two consecutive focused repairs do not reduce the objective error count, stop changing geometry blindly. Re-check the topology:

- can two detail nodes be merged?
- is one edge semantically redundant?
- should the diagram be split into two views or two artifacts?
