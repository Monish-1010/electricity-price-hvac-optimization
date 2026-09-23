# Power BI reconstruction guide

Import `results/schedule.csv` as HourlySchedule, `results/comparison.csv` as Scenario and `results/sensitivity.csv` as Sensitivity. Schedule has a unique integer hour key; the other tables are separate scenario summaries. Do not join sensitivity rows directly to hourly facts.

- KPI cards: baseline cost, optimized cost, saving %, baseline/optimized energy, peak increase.
- Clustered column chart: hour × baseline_kw / optimized_kw.
- Separate line chart: hour × price_eur_kwh; keep its unit explicit.
- Sensitivity chart: flexible_share × saving_pct.
- Callout: “Synthetic prices; constant daily energy; thermal comfort not modeled.”

```dax
Baseline Cost = SUM(HourlySchedule[baseline_cost_eur])
Optimized Cost = SUM(HourlySchedule[optimized_cost_eur])
Savings % = DIVIDE([Baseline Cost] - [Optimized Cost], [Baseline Cost])
Optimized Energy kWh = SUM(HourlySchedule[optimized_kw])
```

The energy expression is valid only because each record represents exactly one hour. Format currency in EUR and percent using decimal measures. Reconcile totals with `sql_cost_summary.csv` before sharing. The SVG in images is an exported analytical chart, not a Power BI screenshot.
