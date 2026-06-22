# Acceptance Testing

Use this to reduce late manual rework. The goal is not exhaustive QA; it is early detection of the failures that make source-based quant and investment research systems unreliable.

## Research Acceptance

Verify:

- core formulas match the source or documented approximation
- date alignment and reporting lags are tested
- output metrics can be reproduced from source scripts
- source-versus-replication/adaptation differences are explained
- recent-period and cost sensitivity are checked when data allows

## Report Acceptance

Verify:

- report follows the confirmed outline
- every chart/table has a conclusion-led title
- source claim, replication/adaptation evidence, and investment interpretation are separated
- assumptions and data substitutions are visible
- no unsupported investment recommendation is made

## Frontend Acceptance

Use browser automation or manual browser checks:

- open the page without console errors
- test every primary tab/filter/toggle
- confirm charts and tables update after interactions
- test desktop and mobile widths
- verify text does not overlap or overflow
- verify loading, empty, and error states where implemented
- confirm sample period, benchmark, cost basis, and data source are visible

## System Acceptance

Verify:

- documented run command works
- outputs are deterministic or variability is explained
- config changes affect expected modules only
- tests cover data alignment, schema generation, and core model logic
- generated report or frontend consumes current outputs, not stale files

## Final Delivery Note

State:

- tests run
- tests not run and why
- manual checks completed
- known unresolved issues
- next recommended validation step
