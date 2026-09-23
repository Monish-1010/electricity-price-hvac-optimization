import unittest
from src.model import synthetic_day, greedy_optimize, pyomo_optimize, metrics

class DispatchTests(unittest.TestCase):
    def test_conservation_and_bounds(self):
        rows=synthetic_day();x=greedy_optimize(rows)
        self.assertAlmostEqual(sum(x),sum(r['baseline_flexible_kw'] for r in rows))
        for r,a in zip(rows,x): self.assertTrue(-1e-8 <= a <= r['max_flexible_kw']+1e-8)
        self.assertLess(metrics(rows,x)['optimized_cost_eur'],metrics(rows,x)['baseline_cost_eur'])

    def test_known_small_optimum_and_negative_price(self):
        rows=[dict(hour=i,price_eur_kwh=p,baseline_kw=1,fixed_kw=0,
                   baseline_flexible_kw=1,max_flexible_kw=2) for i,p in enumerate([1,-1,2])]
        self.assertEqual(greedy_optimize(rows),[1,2,0])

    def test_zero_cost_and_infeasible_share(self):
        rows=synthetic_day()
        for r in rows: r['price_eur_kwh']=0
        self.assertIsNone(metrics(rows,greedy_optimize(rows))['saving_pct'])
        with self.assertRaises(ValueError): synthetic_day(0.7)

    def test_no_flex_no_saving(self):
        r=synthetic_day(0);self.assertEqual(metrics(r,greedy_optimize(r))['saving_eur'],0)

    def test_invalid_baseline_rejected(self):
        r=synthetic_day();r[0]['baseline_flexible_kw']=100
        with self.assertRaises(ValueError):greedy_optimize(r)

    def test_pyomo_matches_independent_exact_solution(self):
        try:
            import pyomo.environ
            import highspy
        except ImportError: self.skipTest('optional Pyomo/HiGHS not installed')
        for share in (0,0.15,0.35,0.5):
            rows=synthetic_day(share)
            self.assertAlmostEqual(metrics(rows,pyomo_optimize(rows))['optimized_cost_eur'],
                                   metrics(rows,greedy_optimize(rows))['optimized_cost_eur'],places=5)

if __name__=='__main__': unittest.main()
