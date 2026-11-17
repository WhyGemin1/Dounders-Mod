"""Paired uncertainty summary for the preregistered-style diagnostic suite."""
from pathlib import Path
from statistics import mean
from random import Random
import csv,json
from soul_ecology_v021 import EcologyTrial
ROOT=Path(__file__).resolve().parent
RESULT=ROOT/'results'/'soul_ecology'
RESULT.mkdir(parents=True,exist_ok=True)
source=ROOT/'results'/'40_hazard'/'results.csv'
rows=list(csv.DictReader(source.open()))
by={(int(r['seed']),r['arm']):r for r in rows}
seeds=sorted(set(int(r['seed']) for r in rows))

def percentile(a,q):
    s=sorted(a);i=(len(s)-1)*q;lo=int(i);hi=min(lo+1,len(s)-1)
    return s[lo]+(i-lo)*(s[hi]-s[lo])

summary={}
for arm in ('episodic','social','full'):
    summary[arm]={}
    for key in ('alive','unsafe_exposures','hazard_deaths','births'):
        diffs=[float(by[(seed,arm)][key])-float(by[(seed,'baseline')][key]) for seed in seeds]
        rng=Random(20261106)
        draws=[mean([diffs[rng.randrange(len(diffs))] for _ in diffs]) for _ in range(5000)]
        summary[arm][key]={
          'mean_paired_difference':mean(diffs),
          'bootstrap_95_CI':[percentile(draws,.025),percentile(draws,.975)],
          'seeds_higher':sum(v>0 for v in diffs),
          'seeds_lower':sum(v<0 for v in diffs),
          'seeds_equal':sum(v==0 for v in diffs),
        }

sensitivity=[]
for decay in (0.02,0.13,0.40):
    runs=[EcologyTrial(s,mode='full',memory_decay=decay).run(12) for s in seeds]
    sensitivity.append({'memory_decay':decay,
      'mean_alive':mean(r['alive'] for r in runs),
      'mean_migrations':mean(r['migrations'] for r in runs),
      'mean_unsafe_exposures':mean(r['unsafe_exposures'] for r in runs),
      'max_mass_discrepancy':max(abs(r['audit']['mass_error']) for r in runs),
      'max_energy_discrepancy':max(abs(r['audit']['energy_error']) for r in runs)})

analysis={'design':{'n_seeds':len(seeds),'seed_first':min(seeds),'seed_last':max(seeds),
 'habitat_hazard_high':.17,'habitat_hazard_low':.018,'steps':12,
 'n_initial_animals':30,'patches':['north','south'],
 'original_v020_demography':'UNCHANGED',
 'decision_information':'local danger perception plus prior episodic/social route evidence'},
 'paired_bootstrap':summary,'memory_decay_sensitivity':sensitivity}
(RESULT/'paired_analysis.json').write_text(json.dumps(analysis,indent=2))
with (RESULT/'memory_sensitivity.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=sensitivity[0].keys());w.writeheader();w.writerows(sensitivity)
print(json.dumps(analysis,indent=2))
