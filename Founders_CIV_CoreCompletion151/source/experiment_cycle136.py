"""Cycle136 prolonged baseline vs Book-funded caregiver-assisted feeding.

Predeclared paired seeds (9711,9712,9731), 4 pairs/species, 5 habitats, no
extra capacity, RSW-K enabled. 30/60/120/180/360/720 milestones; inspect all
G1 cohorts, not just snapshots. Never changes species-specific maturity ages.
"""
import argparse,collections,csv,hashlib,json,os,pickle,statistics,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
sys.path.insert(0,str(Path(__file__).resolve().parent/'world023024'))
from experiment_cycle135 import start,fingerprint,config,scale,sources
from collections import Counter
from generation_audit_021108 import generation_metrics
from juvenile_support_cycle136 import enable_assisted_feeding
from long_horizon_audit_cycle136 import enable_precise_audit,enable_long_horizon_validation
from species_life_02115 import PROFILES
SEEDS=(9711,9712,9731)
DAYS=(30,60,120,180,360,720)


def make_sim(seed,assist):
    c=config(seed,4,False,True)
    sim=start(c)
    enable_precise_audit(sim)
    enable_long_horizon_validation(sim)
    if assist:enable_assisted_feeding(sim)
    return sim,c

def cohort_audit(sim):
    b=sim.bridge
    birth={e['actor']:e for e in b.events if e.get('event')=='birth' and e.get('generation')==1}
    deaths={e['actor']:e for e in b.events if e.get('event')=='death'}
    feeds=collections.Counter(e.get('actor') for e in b.events if e.get('event')=='feeding')
    care=collections.Counter(e.get('child') for e in b.events if e.get('event')=='parental_care')
    aided=collections.Counter(e.get('actor') for e in b.events if e.get('event')=='assisted_dependent_meal')
    records=[]
    for uid,event in sorted(birth.items()):
        a=b.actors[uid]; p=PROFILES[a.species]
        died=deaths.get(uid)
        # Death event day is authoritative; age from actor is updated daily,
        # and is retained after death. Censor live animals at observed day.
        observed_age = a.age
        early_enough=event['day']+p.maturity<=b.day
        records.append(dict(actor=uid,species=a.species,birth_day=event['day'],
            mother=event.get('mother'),father=event.get('father'),
            maturity_age=p.maturity,independence_age=p.independence,
            age_at_last_observation=observed_age,
            died=bool(died),death_day=died['day'] if died else None,
            death_cause=died.get('cause') if died else None,
            juvenile_death=bool(died and observed_age<p.maturity),
            died_before_independence=bool(died and observed_age<p.independence),
            reached_maturity=observed_age>=p.maturity,
            born_early_enough_to_mature=early_enough,
            feeding_events=feeds[uid],parental_care_events=care[uid],
            assisted_meals=aided[uid]))
    summary=dict(g1_births=len(records),g1_alive=sum(not x['died'] for x in records),
      g1_reached_maturity=sum(x['reached_maturity'] for x in records),
      g1_died_before_independence=sum(x['died_before_independence'] for x in records),
      g1_juvenile_deaths=sum(x['juvenile_death'] for x in records),
      g1_starvation_deaths=sum(x['death_cause']=='starvation' for x in records),
      g1_predation_deaths=sum(x['death_cause']=='predation' for x in records),
      g1_alive_juvenile=sum(not x['died'] and x['age_at_last_observation']<x['maturity_age'] for x in records),
      g1_no_feed_before_death=sum(x['died'] and x['feeding_events']==0 for x in records),
      g1_early_enough=sum(x['born_early_enough_to_mature'] for x in records),
      g1_mean_age_at_death=round(statistics.mean(x['age_at_last_observation'] for x in records if x['died']),3) if any(x['died'] for x in records) else None,
      g1_median_age_at_death=statistics.median(x['age_at_last_observation'] for x in records if x['died']) if any(x['died'] for x in records) else None)
    summary['by_species']={s:{'born':sum(x['species']==s for x in records),
                'died_before_independence':sum(x['species']==s and x['died_before_independence'] for x in records),
                'reached_maturity':sum(x['species']==s and x['reached_maturity'] for x in records),
                'starvation':sum(x['species']==s and x['death_cause']=='starvation' for x in records)}
                 for s in PROFILES}
    return summary,records

def summarize136(sim,day,c):
    b=sim.host.book;a=b.audit()
    if a['rejections'] or abs(a['mass_error'])>max(1e-6,1e-10*b.start_mass) or abs(a['energy_error'])>max(1e-6,1e-10*(b.start_energy+b.external)):
        raise AssertionError('Book conservation failed')
    bridge=sim.bridge; gen=generation_metrics(bridge)
    # Correct Cycle108's generic age>80 proxy: species have distinct maturity.
    g1=[x for x in bridge.actors.values() if x.generation==1]
    g1_adults=sum(x.alive and x.stage=='adult' for x in g1)
    g1_reached_maturity=sum(x.age>=PROFILES[x.species].maturity for x in g1)
    living=[x for x in bridge.actors.values() if x.alive]
    deaths=Counter(e.get('cause','unknown') for e in bridge.events if e.get('event')=='death')
    by_species=Counter(x.species for x in living)
    knowledge=dict(bridge.family_knowledge_metrics)
    source=sources(sim)
    return {'seed':c['seed'],'pairs':c['pairs'],'capacity':c['capacity'],
      'memory':c['memory'],'regime':c['regime'],'capacity_scale':scale(c),
      'day':day,'tick':sim.host.sim.tick,'living':len(living),
      'survival_fraction':len(living)/(10*c['pairs']),
      'living_species':dict(by_species),'g1_births':gen['g1_births'],
      'g1_living':gen['g1_living'],'g1_adults':g1_adults,
      'g1_reached_maturity_ever':g1_reached_maturity,
      'g2_births':gen['g2_births'],'death_causes':dict(deaths),
      'tree_state':str(bridge.tree.state),'book_rejections':a['rejections'],
      'mass_error':a['mass_error'],'energy_error':a['energy_error'],
      'knowledge_observations':knowledge.get('local_food_observations',0),
      'knowledge_funded_investments':knowledge.get('funded_investments',0),
      'knowledge_declined':knowledge.get('investment_declined_resource_or_health',0),
      'family_provisions':bridge.family_fluxes.get('provision_events',0),
      'sources':source,'book_transactions':a['transactions'],
      'habitat_plant':{h:b.mass[bridge.tree.acct('plant',h)] for h in bridge.tree.habitats}}

def run(seed,assist,dir,days=720,save_checkpoint=False):
    if seed not in SEEDS or type(assist) is not bool or days not in (360,720):
        raise ValueError('non-preregistered design')
    out=Path(dir);out.mkdir(parents=True,exist_ok=True)
    ident=f'C136_seed{seed}_assist{int(assist)}_day{days}'
    target=out/(ident+'.json')
    if target.exists():raise FileExistsError(target)
    started=time.monotonic();sim,c=make_sim(seed,assist)
    metrics=[];checkpoint=None
    for milestone in DAYS:
        if milestone>days:break
        for _ in range(milestone-(metrics[-1]['day'] if metrics else 0)):
            sim.step()
        row=summarize136(sim,milestone,c)
        cohort,_=cohort_audit(sim)
        row['cohort']=cohort
        row['assisted_feeding_metrics']=dict(getattr(sim.bridge,'juvenile_support_metrics',{}))
        metrics.append(row)
        if milestone==30 and save_checkpoint:
            snap=pickle.dumps(sim,protocol=pickle.HIGHEST_PROTOCOL)
            checkpoint=out/(ident+'.day30.pkl')
            checkpoint.write_bytes(snap)
            row['checkpoint_sha256']=hashlib.sha256(snap).hexdigest()
    cohort,actor_rows=cohort_audit(sim)
    result=dict(cycle=136,seed=seed,assisted_feeding=assist,days=days,
        configuration=c,milestones=metrics,final_cohort=cohort,
        individual_g1=actor_rows,capacity_funding=sim.capacity_funding,
        final_semantic_sha256=fingerprint(sim),
        checkpoint_file=checkpoint.name if checkpoint else None,
        duration_seconds=round(time.monotonic()-started,3))
    temp=target.with_suffix('.tmp');temp.write_text(json.dumps(result,sort_keys=True));os.replace(temp,target)
    return result

def replay(result_dir,seed,assist,days=720):
    target=Path(result_dir)/(f'C136_seed{seed}_assist{int(assist)}_day{days}.json')
    result=json.loads(target.read_text());cp=Path(result_dir)/result['checkpoint_file']
    blob=cp.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=result['milestones'][0]['checkpoint_sha256']:
        raise AssertionError('checkpoint byte hash mismatch')
    sim=pickle.loads(blob)
    for _ in range(days-30):sim.step()
    c=config(seed,4,False,True)
    if fingerprint(sim)!=result['final_semantic_sha256']:
        raise AssertionError('full semantic replay mismatch')
    direct=result['milestones'][-1];actual=summarize136(sim,days,c)
    for key,val in direct.items():
        if key in actual and val!=actual[key]:raise AssertionError('milestone mismatch '+key)
    return dict(seed=seed,assist=assist,days=days,match=True,
                checkpoint_sha256=hashlib.sha256(blob).hexdigest(),
                full_semantic_sha256=result['final_semantic_sha256'])

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seed',type=int,required=True)
    a.add_argument('--assist',type=int,choices=(0,1),required=True)
    a.add_argument('--days',type=int,choices=(360,720),default=720)
    a.add_argument('--output',required=True);a.add_argument('--checkpoint',action='store_true')
    args=a.parse_args();r=run(args.seed,bool(args.assist),args.output,args.days,args.checkpoint)
    print(json.dumps({'seed':args.seed,'assist':args.assist,'days':args.days,
        'living':r['milestones'][-1]['living'],'g1':r['final_cohort']['g1_births'],
        'g1_matured':r['final_cohort']['g1_reached_maturity'],
        'g1_starvation_deaths':r['final_cohort']['g1_starvation_deaths'],
        'g2_births':r['milestones'][-1]['g2_births'],
        'seconds':r['duration_seconds']}),flush=True)
