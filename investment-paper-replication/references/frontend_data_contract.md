# Frontend Data Contract

Use this before connecting frontend components to real data. Many frontend defects come from unstable schemas, ambiguous units, or sample data that differs from production output.

## Required Contract

Define:

- dataset name
- producer module or file
- consumer component
- refresh cadence
- date/time conventions
- units and precision
- null and missing value behavior
- sorting and ranking rules
- benchmark and currency conventions

## Schema Template

```json
{
  "metadata": {
    "source_id": "string",
    "run_id": "string",
    "as_of_date": "YYYY-MM-DD",
    "frequency": "monthly",
    "currency": "USD",
    "benchmark": "string"
  },
  "summary": {
    "annualized_return": 0.0,
    "volatility": 0.0,
    "information_ratio": 0.0,
    "max_drawdown": 0.0,
    "turnover": 0.0
  },
  "series": [
    {
      "date": "YYYY-MM-DD",
      "strategy": 100.0,
      "benchmark": 100.0,
      "drawdown": -0.05
    }
  ],
  "tables": {
    "robustness": []
  }
}
```

Adapt the schema to the project, but keep the metadata block explicit.

## Contract Checks

Before frontend implementation:

- sample data uses the same schema as expected production data
- all chart fields are present and typed
- units are explicit in metadata or labels
- missing values have display rules
- dates are consistently formatted
- tables have stable column ids
- frontend handles empty arrays and partial results
