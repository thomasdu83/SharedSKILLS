# Quality Rubric

## Process quality

Check whether the note has:

- fixed information cutoff and horizons;
- fact/inference/scenario/action separation;
- a dominant mechanism with an alternative explanation;
- three observable scenarios totaling 100%;
- explicit pricing and trend checks;
- conditional asset mapping;
- falsifiers and timing;
- a frozen version and a linked review plan.

## Forecast quality

Use the stated horizon and compare with simple baselines:

- persistence: keep the previous view;
- trend: a transparent price-momentum rule;
- consensus: available market or analyst expectation.

For event probabilities, record Brier components `(p - outcome)^2` and review calibration across many forecasts. For cross-asset relative strength, use a rank or hit-rate measure appropriate to the stated universe. Do not treat overlapping weekly windows as independent observations.

## Decision quality

Ask whether the stance matched the stated probability, asymmetry, liquidity, and risk. A correct macro call with an impossible-to-express asset is not a complete success; a wrong call avoided by a disciplined no-trade can be a good decision.

## Error taxonomy

1. Macro state error.
2. Policy reaction/transmission error.
3. Market pricing/positioning error.
4. Macro-to-asset mapping error.
5. Horizon/timing error.
6. Decision sizing or expression error.
7. Good process/bad outcome.
8. Bad process/good outcome.

## Framework-change gate

Do not change a formal framework because one outcome was wrong. Create a change candidate and wait for repeated evidence, a clear counterexample, or a strong mechanism-level reason. When changing it, record what old forecasts are affected and what remains valid.

