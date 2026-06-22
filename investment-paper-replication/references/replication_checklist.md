# Replication Checklist

Use this checklist before claiming a source document has been replicated, adapted, or systematized.

## Source Extraction

- Research question and economic mechanism identified.
- Target tables and figures listed.
- Sample period, market, and universe captured.
- Frequency and rebalance schedule captured.
- Model equations or portfolio rules captured.
- Transaction cost assumptions captured.
- Ambiguous or missing implementation details listed.

## Data

- Variables mapped to available fields.
- Data vintage and timestamp meaning understood.
- Delisting, survivorship, restatement, and index membership issues considered.
- Corporate actions and currency conversions considered where relevant.
- Missing values and outliers handled explicitly.

## Time Alignment

- Signal formation date separated from portfolio holding date.
- Publication/reporting lags applied where needed.
- Rebalance dates and holding periods match the source or stated approximation.
- No future data used in feature construction, ranking, normalization, or model fitting.

## Model and Portfolio Construction

- Formulas implemented from the source or documented approximation.
- Ranking, winsorization, standardization, neutralization, and weighting rules documented.
- Benchmarks and risk-free rates defined.
- Long-only, long-short, leverage, cash, and exposure constraints documented.

## Validation

- Summary statistics compared with the source where possible.
- Main table or figure directionally reproduced.
- Sensitivity to costs, universe, parameters, and subperiods checked.
- Recent-period performance checked when data allows.
- Turnover, drawdown, capacity, and implementation burden estimated when relevant.

## Reporting

- Exact replication, approximation, and conceptual adaptation clearly separated.
- Differences from the source explained.
- Investment use case and limitations stated plainly.
- Outputs are reproducible from scripts or documented manual steps.
