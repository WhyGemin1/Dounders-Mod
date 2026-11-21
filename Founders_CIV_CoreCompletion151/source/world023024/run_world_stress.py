"""96 distinct deterministic WORLD-022 integration stressors (12 families x 8).

Stressors are interventions against coupled SOCIAL-021 + v0.18 physical engine.
They test INTERNAL correctness; no human realism or world ecology validity claim.
"""
from __future__ import annotations
import argparse,csv,json,math,time
from collections import Counter
from pathlib import Path
from statistics import mean
from founders_civ.experimental.world_integration import IntegratedWorld
from test_world_integration import make_realm

FAMILIES=[
 'coupled_clock','energy_shock','substrate_shock','invalid_blueprint',
 'dependency_rejection','planting_validity','maintenance_lapse','checkpoint_rollback',
 'social_ablation','determinism','parent_cascade','cognitive_stressor'
]

def expect_reject(fn,needle=None):
    try:fn()
    except (ValueError,KeyError,TypeError) as exc:
        if needle and needle.lower() not in str(exc).lower():raise AssertionError(f'wrong rejection {exc}')
        return str(exc)
    raise AssertionError('expected rejection did not occur')

def refill(s,who='F001',qty=4):
    if s.book.energy[f'founder:{who}']<qty:
        missing=qty-s.book.energy[f'founder:{who}']
        s.book.move(energy=[('river_pool',f'founder:{who}',missing)])

def child(s,parent,kind,name):
    author='F001';refill(s,author,5.5)
    pos=(parent['x']+2,parent['y']+2)
    b=s.seeds.draft(author,kind,name,parent['id'],x=pos[0],y=pos[1]);s.seeds.research(author,b.id)
    s.step()
    if s.tick not in b.research_ticks:s.seeds.research(author,b.id)
    peer=next(q for q,v in s.founders.people.items() if q!=author and v.location==s.founders.people[author].location)
    s.seeds.validate(peer,b.id)
    refill(s,author,2)
    return s.seeds.plant(author,b.id)

def test_case(family,index,seed):
    mode=['full','no_partner','no_teach','no_faction','neutral_trust','isolated','full','no_faction'][index] if family=='social_ablation' else 'full'
    s=IntegratedWorld(seed=seed,social_mode=mode,days=65)
    details={};desc='';cycles=0
    if family=='coupled_clock':
        n=index+1
        for _ in range(n):s.step()
        cycles=n
        assert s.ecology.day==s.tick and s.counter['decision']==n*100
        assert s.book is s.ecology.book is s.founders.book
        desc=f'Run {n} coupled ecology/social/construct cycles'
    elif family=='energy_shock':
        fid=f'F{index+1:03d}'
        start=s.book.energy[f'founder:{fid}'];rate=[.04,.20,.35,.50,.65,.82,.96,1.0][index]
        s.book.move(energy=[(f'founder:{fid}','environment:heat',start*rate)])
        before=s.book.energy[f'founder:{fid}']
        for _ in range(3):s.step()
        cycles=3;assert s.book.energy[f'founder:{fid}']>=0
        details={'founder':fid,'removed_fraction':rate,'remaining_before_cycles':round(before,5)}
        desc=f'Funded founder energy loss {rate:.0%}, then 3 cycles'
    elif family=='substrate_shock':
        amount=s.book.mass['soil:Solara:grassland']*[.04,.12,.20,.3,.44,.6,.82,.995][index]
        s.book.move(material=[('soil:Solara:grassland','soil:Solara:ridge',amount)])
        before=s.book.mass['soil:Solara:grassland']
        for _ in range(3):s.step()
        cycles=3;assert s.book.mass['soil:Solara:grassland']>=0
        details={'moved_material':round(amount,4),'remaining':round(before,4)}
        desc=f'Move {amount:.2f} physical soil units between patches'
    elif family=='invalid_blueprint':
        cases=[('kind',lambda:s.seeds.draft('F001','ghost','Name',x=50,y=50)),
               ('short_name',lambda:s.seeds.draft('F001','realm','X',x=50,y=50)),
               ('bad_rule',lambda:s.seeds.draft('F001','realm','Name',rules={'unknown':.3},x=50,y=50)),
               ('nan_rule',lambda:s.seeds.draft('F001','realm','Name',rules={'stability':float('nan')},x=50,y=50)),
               ('overflow_rule',lambda:s.seeds.draft('F001','realm','Name',rules={'stability':1.1},x=50,y=50)),
               ('underflow_rule',lambda:s.seeds.draft('F001','realm','Name',rules={'stability':-.01},x=50,y=50)),
               ('coordinate',lambda:s.seeds.draft('F001','realm','Name',x=101,y=50)),
               ('infinite_coord',lambda:s.seeds.draft('F001','realm','Name',x=float('inf'),y=50))]
        label,fn=cases[index]
        before=s.book.energy['founder:F001']
        details={'rejection':expect_reject(fn),'energy_unchanged':s.book.energy['founder:F001']==before}
        assert s.book.energy['founder:F001']==before
        desc=f'Malformed seed input: {label}'
    elif family=='dependency_rejection':
        if index==0:fn=lambda:s.seeds.draft('F001','world','No realm')
        elif index==1:fn=lambda:s.seeds.draft('F001','underworld','No world')
        elif index==2:fn=lambda:s.seeds.draft('F001','species','No world')
        elif index==3:fn=lambda:s.seeds.draft('F001','dimension','No realm')
        elif index==4:fn=lambda:s.seeds.draft('F001','realm','Wrong parent','CRE-99999',x=66,y=45)
        else:
            b=s.seeds.draft('F001','realm',f'Draft {index}',x=65,y=45)
            if index==5:fn=lambda:s.seeds.plant('F001',b.id)
            elif index==6:fn=lambda:s.seeds.validate('F002',b.id)
            else:
                s.seeds.research('F001',b.id);fn=lambda:s.seeds.research('F001',b.id)
        details={'rejection':expect_reject(fn)}
        desc=['world without realm','underworld without world','species without world','dimension without realm','realm with forbidden host','plant draft before validation','review before research','repeat research same cycle'][index]
    elif family=='planting_validity':
        refill(s)
        rules={'stability':.25+.1*index,'recycling':.14+.09*index}
        b=s.seeds.draft('F001','realm',f'Island {index}',rules=rules,x=48+index*4,y=48)
        s.seeds.research('F001',b.id);s.step();cycles=1
        if s.tick not in b.research_ticks:s.seeds.research('F001',b.id)
        peer=next(a for a,f in s.founders.people.items() if a!='F001' and f.location==s.founders.people['F001'].location)
        s.seeds.validate(peer,b.id)
        refill(s)
        before=s.book.mass['soil:Solara:grassland'];c=s.seeds.plant('F001',b.id)
        assert abs((before-s.book.mass['soil:Solara:grassland'])-2.5)<1e-7
        assert c['kind']=='realm' and s.book.mass[f'construct:{c["id"]}']>0
        details={'id':c['id'],'rule_stability':rules['stability']}
        desc=f'Verified island-seed planting with distinct operating rules {index}'
    elif family=='maintenance_lapse':
        refill(s);realm=make_realm(s,name=f'Maintenance {index}',x=65,y=45);cycles=s.tick
        # Test underfunding from 0 through 7 replenishment cycles. Other actors
        # remain eligible to fund independently; only forced amount is controlled.
        for j in range(8):
            if j<index: s.seeds.tend('F001',realm['id'],.25)
            s.seeds.advance()
        result=s.seeds.plants[realm['id']]['status']
        assert result in ('stable','collapsed')
        if result=='collapsed':details['tend_rejection']=expect_reject(lambda:s.seeds.tend('F001',realm['id'],.6))
        details['status']=result
        desc=f'Plant then apply {index} active maintenance top-ups / 8 decay cycles'
    elif family=='checkpoint_rollback':
        fid=f'F{index+1:03d}';f=s.founders.people[fid]
        s.save_checkpoint(fid)
        prev=f.skills['research']
        s.founders.learn(fid,'research',.09+.01*index,f'test:unsaved:{index}')
        s.states[fid].cognition.claim('field_care').understanding=.3+.05*index
        before=s.book.audit()['mass_total']
        success=s.kill_and_rebirth(fid)
        assert success and abs(f.skills['research']-prev)<1e-9
        assert s.book.audit()['mass_total']==before
        assert s.states[fid].cognition.knowledge.get('field_care',None) is None
        details={'restored_skill':round(f.skills['research'],4),'deaths':f.deaths}
        desc=f'Checkpoint mortality and unsaved knowledge loss F{index+1:03d}'
    elif family=='social_ablation':
        for _ in range(5+index):s.step()
        cycles=s.tick
        assert s.counter['decision']==cycles*100
        if mode=='no_faction':assert len(s.factions)==0
        if mode=='isolated':assert s.counter['teach']==0
        details={'mode':mode,'factions':len(s.factions),'teach':s.counter['teach']}
        desc=f'Run {mode} social intervention for {cycles} cycles with active ecology'
    elif family=='determinism':
        other=IntegratedWorld(seed=seed,days=65)
        for _ in range(index+1):s.step();other.step()
        cycles=index+1
        assert s.summary(include_events=False)['actions']==other.summary(include_events=False)['actions']
        assert s.seeds.export()==other.seeds.export()
        assert s.book.audit()['transactions']==other.book.audit()['transactions']
        details={'equal_transactions':True,'equal_creations':True}
        desc=f'Exact cloned-seed replay across {cycles} integrated cycles'
    elif family=='parent_cascade':
        refill(s,qty=8)
        island=make_realm(s,name=f'Island {index}',x=65,y=45)
        refill(s,qty=8)
        tree=child(s,island,'world',f'World {index}')
        cycles=s.tick
        if index%2:
            try:flower=child(s,tree,'underworld',f'Flower {index}')
            except ValueError:flower=None
        else:flower=None
        if index%4<2:s.seeds.constructs.collapse(island['id'])
        else:s.seeds.constructs.collapse(tree['id'])
        s.seeds.advance()
        if s.seeds.plants[island['id']]['status']=='collapsed':
            assert s.seeds.plants[tree['id']]['status']=='collapsed'
        if flower and s.seeds.plants[tree['id']]['status']=='collapsed':
            assert s.seeds.plants[flower['id']]['status']=='collapsed'
        details={'root':s.seeds.plants[island['id']]['status'],'world':s.seeds.plants[tree['id']]['status'],'flower':s.seeds.plants[flower['id']]['status'] if flower else 'not_planted'}
        desc=f'Physically collapse {"realm" if index%4<2 else "world"} and check child cascade'
    elif family=='cognitive_stressor':
        for _ in range(index+2):s.step()
        cycles=s.tick
        actor=f'F{index+1:03d}'
        me=s.states[actor]
        target=s.founders.people[actor].partner_id
        # Directed trust changes via evidence and action policy; no stock mutations.
        me.cognition.partner(target).update('integrity',index%2==0,strength=.2+.13*index)
        me.cognition.partner(target).update('ability',index%3==0,strength=.2+.09*index)
        me.main_goal=['research','solidarity','leadership','exploration'][index%4]
        s.step();cycles+=1
        assert s.states[actor].main_goal in ['research','solidarity','leadership','exploration'] or s.states[actor].main_goal in ('mastery','security')
        details={'changed_founder':actor,'target':target,'goal_after':s.states[actor].main_goal}
        desc=f'Trust-belief evidence perturbation + goal update {index} and one more cycle'
    else:raise AssertionError(family)
    audit=s.book.audit()
    assert s.book is s.ecology.book is s.founders.book
    assert s.founders.integrity()
    assert s.tick==s.ecology.day
    assert abs(audit['mass_error'])<1e-6 and abs(audit['energy_error'])<1e-5
    assert min(s.book.mass.values())>=-1e-7 and min(s.book.energy.values())>=-1e-7
    for bp in s.seeds.blueprints.values():
        if bp.planted_id:
            assert bp.stage=='planted' and bp.validation_event and len(bp.research_ticks)>=2
    for item in s.seeds.plants.values():
        if item['parent']:
            p=s.seeds.plants[item['parent']]
            if item['status']=='stable':assert p['status']=='stable'
    return {'description':desc,'cycles':cycles,'actors':len(s.founders.people),
            'blueprints':len(s.seeds.blueprints),'creations':len(s.seeds.plants),
            'physical_transactions':audit['transactions'],
            'event_count':len(s.events)+len(s.ecology.events),
            'mass_error':audit['mass_error'],'energy_error':audit['energy_error'],
            'details':details}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results/world_stress');ap.add_argument('--repeats',type=int,default=8)
    args=ap.parse_args();folder=Path(args.out);folder.mkdir(parents=True,exist_ok=True)
    rows=[];start=time.perf_counter()
    for fam_index,family in enumerate(FAMILIES):
        for variant in range(args.repeats):
            index=fam_index*args.repeats+variant;seed=32000+index
            try:
                x=test_case(family,variant,seed)
                rows.append({'id':f'STR-{index+1:03d}','family':family,'seed':seed,'variant':variant,
                             'pass':True,**x})
            except Exception as exc:
                rows.append({'id':f'STR-{index+1:03d}','family':family,'seed':seed,'variant':variant,
                             'pass':False,'description':f'{family}:variant{variant}','details':{'error':type(exc).__name__+': '+str(exc)},
                             'cycles':0,'actors':0,'blueprints':0,'creations':0,'physical_transactions':0,'event_count':0,'mass_error':None,'energy_error':None})
        print(f'{family}: {sum(r["pass"] for r in rows if r["family"]==family)}/{args.repeats}',flush=True)
    elapsed=time.perf_counter()-start
    flds=['id','family','seed','variant','description','pass','cycles','actors','blueprints','creations','physical_transactions','event_count','mass_error','energy_error','details']
    with (folder/'stressors.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=flds);w.writeheader()
        for r in rows:w.writerow({**r,'details':json.dumps(r['details'],sort_keys=True)})
    report={'version':'WORLD-022','interpretation':'Synthetic integration stress tests; internal invariants only. Provisional parameters.',
            'stressors':len(rows),'passed':sum(r['pass'] for r in rows),'failed':sum(not r['pass'] for r in rows),
            'duration_sec':round(elapsed,2),'families':{fam:sum(r['pass'] for r in rows if r['family']==fam) for fam in FAMILIES},
            'max_abs_mass_error':max(abs(r['mass_error']) for r in rows if r['mass_error'] is not None),
            'max_abs_energy_error':max(abs(r['energy_error']) for r in rows if r['energy_error'] is not None),
            'total_engine_cycles':sum(r['cycles'] for r in rows),
            'total_physical_transactions':sum(r['physical_transactions'] for r in rows),
            'failures':[r for r in rows if not r['pass']]}
    (folder/'summary.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
    print('SUMMARY',json.dumps(report,indent=2),flush=True)
    return report['failed']==0
if __name__=='__main__':raise SystemExit(0 if main() else 1)
