"""GD-01 experimental Founder cognition layer; imports v0.18 Agent and stable_seed.
Not a replacement for the v0.18 conservation/ecology engine.
"""
import random, copy, csv, json, math, argparse
from collections import Counter
from pathlib import Path
from founders_civ.core.engine import Agent, Simulation
ACTIONS=('research','craft','explore','teach','assist','rest')
GOALS=('research','craft','explore','teach','assist')
SKILLS={'research':'coordinate','craft':'build','explore':'navigate','teach':'teach','assist':'forage','rest':None}
GROUPS=('control','removal','instability','disconnect','recovery')

def initialize(seed):
    actors=[]
    for i in range(100):
        rng=random.Random(Simulation.stable_seed(seed,'founder',i))
        a=Agent(id=f'F{i:03}',species='founder',world='House',patch='river',group='House',age=100000,
                traits={'ambition':rng.uniform(.2,.95),'curiosity':rng.uniform(.2,.95),'empathy':rng.uniform(.2,.95),'caution':rng.uniform(.2,.95)},
                skills={s:rng.uniform(.12,.65) for s in SKILLS.values() if s},goal=rng.choice(GOALS),
                willing=rng.uniform(.35,.95),fear=rng.uniform(.1,.4))
        a.beliefs={'preference_'+k:rng.uniform(.1,.8) for k in ACTIONS}
        a.expectations={'energy':rng.uniform(.5,1.0),'attitude':rng.uniform(.3,.9)}
        actors.append(a)
    ids=list(range(100));rng=random.Random(seed+991);rng.shuffle(ids)
    for x,y in zip(ids[::2],ids[1::2]):
        actors[x].route['partner']=actors[y].id;actors[y].route['partner']=actors[x].id
    return actors

def tick(actors,seed,t,group,intervention_start=200,intervention_end=600):
    active=intervention_start<=t<intervention_end
    counts=Counter()
    for a in actors:
        rg=random.Random(Simulation.stable_seed(seed,t,a.id,'gd01'))
        goal=a.goal
        if active and (group=='removal' or (group=='recovery' and t<intervention_start+200)):goal=None
        if active and group=='instability' and (t-intervention_start)%10==0:
            a.route['temporary_goal']=rg.choice(GOALS)
        if active and group=='instability':goal=a.route.get('temporary_goal',goal)
        weight=.15 if (active and group=='disconnect') else (0 if goal is None else 1.15)
        energy=a.expectations['energy'];attitude=a.expectations['attitude']
        scores=[]
        for action in ACTIONS:
            skill=a.skills.get(SKILLS[action],0.3) if SKILLS[action] else .4
            preference=a.beliefs['preference_'+action]
            score=.5*preference+.35*skill+.22*attitude + (weight if action==goal else 0)
            if action=='rest':score+=1.4*(1-energy)
            if action=='assist':score+=.4*a.traits['empathy']
            if action=='research':score+=.3*a.traits['curiosity']
            scores.append(score+rg.gammavariate(1,.18))
        action=ACTIONS[max(range(len(scores)),key=lambda i:scores[i])]
        counts[action]+=1
        if action=='rest':energy=min(1,energy+.14)
        else:
            energy=max(0,energy-.028)
            key=SKILLS[action]
            if key:
                a.skills[key]=min(1,a.skills[key]+.00055*(.6+a.traits['ambition'])*(1-a.skills[key]))
        # experience and attitudes updated; goals only change under assigned intervention
        a.expectations['energy']=energy
        a.expectations['attitude']=max(.05,min(.95,attitude+.003*(.5 if action==goal else -.1)))
        a.practiced[action]+=1
        if t%25==0:a.memory.append((t,action))
    return counts

def run(seed=42,baseline=200,intervention=400,recovery=200,followup=200):
    total=baseline+intervention+recovery+followup
    original=initialize(seed)
    # Identical baseline before branch cloning
    for t in range(baseline):tick(original,seed,t,'control',baseline,baseline+intervention)
    snapshot=copy.deepcopy(original)
    results=[];histories=[]
    for group in GROUPS:
        actors=copy.deepcopy(snapshot)
        base={a.id:dict(a.practiced) for a in actors}
        for t in range(baseline,total):
            counts=tick(actors,seed,t,group,baseline,baseline+intervention)
            if (t+1)%100==0:
                histories.append({'seed':seed,'group':group,'tick':t+1,**{x:counts[x] for x in ACTIONS}})
        for a in actors:
            pre=base[a.id];post={x:a.practiced[x]-pre.get(x,0) for x in ACTIONS}
            n=sum(post.values()); distribution={x:post[x]/max(1,n) for x in ACTIONS}
            original_goal=a.goal
            results.append({'seed':seed,'group':group,'founder':a.id,'baseline_goal':original_goal,
               'goal_action_share':distribution.get(original_goal,0),'skill_mean':sum(a.skills.values())/len(a.skills),
               'ambition':a.traits['ambition'],'partner':a.route['partner'],
               **{'actions_'+x:post[x] for x in ACTIONS}})
    return results,histories

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=5);ap.add_argument('--ticks',type=int,default=1000);ap.add_argument('--out',default='gd01_results');args=ap.parse_args()
    if args.ticks!=1000:raise ValueError('This pilot currently uses a fixed 200/400/200/200 phase schedule; use --ticks 1000.')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rows=[];history=[]
    for seed in range(42,42+args.seeds):
        r,h=run(seed);rows.extend(r);history.extend(h)
    for name,data in [('founder_results.csv',rows),('action_snapshots.csv',history)]:
        with (out/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
    summary=[]
    for g in GROUPS:
        z=[r for r in rows if r['group']==g]
        summary.append({'group':g,'founder_runs':len(z),'goal_action_share':round(sum(r['goal_action_share'] for r in z)/len(z),4),
          'mean_skill':round(sum(r['skill_mean'] for r in z)/len(z),4),
          'research_actions':round(sum(r['actions_research'] for r in z)/len(z),1),
          'craft_actions':round(sum(r['actions_craft'] for r in z)/len(z),1)})
    (out/'summary.json').write_text(json.dumps({'seeds':args.seeds,'founders_per_world':100,'branches':5,'ticks':1000,'notes':'Synthetic experimental extension of v0.18 Agent, not full physics-engine execution; no identity validation yet.','results':summary},indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
