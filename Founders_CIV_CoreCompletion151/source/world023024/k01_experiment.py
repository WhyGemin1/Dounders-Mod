"""K-01: matched-world tests of information channels, trust and cognition.
Uses the v0.18 Agent through GD-01 initialize(); independent experimental decision layer.
"""
import argparse,copy,csv,json,random,statistics
from pathlib import Path
from founders_civ.core.engine import Simulation
from gd01_experiment import initialize
from knowledge_architecture import Claim,KnowledgeWorld,Cognition,encounter,practice

BRANCHES=('direct_observation','archive','spoken','cultural_imitation','independent_discovery')
CLAIM='K-RIVER-01'

def trial(seed,branch,ticks=80,trace=False):
    actors=initialize(seed)
    world=KnowledgeWorld();world.add(Claim(CLAIM,'river_energy','A layered conduit stabilizes energy'))
    # Same founder state across all five branches; each receives different evidence channels.
    cognition={a.id:Cognition(attention=0.5+0.4*a.traits['curiosity'],metacognition=0.4+0.5*a.traits['caution']) for a in actors}
    actors_by_id={a.id:a for a in actors}
    # Source with high skill; information is not automatically available to all actors.
    source=max(actors,key=lambda a:a.skills['build'])
    world.externalize(0,source.id,CLAIM)
    first_exposure={a.id:None for a in actors}
    successful={a.id:0 for a in actors}; attempts={a.id:0 for a in actors}
    messages=0; misinterpretations=0
    for t in range(ticks):
        for a in actors:
            rg=random.Random(Simulation.stable_seed(seed,branch,t,a.id,'k01'))
            c=cognition[a.id];k=c.claim(CLAIM)
            p=actors_by_id[a.route['partner']]
            trust=c.partner(p.id)
            # Initial relational evidence identical across branches, but branch experiences diverge.
            channel={'direct_observation':(.32,.94,.65,'observation'),
                     'archive':(.26,.89,.58,'archive'),
                     'spoken':(.34,.79,trust.expectation('integrity'),'speech'),
                     'cultural_imitation':(.27,.65,.55,'imitation'),
                     'independent_discovery':(.095,.91,.5,'experiment')}[branch]
            probability,fidelity,credibility,medium=channel
            if branch=='spoken':
                # Actual partner reliability differs by founder; trust estimates update on feedback.
                fidelity*=.55+.45*p.traits['empathy']
            if branch=='cultural_imitation':
                # Practice can propagate without verbalized understanding.
                fidelity*=.65+.35*p.skills['build']
            if rg.random()<probability:
                if branch=='independent_discovery' and rg.random()>.30+.45*a.traits['curiosity']:
                    world.record(t,a.id,'failed_search',CLAIM,medium=medium)
                else:
                    eid=encounter(world,c,t,a.id,CLAIM,p.id if branch in ('spoken','cultural_imitation') else 'environment',medium,fidelity,credibility)
                    if first_exposure[a.id] is None:first_exposure[a.id]=t
                    if branch=='spoken':
                        messages+=1
                        # Evidence of message fidelity is imperfect and distinct from actual truth.
                        verified=rg.random()<.55
                        if verified:
                            trust.update('integrity',rg.random()<fidelity)
                            world.record(t,a.id,'source_feedback',CLAIM,source=p.id,integrity=round(trust.expectation(),5),parent_event=eid)
                    if rg.random()>fidelity:misinterpretations+=1
            # Goal, skill, and cognition affect decision; no guaranteed application from exposure.
            seek=0.12+0.20*a.traits['ambition']+0.15*k.understanding
            if branch=='cultural_imitation':seek+=.09
            if rg.random()<seek:
                attempts[a.id]+=1
                ok=practice(world,c,t,a.id,CLAIM,a.skills['build'],environment_ok=rg.random()>.10)
                if ok:
                    successful[a.id]+=1
                    a.skills['build']=min(1.,a.skills['build']+.001*(1-a.skills['build']))
    records=[]
    for a in actors:
        k=cognition[a.id].claim(CLAIM)
        records.append({'seed':seed,'branch':branch,'founder':a.id,'exposures':k.exposures,'recall':k.recall,'understanding':k.understanding,'confidence':k.confidence,'applications':successful[a.id],'attempts':attempts[a.id], 'first_exposure':first_exposure[a.id] if first_exposure[a.id] is not None else -1,'integrity_trust':cognition[a.id].partner(a.route['partner']).expectation('integrity'),'final_build_skill':a.skills['build']})
    stats={'seed':seed,'branch':branch,'founders':len(records),'exposure_rate':sum(x['exposures']>0 for x in records)/len(records),'mean_recall':statistics.mean(x['recall'] for x in records),'mean_understanding':statistics.mean(x['understanding'] for x in records),'mean_confidence':statistics.mean(x['confidence'] for x in records),'successful_applications':sum(x['applications'] for x in records),'attempts':sum(x['attempts'] for x in records),'success_rate':sum(x['applications'] for x in records)/max(1,sum(x['attempts'] for x in records)),'messages':messages,'misinterpretations':misinterpretations,'mean_integrity_trust':statistics.mean(x['integrity_trust'] for x in records)}
    return stats,records,world.events if trace else []

def csvwrite(path,rows):
    if not rows:return
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=8);p.add_argument('--ticks',type=int,default=80);p.add_argument('--out',default='k01_results');p.add_argument('--trace-seeds',type=int,default=1);args=p.parse_args()
    out=Path(args.out);out.mkdir(exist_ok=True,parents=True)
    stats=[];founders=[];events=[]
    for seed in range(42,42+args.seeds):
        for branch in BRANCHES:
            s,r,e=trial(seed,branch,args.ticks,trace=seed<42+args.trace_seeds)
            stats.append(s);founders+=r
            for ev in e:events.append({'seed':seed,'branch':branch,**ev})
    csvwrite(out/'run_metrics.csv',stats);csvwrite(out/'founder_metrics.csv',founders)
    # union fields across event types for lossless tracing
    if events:
        keys=list(dict.fromkeys(k for e in events for k in e))
        with (out/'event_trace.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(events)
    summary=[]
    for b in BRANCHES:
        rr=[r for r in stats if r['branch']==b]
        summary.append({'branch':b,'seeds':len(rr),**{k:round(statistics.mean(x[k] for x in rr),5) for k in ('exposure_rate','mean_recall','mean_understanding','mean_confidence','successful_applications','success_rate','mean_integrity_trust')}})
    payload={'status':'executed synthetic pilot; NOT human validation','integration':'v0.18 Agent + GD-01 founder initializer; independent experimental cognitive layer; not v0.18 physical ledger','ticks':args.ticks,'seeds':args.seeds,'founders_per_world':100,'branches':list(BRANCHES),'parameters':'provisional; do not interpret channel ordering as empirical result','results':summary}
    (out/'summary.json').write_text(json.dumps(payload,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
