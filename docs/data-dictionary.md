# Data dictionary

One record = one hour in an illustrative 24-hour day. No time zone or daylight-saving interpretation is implied.

| Field | Unit / meaning |
|---|---|
| hour | Integer 0–23; interval begins at this hour |
| price_eur_kwh | Synthetic unit energy price; taxes/demand charges excluded |
| baseline_kw | Original hourly electrical power |
| fixed_kw | Demand that cannot move |
| baseline_flexible_kw | Shiftable demand in the original schedule |
| max_flexible_kw | Allowed flexible power cap for that hour |
| optimized_flexible_kw | Flexible allocation returned by optimization |
| optimized_kw | fixed_kw + optimized_flexible_kw |
| baseline_cost_eur / optimized_cost_eur | Power × one hour × price |

`results/comparison.csv` records the solver and scenario totals. `sensitivity.csv` varies the eligible-hour flexible share. `sql_cost_summary.csv` reaggregates schedule records independently. All values originate in `synthetic_day()`; no confidential or public market dataset is used.
