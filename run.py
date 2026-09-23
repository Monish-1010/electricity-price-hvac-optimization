# Regenerate all synthetic inputs, SQL outputs and figures from the repository root.
import argparse
import csv
import json
from pathlib import Path
import sqlite3
from src.model import synthetic_day, solve, metrics

ROOT = Path(__file__).resolve().parent
def csv_write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def figure(rows):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="520" viewBox="0 0 1100 520" role="img" aria-label="Synthetic baseline and optimized hourly HVAC load">',
           '<rect width="1100" height="520" fill="#F5F7FA"/>',
           '<g font-family="Arial,sans-serif" fill="#10243A">',
           '<text x="48" y="45" font-size="25" font-weight="bold">HVAC flexibility | a transparent daily dispatch</text>',
           '<text x="48" y="74" font-size="15">Synthetic scenario · 480 kWh held constant · electricity-only objective</text>',
           '<text x="65" y="111" font-size="14">Electric power (kW)</text>']
    for kw in range(0,41,10):
        y=410-kw*6.5
        parts += [f'<line x1="80" y1="{y}" x2="1040" y2="{y}" stroke="#D7DFE7"/>',f'<text x="48" y="{y+5}">{kw}</text>']
    for i,r in enumerate(rows):
        x=85+i*39.5
        for shift,key,color in [(0,'baseline_kw','#10243A'),(16,'optimized_kw','#087F8C')]:
            h=r[key]*6.5
            parts.append(f'<rect x="{x+shift}" y="{410-h}" width="14" height="{h}" fill="{color}" rx="2"/>')
        if i%2==0: parts.append(f'<text x="{x+4}" y="432" font-size="12">{i:02d}</text>')
    parts += ['<text x="495" y="454" font-size="14">Hour of synthetic day</text>',
              '<rect x="70" y="480" width="14" height="14" fill="#10243A"/><text x="92" y="492">Baseline</text>',
              '<rect x="220" y="480" width="14" height="14" fill="#087F8C"/><text x="242" y="492">Optimized</text>',
              '<text x="470" y="492" font-size="13">Higher peak demand is a trade-off; demand charges are excluded.</text></g></svg>']
    (ROOT/'images').mkdir(exist_ok=True)
    (ROOT/'images/schedule.svg').write_text('\n'.join(parts),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--solver',choices=['auto','pyomo','greedy'],default='auto');args=ap.parse_args()
    rows=synthetic_day();x,backend=solve(rows,args.solver)
    csv_write(ROOT/'data/raw/hourly_scenario.csv',rows)
    schedule=[dict(r,optimized_flexible_kw=round(a,8),optimized_kw=round(r['fixed_kw']+a,8),
                   baseline_cost_eur=round(r['baseline_kw']*r['price_eur_kwh'],6),
                   optimized_cost_eur=round((r['fixed_kw']+a)*r['price_eur_kwh'],6)) for r,a in zip(rows,x)]
    csv_write(ROOT/'results/schedule.csv',schedule)
    result=dict(scenario='synthetic_24h',solver=backend,**metrics(rows,x))
    csv_write(ROOT/'results/comparison.csv',[result])
    sensitivity=[]
    for share in (0,0.15,0.25,0.35,0.5):
        s=synthetic_day(share);a,_=solve(s,'greedy');sensitivity.append(dict(flexible_share=share,**metrics(s,a)))
    csv_write(ROOT/'results/sensitivity.csv',sensitivity)
    con=sqlite3.connect(':memory:')
    columns=list(schedule[0]);con.execute('CREATE TABLE schedule ('+', '.join(c+' REAL' for c in columns)+')')
    con.executemany('INSERT INTO schedule VALUES ('+','.join('?' for c in columns)+')',[list(r.values()) for r in schedule])
    cursor=con.execute((ROOT/'sql/cost_summary.sql').read_text())
    csv_write(ROOT/'results/sql_cost_summary.csv',[dict(zip([c[0] for c in cursor.description],r)) for r in cursor.fetchall()]);con.close()
    figure(schedule)
    (ROOT/'results/insights.md').write_text(f'''# Synthetic scenario findings

Baseline cost: EUR {result['baseline_cost_eur']:.2f}; optimized cost: EUR {result['optimized_cost_eur']:.2f}.
The model keeps total energy at {result['baseline_energy_kwh']:.0f} kWh while rescheduling part of the 126 kWh flexible allocation; the modeled energy bill falls by {result['saving_pct']:.2f}%.
Peak load rises from {result['baseline_peak_kw']:.1f} to {result['optimized_peak_kw']:.1f} kW.

This is a generated demonstration, not a measured saving. Before piloting, add tariffs,
thermal/comfort constraints, ramp limits, equipment cycling, forecast uncertainty and a
validated baseline. Compare sensitivity.csv to see the effect of assumed flexibility.
''',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
