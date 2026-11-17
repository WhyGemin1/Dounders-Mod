"""Small paired-seed compatibility matrix (not an ecological validation study)."""
import argparse,csv,json
from pathlib import Path
from founders_civ.integration import ScenarioSpec,IntegrationHost

PROFILES={
 'commons':('collective','careful','full',False),
 'owner':('owner','careful','full',False),
 'faction':('fragmented','careful','full',False),
 'high_harvest':('collective','intensive','full',False),
 'private':('collective','careful','full',True),
 'no_teaching':('collective','careful','no_teach',False),
 'neutral_trust':('collective','careful','neutral_trust',False),
 'isolated':('collective','careful','isolated',False),
}

def run_matrix(seeds=(820,821),cycles=6,profiles=None):
    rows=[]
    profiles=profiles or tuple(PROFILES)
    for seed in seeds:
        for name in profiles:
            gov,extract,mode,private=PROFILES[name]
            spec=ScenarioSpec(seed=int(seed),cycles=int(cycles),governance=gov,
                extraction=extract,social_mode=mode,allow_private=private,extensions=())
            host=IntegrationHost(spec)
            out=host.run()
            q=out['final_observation']
            rows.append({'seed':seed,'profile':name,'cycles':cycles,
                'tree_state':q['shared_tree_state'],'residents':q['shared_tree_population'],
                'stewards':q['stewards'],'private_active':q['active_private_trees'],
                'events':out['events_forwarded'],'mass_error':q['conserved_mass_error'],
                'energy_error':q['conserved_energy_error'],'founders':q['founders']})
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seeds',nargs='+',type=int,default=[820,821])
    p.add_argument('--cycles',type=int,default=6)
    p.add_argument('--profiles',nargs='+',choices=PROFILES,default=list(PROFILES))
    p.add_argument('--out',type=Path,default=Path('results/integration_025/matrix.csv'))
    a=p.parse_args()
    rows=run_matrix(a.seeds,a.cycles,a.profiles)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'scenarios':len(rows),'completed':len(rows),'collapsed':sum(x['tree_state']!='active' for x in rows),
       'max_mass_error':max(abs(x['mass_error']) for x in rows),
       'max_energy_error':max(abs(x['energy_error']) for x in rows),
       'csv':str(a.out)},indent=2))
