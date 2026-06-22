# Frontend Interaction Checklist

Use this before implementing or accepting a frontend prototype or app.

## User Paths

Define core paths:

- open dashboard/report
- inspect executive summary
- change date range or sample period
- switch scenario, tab, or model version
- filter universe, asset class, region, factor, or benchmark
- inspect chart tooltip or data table
- export or copy outputs if supported
- recover from empty, loading, and error states

## Interaction Specification

For each control, document:

| Control | Input | Expected State Change | Expected Output Change | Empty/Error State |
|---|---|---|---|---|
| Date range | | | | |
| Scenario tab | | | | |
| Metric toggle | | | | |
| Universe filter | | | | |

## Common Failure Points

Check:

- filters update every dependent chart and table
- chart titles and numbers update with selected state
- units and date ranges remain visible
- selected tabs and controls have clear active states
- loading states are not confused with empty results
- empty states explain why data is missing
- error states are visible and actionable
- reset/default state is obvious
- mobile or narrow widths do not hide critical controls
- keyboard focus and clickable targets are usable

## Investment-Specific Requirements

Verify:

- charts do not imply unsupported conclusions
- benchmark and sample period are always visible
- gross and net results are clearly labeled
- methodology caveats are close to the relevant output
- risk, turnover, cost, and drawdown views are available when relevant
- reported metrics match data source precision and units

## Acceptance

A frontend is not done until the core user paths are exercised manually or with browser automation, and unresolved interaction gaps are listed.

