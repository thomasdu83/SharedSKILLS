# Investment Validation

Use this frame to convert replication outputs into investment decisions.

## Classify the Use Case

Classify the source result as one or more of:

- alpha signal
- asset allocation input
- risk monitor
- portfolio construction constraint
- manager selection or due diligence lens
- macro regime indicator
- execution or trading cost improvement
- research-only conceptual framework

## Investability Questions

Answer these before recommending use:

- Does the effect survive transaction costs?
- Is turnover realistic?
- Is the data available at the decision time?
- Is the signal timely enough for the intended holding period?
- Is capacity plausible for the user's portfolio size?
- Is performance concentrated in one subperiod, region, asset, or regime?
- Does it duplicate an existing factor or exposure?
- Does it improve portfolio-level outcomes after costs and constraints?

## Failure and Monitoring

Define:

- expected decay channels
- market regimes where it may fail
- crowding indicators
- rolling information coefficient or hit-rate monitor
- turnover and cost monitor
- drawdown or underperformance trigger
- data quality checks
- review cadence

## Recommendation Language

Use conservative labels:

- **Production candidate**: replication is credible and implementation risks are manageable.
- **Research candidate**: logic is promising but needs more validation.
- **Monitoring lens**: useful as context, not as a direct trading rule.
- **Do not implement**: data, robustness, or economic logic is too weak.

Always separate practical recommendation from confidence level.
