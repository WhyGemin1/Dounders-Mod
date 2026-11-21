"""U026-C003 offline matched-seed comparison of opt-in WORLD024 provisioning.

Not a native WorldBox test, not a claim of ecological stability.
"""
from __future__ import annotations
import argparse,csv,json,hashlib
from pathlib import Path
from run_world_tree_pilot import bootstrap


def run(seed,days,arm):
    sim,realm,tid=bootstrap(seed=seed)
    tree=sim.world_trees.worlds[tid]
    if arm=='c003_provisioning':policy=tree.enable_provisioning()
    for _ in range(days):sim.step()
    audit=sim.book.audit()
    lots=tree.provisioning.lots if tree.provisioning else {}
    return {
        'seed':seed,'days':days,'arm':arm,'tree_id':tid,
        'tree_age':tree.age,'tree_state':tree.state,
        'tree_status':sim.seeds.plants[tid]['status'],
        'population':tree.population,'births':tree.counters['tree_birth'],
        'deaths':tree.counters['tree_death'],
        'generations':sorted(set(r.generation for r in tree.residents.values())),
        'founders':len(sim.founders.people),
        'food_lots':sum(v.kind=='food' for v in lots.values()),
        'fruit_lots':sum(v.kind=='fruit' for v in lots.values()),
        'mature_fruits':len(tree.provisioning.mature_fruit()) if tree.provisioning else 0,
        'decayed_lots':sum(v.state=='decayed' for v in lots.values()),
        'river_pool':sim.book.energy['river_pool'],
        'ce_river':sim.book.energy['ce:river'],
        'asset_ids':len(sim.book.asset_ids),
        'book_seq':sim.book.seq,
        'rejections':audit['rejections'],
        'mass_error':audit['mass_error'],'energy_error':audit['energy_error'],
    }


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[]
    for days,seeds in ((30,(820,821,822)),(180,(820,))):
        for seed in seeds:
            for arm in ('control','c003_provisioning'):
                print(f'run {seed} {days} {arm}',flush=True)
                row=run(seed,days,arm)
                if row['founders']!=100 or abs(row['mass_error'])>1e-5 or abs(row['energy_error'])>1e-4:
                    raise AssertionError(row)
                rows.append(row)
    replay=run(820,30,'c003_provisioning')
    assert replay == next(r for r in rows if r['seed']==820 and r['days']==30 and r['arm']=='c003_provisioning')
    root=Path(__file__).resolve().parents[1]
    tracked=['founders_civ/core/autonomous_provisioning.py','founders_civ/core/living_assets.py',
             'founders_civ/experimental/world_trees.py','founders_civ/core/ledger.py']
    manifest={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in tracked}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps({'schema':'U026-C003-matched-v1','simulator':'actual Core151 Book / WORLD024 Tree, offline',
                                'configuration':{'seeds':[820,821,822],'horizons':[30,180],'arms':['control','c003_provisioning']},
                                'source_sha256':manifest,'rows':rows,'deterministic_replay':True},indent=2)+'\n')
    flat=[{**r,'generations':','.join(map(str,r['generations']))} for r in rows]
    with a.out.with_suffix('.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print('PASS',len(rows),'matched arms and deterministic replay')

if __name__=='__main__':main()
