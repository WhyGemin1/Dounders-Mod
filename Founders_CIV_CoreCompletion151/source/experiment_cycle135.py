"""Cycle135: preregistered Cycle132 density x finite capacity x RSW-K memory experiment.

Experimental only. Native WORLD-023 demographic scheduler and bridge demographic
scheduler remain separate. All physical transfers go through one authoritative Book.
"""
import csv, hashlib, json, math, os, pickle, time, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"world023024"))
from collections import Counter
from src.integrated_02160 import Unified260
from src.habitat_bridge import SPECIES
from src.generation_audit_021108 import generation_metrics
from src.species_life_02115 import PROFILES

SEEDS=(9711,9712,9731,9732,9741,9742)
MILESTONES=(30,60,120,180)
DONOR_MASS=tuple(f'{kind}:Solara:{biome}' for kind in ('plant','soil','detritus','water') for biome in ('grassland','wetland'))
DONOR_ENERGY=('chem:Solara:grassland','chem:Solara:wetland','house')

def config(seed,pairs,capacity,memory,regime='fixed_total'):
    if seed not in SEEDS:raise ValueError('seed must be preregistered')
    if type(pairs)!=int or pairs not in (4,8):raise ValueError('pair level')
    if type(capacity)!=bool or type(memory)!=bool:raise ValueError('binary switches required')
    if regime not in ('fixed_total','scaled_per_capita'):raise ValueError('resource regime')
    return dict(seed=seed,pairs=pairs,capacity=capacity,memory=memory,regime=regime)

def scale(c):
    return (0.5 if c['pairs']==4 or c['regime']=='fixed_total' else 1.0) if c['capacity'] else 0.0

def sources(sim):
    b=sim.host.book
    return {'mass':{x:b.mass[x] for x in DONOR_MASS},'energy':{x:b.energy[x] for x in DONOR_ENERGY}}

def start(c):
    sim=Unified260(seed=c['seed'],counts={k:2*c['pairs'] for k in SPECIES},
                  five_habitats=True,capacity_scale=scale(c),family_benefits=True,
                  resource_aware_family=c['memory'])
    for species in SPECIES:
        pairs=[p for p in sim.bridge.family_pairs if p.startswith('family:'+species+':')]
        if len(pairs)!=c['pairs']:raise AssertionError('founding pair count mismatch')
    if sim.host.book is not sim.bridge.tree.book:raise AssertionError('distinct Books')
    return sim

def summarize(sim,day,c):
    b=sim.host.book;a=b.audit()
    if a['rejections'] or abs(a['mass_error'])>1e-6 or abs(a['energy_error'])>1e-6:
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

def run_arm(c,out_dir,save_checkpoint=False):
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:16]
    dest=out_dir/(key+'.json')
    if dest.exists():raise FileExistsError(dest)
    start_time=time.monotonic();sim=start(c)
    initial=sources(sim)
    rows=[];last=0;checkpoint=None
    for day in MILESTONES:
        for _ in range(day-last):sim.step()
        row=summarize(sim,day,c);rows.append(row)
        if day==30 and save_checkpoint:
            checkpoint=out_dir/(key+'.day30.pkl')
            binary=pickle.dumps(sim,protocol=pickle.HIGHEST_PROTOCOL)
            checkpoint.write_bytes(binary)
            row['checkpoint_sha256']=hashlib.sha256(binary).hexdigest()
        last=day
    final_digest=fingerprint(sim) if checkpoint else None
    # The finite funding is an actual external debit at init, with a material
    # balance receipt. Later donor dynamics can regenerate: don't confuse those
    # with a shipment receipt.
    data={'configuration':c,'initial_donor_balances':initial,
          'funding_receipt':sim.capacity_funding,'milestones':rows,
          'checkpoint_file':checkpoint.name if checkpoint else None,
          'day180_semantic_state_sha256':final_digest,
          'elapsed_seconds':round(time.monotonic()-start_time,2)}
    temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,sort_keys=True))
    os.replace(temp,dest)
    return data

def stable(x, seen=None,depth=0):
    """Canonical semantic digest; excludes incidental object/pickle identity."""
    if seen is None:seen=set()
    if x is None or type(x) in (int,float,str,bool):return x
    if depth>15:raise ValueError('unexpected recursive state')
    if isinstance(x,dict):return {str(k):stable(v,seen,depth+1) for k,v in sorted(x.items(),key=lambda p:str(p[0]))}
    if isinstance(x,(tuple,list)):return [stable(v,seen,depth+1) for v in x]
    if isinstance(x,set):return sorted([stable(v,seen,depth+1) for v in x],key=str)
    if hasattr(x,'__dict__'):
        if id(x) in seen:raise ValueError('cyclic object in selected state')
        seen.add(id(x)); r=stable(vars(x),seen,depth+1);seen.remove(id(x));return r
    raise TypeError(f'unexpected state type {type(x)}')

def fingerprint(sim):
    bridge=sim.bridge;book=sim.host.book;tree=bridge.tree
    # This is a semantic state digest, NOT just a survivor count. Include
    # physical accounts, lineage/cognition, spatial coordinates, tree and events.
    data={'clock':sim.host.sim.tick,'bridge_day':bridge.day,
          'book_mass':stable(dict(book.mass)),'book_energy':stable(dict(book.energy)),
          'book_audit':stable(book.audit()),
          'actors':{i:stable(a) for i,a in sorted(bridge.actors.items())},
          'bridge_events':stable(bridge.events),'positions':stable(bridge.positions),
          'bridge_rng_state':stable(bridge.rng.getstate()),
          'tree_state':tree.state,'tree_counters':stable(dict(tree.counters)),
          'tree_events':stable(tree.daily_events),
          'tree_timeline':stable(tree.timeline),
          'knowledge_events':stable(tree.sim.knowledge.events),
          'family_knowledge_metrics':stable(dict(bridge.family_knowledge_metrics)),
          'family_fluxes':stable(dict(bridge.family_fluxes)),
          'knowledge_claims':stable(tree.sim.knowledge.claims),
          'donors':sources(sim)}
    return hashlib.sha256(json.dumps(data,sort_keys=True,default=str).encode()).hexdigest()

def replay30_150(c,out_dir):
    out_dir=Path(out_dir);key=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:16]
    record=json.loads((out_dir/(key+'.json')).read_text())
    snap=(out_dir/(key+'.day30.pkl')).read_bytes()
    if hashlib.sha256(snap).hexdigest()!=record['milestones'][0]['checkpoint_sha256']:
        raise AssertionError('checkpoint hash altered')
    sim=pickle.loads(snap)
    if sim.host.sim.tick!=record['milestones'][0]['tick']:
        raise AssertionError('checkpoint clock altered')
    for _ in range(150):sim.step()
    actual=summarize(sim,180,c)
    expected=record['milestones'][-1]
    for k in expected:
        if k not in actual or actual[k]!=expected[k]:
            raise AssertionError('replay mismatch at '+k)
    replay_hash=fingerprint(sim)
    if replay_hash!=record['day180_semantic_state_sha256']:
        raise AssertionError('full semantic state replay mismatch')
    return {'config':c,'match':True,'checkpoint_sha256':hashlib.sha256(snap).hexdigest(),
        'semantic_state_sha256':replay_hash,'target_day':180,'book_rejections':actual['book_rejections']}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True)
    p.add_argument('--pairs',type=int,required=True);p.add_argument('--capacity',type=int,choices=[0,1],required=True)
    p.add_argument('--memory',type=int,choices=[0,1],required=True)
    p.add_argument('--regime',choices=['fixed_total','scaled_per_capita'],default='fixed_total')
    p.add_argument('--output',required=True);p.add_argument('--save-checkpoint',action='store_true')
    arg=p.parse_args();c=config(arg.seed,arg.pairs,bool(arg.capacity),bool(arg.memory),arg.regime)
    d=run_arm(c,arg.output,arg.save_checkpoint)
    print(json.dumps({'arm':c,'last':d['milestones'][-1]['living'],'g1_adults':d['milestones'][-1]['g1_adults'],
       'g2_births':d['milestones'][-1]['g2_births'],'seconds':d['elapsed_seconds']},sort_keys=True),flush=True)
