"""TR-01 controlled source-evidence / metacognition tests on v0.19 module."""
import argparse,json,csv,random,statistics
from pathlib import Path
from founders_civ.core.engine import Simulation
from knowledge_architecture import Cognition,KnowledgeWorld,Claim,encounter
CONDITIONS=('reliable_verified','unreliable_verified','unreliable_unverified','unreliable_low_metacognition')

def run(seed,condition,actors=100,rounds=20):
    w=KnowledgeWorld();w.add(Claim('C1','river','Claim from source'))
    data=[]
    for i in range(actors):
        id=f'F{i:03}';rg=random.Random(Simulation.stable_seed(seed,condition,i))
        c=Cognition(metacognition=.1 if condition=='unreliable_low_metacognition' else .8)
        relation=c.partner('S1');truthful=condition=='reliable_verified';verified=condition in ('reliable_verified','unreliable_verified')
        for t in range(rounds):
            # External ground truth is separate from actor's evidence and judgment.
            actual_accuracy=rg.random() < (.85 if truthful else .2)
            prior=relation.expectation('integrity')
            eid=encounter(w,c,t,id,'C1','S1','speech',fidelity=1.,trust=prior)
            if verified:
                # Realistic observation noise: checks can misclassify source quality.
                observed=actual_accuracy if rg.random()<.9 else not actual_accuracy
                relation.update('integrity',observed)
                w.record(t,id,'verification','C1',observed=int(observed),actual=int(actual_accuracy),parent_event=eid)
            elif rg.random()<.15*c.metacognition:
                relation.update('integrity',actual_accuracy,strength=.5)
                w.record(t,id,'limited_feedback','C1',actual=int(actual_accuracy),parent_event=eid)
        trust=relation.expectation('integrity');target=.85 if truthful else .2
        data.append({'seed':seed,'condition':condition,'founder':id,'trust':trust,'target_accuracy':target,'absolute_calibration_error':abs(trust-target),'confidence':c.claim('C1').confidence,'understanding':c.claim('C1').understanding})
    return data,w.events

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=12);ap.add_argument('--out',default='tr01_results');args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);allrows=[];trace=[]
    for seed in range(42,42+args.seeds):
        for cond in CONDITIONS:
            rows,events=run(seed,cond);allrows+=rows
            if seed==42:trace += [{'seed':seed,'condition':cond,**e} for e in events]
    with (out/'founder_metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=allrows[0].keys());w.writeheader();w.writerows(allrows)
    with (out/'event_trace.csv').open('w',newline='') as f:
        keys=list(dict.fromkeys(k for e in trace for k in e));w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(trace)
    summary=[]
    for cond in CONDITIONS:
        r=[x for x in allrows if x['condition']==cond]
        summary.append({'condition':cond,'founder_runs':len(r),'mean_trust':round(statistics.mean(x['trust'] for x in r),5),'mean_calibration_error':round(statistics.mean(x['absolute_calibration_error'] for x in r),5),'mean_confidence':round(statistics.mean(x['confidence'] for x in r),5)})
    (out/'summary.json').write_text(json.dumps({'status':'synthetic controlled test; source truth is programmed','seeds':args.seeds,'founders_per_condition':100,'rounds':20,'results':summary},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
