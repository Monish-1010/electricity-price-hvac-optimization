# Model and decision logic

For each one-hour interval t, p[t] is EUR/kWh, f[t] is fixed power and x[t] is flexible power in kW.

Minimize sum(p[t] * (f[t] + x[t]) * 1h), subject to:

- 0 <= x[t] <= maximum_flexible_power[t];
- sum(x[t] * 1h) = sum(baseline_flexible_power[t] * 1h).

The eligible window is 07:00–18:59; outside it, flexible capacity is zero. Each eligible hour permits up to 18 kW of flexible demand. The baseline is 30 kW during the window and 10 kW outside it. At 35% flexibility, the shiftable energy is 126 kWh and fixed demand is 354 kWh.

The fallback sorts eligible hours by increasing price and fills their capacity until the required energy is allocated. An exchange argument establishes optimality for this model: moving energy from a dearer hour to a cheaper hour with spare capacity cannot increase cost. Negative prices are supported; energy equality prevents unlimited additional consumption. Equal-price hours use chronological tie-breaking. The Pyomo model uses the same constraints and HiGHS, with an explicit optimal-termination check.

Sensitivity changes the flexible share while holding the hourly cap and prices fixed. It is a scenario analysis, not a forecast. Reducing time resolution or adding ramps, thermal storage, minimum run times or peak tariffs changes the model and invalidates this simple greedy proof.

Validation checks energy equality, feasible bounds, a hand-calculated small optimum including a negative price, no-flex behavior, invalid inputs and independent Pyomo/fallback objective agreement. SQL reaggregates the exported schedule. The synthetic price curve has morning/evening peaks by design and carries no date, market area or real tariff attribution.

The scenario generator accepts flexible shares from 0 to 0.6 because its fixed 18 kW hourly capacity cannot accommodate a larger baseline flexible allocation. Relative savings are undefined when baseline cost is zero or negative; the exported percentage is then blank and the absolute EUR difference remains available.
