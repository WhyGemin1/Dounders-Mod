#!/usr/bin/env python3
"""Matched-seed synthetic M05 World Tree sensitivity runs.

No claims about actual WorldBox births, deaths or ecological stability.
The eight arms are NOT a validated reproduction of an earlier Core151 design.
"""
import argparse,csv,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from m05_core import Store

ARMS={
 'baseline':{},
 'dry':{'water_scale':.45},
 'river_scarcity':{'river_supply':20},
 'habitat_loss':{'support_scale':.55},
 'high_maintenance':{'maintenance':15},
 'reduced_capture':{'canopy_capture':28},
 'combined_stress':{'water_scale':.45,'support_scale':.65,'river_supply':25},
 'stewardship':{'support_bonus':.12,'water_scale':1.07}
}

def clamp(x):return min(1.,max(0.,x))

def run(output_dir,arms,seeds,horizons):
    work=Path(output_dir);work.mkdir(parents=True,exist_ok=True)
    template=json.loads((Path(__file__).resolve().parents[1]/'examples/world.json').read_text())
    maximum=max(horizons)
    records=[]
    for seed in range(seeds):
        # One common stream per seed is reused ACROSS arms: matched disturbances.
        rng=random.Random(seed+9711)
        shocks=[]
        for _ in range(maximum):
            shocks.append([(rng.uniform(-.08,.08),rng.uniform(-.1,.1),rng.uniform(-.06,.06)) for h in range(4)])
        for arm in arms:
            knobs=ARMS[arm]
            cfg=json.loads(json.dumps(template))
            cfg['world_key']='M05-synthetic-'+str(seed)+'-'+arm
            tree=cfg['trees'][0]['config']
            tree['maintenance']=knobs.get('maintenance',tree['maintenance'])
            tree['canopy_capture']=knobs.get('canopy_capture',tree['canopy_capture'])
            dbfile=work/(f'{arm}_seed{seed:02d}.sqlite')
            # Every explicit new run starts from an empty database.
            if dbfile.exists():raise RuntimeError('Refusing to overwrite prior experiment: '+str(dbfile))
            db=Store(str(dbfile))
            try:
                db.initialize(cfg['world_key'])
                for founder in cfg['founders']:db.add_founder(founder)
                for t in cfg['trees']:db.add_tree(t['id'],t['config'])
                for period in range(1,maximum+1):
                    conditions={}
                    habitat_overrides={}
                    for h,disturbance in zip(tree['habitats'],shocks[period-1]):
                        light,water,support=disturbance
                        habitat_overrides[h['id']]={
                            'light':clamp(h['light']+light),
                            'water':clamp(h['water']*knobs.get('water_scale',1)+water),
                            'support':clamp(h['support']*knobs.get('support_scale',1)+knobs.get('support_bonus',0)+support)}
                    conditions['WORLD-TREE-001']=habitat_overrides
                    db.cycle(period,knobs.get('river_supply',90),conditions)
                    if period in horizons:
                        state=db.status();tree_state=state['trees'][0]
                        records.append({'arm':arm,'seed':seed,'horizon':period,
                           'tree_alive':int(tree_state['alive']),'tree_health':tree_state['health'],
                           'fruit_created':tree_state['fruit_total'],
                           'fruit_current':tree_state['unharvested_fruit'],
                           'book_balanced':db.audit()['book_balanced'],
                           'measurement':'virtual_tree_only_not_native_ecology'})
            finally:db.close()
    csv_path=work/'matched_batch.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]) if records else [])
        writer.writeheader();writer.writerows(records)
    metadata={'status':'SYNTHETIC_HYPOTHESIS_TEST_ONLY','arms':arms,'seeds':seeds,
       'horizons':horizons,'rows':len(records),'csv':str(csv_path),
       'warning':'Results are not native WorldBox outcomes. Animal reproduction/mortality not evaluated.'}
    (work/'run_manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return metadata

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',required=True)
    p.add_argument('--seeds',type=int,default=30)
    p.add_argument('--horizons',default='30,180,360,720,1080')
    p.add_argument('--arms',default=','.join(ARMS))
    a=p.parse_args();arms=a.arms.split(',')
    if not all(x in ARMS for x in arms):p.error('Unknown arm')
    h=sorted(set(int(x) for x in a.horizons.split(',')))
    if a.seeds<1 or a.seeds>100 or len(arms)>8 or h[0]<1 or h[-1]>1080:p.error('Bounds exceeded')
    print(json.dumps(run(a.output_dir,arms,a.seeds,h),indent=2))
