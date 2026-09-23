-- One row per hour, each interval exactly one hour. Energy (kWh) = power (kW) * 1h.
SELECT ROUND(SUM(baseline_cost_eur), 6) AS baseline_cost_eur,
       ROUND(SUM(optimized_cost_eur), 6) AS optimized_cost_eur,
       ROUND(SUM(baseline_kw), 6) AS baseline_kwh,
       ROUND(SUM(optimized_kw), 6) AS optimized_kwh,
       ROUND(MAX(optimized_kw), 6) AS optimized_peak_kw
FROM schedule;
