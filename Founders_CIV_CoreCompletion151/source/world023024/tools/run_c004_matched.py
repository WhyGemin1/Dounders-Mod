"""C004 offline experimental arms on the SAME Core151 Book and WORLD024 Tree.

No WorldBox game side test. This uses control, C003 supplies-only, and C004
perception-gated autonomous Founder harvest. All ecological coefficients
remain synthetic. Test horizons are bounded by the supplied IntegratedWorld.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from run_world_tree_pilot import bootstrap

ARMS=('control','c003_supply','c004_harvest')


def run(seed,days,arm):
    if arm not in ARMS:raise ValueError('unknown arm')
    sim,realm,tid=bootstrap(seed=seed)
    tree=sim.world_trees.worlds[tid]
    if arm!='control':tree.enable_provisioning()
    if arm=='c004_harvest':sim.founder_harvest_enabled=True
    for _ in range(days):sim.step()
    audit=sim.book.audit()
    harvest=[e for e in sim.events if e['action']=='tree_founder_harvest']
    policy=tree.provisioning
    return {'seed':seed,'days':days,'arm':arm,'founders':len(sim.founders.people),
            'pop':tree.population,'births':tree.counters['tree_birth'],
            'deaths':tree.counters['tree_death'],
            'generations':sorted({r.generation for r in tree.residents.values()}),
            'tree_state':tree.state,'tree_age':tree.age,
            'lots':len(policy.lots) if policy else 0,
            'mature_lots':len(policy.mature_fruit()) if policy else 0,
            'harvest_events':len(harvest),
            'harvested_food':sum(e.get('resource_kind')=='food' for e in harvest),
            'harvested_fruit':sum(e.get('resource_kind')=='fruit' for e in harvest),
            'harvested_founders':len({e['actor'] for e in harvest}),
            'tree_observations':sum(e['action']=='tree_observed' for e in sim.events),
            'tree_action_rejections':sum(e['action']=='world_action_rejected' for e in sim.events),
            'founder_portable_mass':sum(v for k,v in sim.book.mass.items() if k.startswith(('fruit:lot:','portable_food:lot:')) and ':founder:' in k),
            'founder_creation_charge':sum(v for k,v in sim.book.energy.items() if k.startswith('ce:fruit:lot:') and ':founder:' in k),
            'river_charge':sim.book.energy['ce:river'],
            'book_seq':sim.book.seq,'book_rejections':audit['rejections'],
            'mass_error':audit['mass_error'],'energy_error':audit['energy_error']}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--long',action='store_true',help='additional 360-day paired seed if explicitly requested')
    a=p.parse_args()
    matrix=[(30,(820,821,822)),(180,(820,))]
    if a.long:matrix.append((360,(820,)))
    rows=[]
    for days,seeds in matrix:
        for seed in seeds:
            for arm in ARMS:
                print('RUN',seed,days,arm,flush=True)
                r=run(seed,days,arm)
                if r['founders']!=100 or abs(r['mass_error'])>1e-5 or abs(r['energy_error'])>1e-4:
                    raise AssertionError(r)
                if arm!='c004_harvest' and r['harvest_events']:
                    raise AssertionError('harvest leak into control '+str(r))
                rows.append(r)
    a1=run(820,30,'c004_harvest')
    assert a1==next(r for r in rows if r['seed']==820 and r['days']==30 and r['arm']=='c004_harvest')
    root=Path(__file__).resolve().parents[1]
    tracked=['founders_civ/core/founder_harvesting.py','founders_civ/core/autonomous_provisioning.py','founders_civ/core/living_assets.py','founders_civ/core/ledger.py','founders_civ/experimental/world_integration.py','founders_civ/experimental/world_trees.py']
    source={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in tracked}
    data={'schema':'U026-C004-offline-matched-v1','source_sha256':source,
          'matrix':matrix,'arms':list(ARMS),'rows':rows,'replay_verified':True,
          'limitations':'WorldBox not run; Founder ingestion/digestion and multigenerational calibration remain incomplete'}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,indent=2)+'\n')
    flat=[{**r,'generations':','.join(map(str,r['generations']))} for r in rows]
    with a.out.with_suffix('.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print('PASS',len(rows),'arms; replay verified',flush=True)

if __name__=='__main__':main()
