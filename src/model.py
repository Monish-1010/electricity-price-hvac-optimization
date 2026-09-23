"""Transparent daily load-shifting model; no building controller or thermal model."""
import math

def synthetic_day(flexible_share=0.35):
    if not 0 <= flexible_share <= 0.6:
        raise ValueError('flexible_share must be between 0 and 0.6 for the fixed capacity')
    rows = []
    for hour in range(24):
        occupied = 7 <= hour <= 18
        baseline = 30.0 if occupied else 10.0
        price = round(0.10 + 0.11 * math.exp(-((hour-18)/3)**2)
                      + 0.065 * math.exp(-((hour-8)/2)**2), 4)
        flexible = baseline * flexible_share if occupied else 0.0
        rows.append(dict(hour=hour, price_eur_kwh=price,
                         baseline_kw=baseline, fixed_kw=baseline-flexible,
                         baseline_flexible_kw=flexible,
                         max_flexible_kw=18.0 if occupied else 0.0))
    return rows

def validate(rows):
    if not rows or len({r['hour'] for r in rows}) != len(rows):
        raise ValueError('nonempty rows with unique hours required')
    for r in rows:
        vals = [r[k] for k in ('price_eur_kwh','baseline_kw','fixed_kw',
                               'baseline_flexible_kw','max_flexible_kw')]
        if not all(math.isfinite(v) for v in vals):
            raise ValueError('all inputs must be finite')
        if min(vals[1:]) < 0 or r['baseline_flexible_kw'] > r['max_flexible_kw'] + 1e-9:
            raise ValueError('invalid power bounds or infeasible baseline')
        if abs(r['baseline_kw']-r['fixed_kw']-r['baseline_flexible_kw']) > 1e-8:
            raise ValueError('baseline must equal fixed plus flexible load')

def greedy_optimize(rows):
    """Exact continuous-knapsack solution for this model, with one-hour intervals."""
    validate(rows)
    remaining = sum(r['baseline_flexible_kw'] for r in rows)
    x = [0.0] * len(rows)
    for i in sorted(range(len(rows)), key=lambda i: (rows[i]['price_eur_kwh'], rows[i]['hour'])):
        x[i] = min(rows[i]['max_flexible_kw'], remaining)
        remaining -= x[i]
    if remaining > 1e-8:
        raise ValueError('flexible energy exceeds allowed capacity')
    return x

def pyomo_optimize(rows):
    validate(rows)
    import pyomo.environ as pyo
    m = pyo.ConcreteModel()
    m.hours = pyo.RangeSet(0, len(rows)-1)
    m.x = pyo.Var(m.hours, domain=pyo.NonNegativeReals,
                  bounds=lambda m,i: (0, rows[i]['max_flexible_kw']))
    m.energy = pyo.Constraint(expr=sum(m.x[i] for i in m.hours)
                             == sum(r['baseline_flexible_kw'] for r in rows))
    m.cost = pyo.Objective(expr=sum(rows[i]['price_eur_kwh'] *
                                   (rows[i]['fixed_kw'] + m.x[i]) for i in m.hours))
    solver = pyo.SolverFactory('appsi_highs')
    if not solver.available(exception_flag=False):
        raise RuntimeError('HiGHS is unavailable; use --solver greedy')
    result = solver.solve(m)
    if result.solver.termination_condition != pyo.TerminationCondition.optimal:
        raise RuntimeError('solver did not return optimal termination')
    return [pyo.value(m.x[i]) for i in m.hours]

def solve(rows, solver='auto'):
    if solver == 'greedy':
        return greedy_optimize(rows), 'greedy-exact'
    if solver == 'pyomo':
        return pyomo_optimize(rows), 'pyomo-highs'
    if solver != 'auto':
        raise ValueError('unknown solver')
    try:
        import pyomo.environ
        import highspy
    except ImportError:
        return greedy_optimize(rows), 'greedy-exact'
    return pyomo_optimize(rows), 'pyomo-highs'

def metrics(rows, x):
    base = sum(r['baseline_kw']*r['price_eur_kwh'] for r in rows)
    opt = sum((r['fixed_kw']+a)*r['price_eur_kwh'] for r,a in zip(rows,x))
    return dict(baseline_cost_eur=round(base,6), optimized_cost_eur=round(opt,6),
                saving_eur=round(base-opt,6), saving_pct=round(100*(base-opt)/base,4) if base > 0 else None,
                baseline_energy_kwh=sum(r['baseline_kw'] for r in rows),
                optimized_energy_kwh=round(sum(r['fixed_kw']+a for r,a in zip(rows,x)),6),
                baseline_peak_kw=max(r['baseline_kw'] for r in rows),
                optimized_peak_kw=round(max(r['fixed_kw']+a for r,a in zip(rows,x)),6))
