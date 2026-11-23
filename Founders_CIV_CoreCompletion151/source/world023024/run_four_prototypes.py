"""Run the four stand-alone v0.19 prototype demonstrations and save auditable data."""
from pathlib import Path
from json import dumps
import csv
from founders_civ.core.ledger import Book
from founders_civ.experimental import FounderRegistry,SoulNetwork,Population,ConstructRegistry

OUT=Path(__file__).parent/'results'/'experimental'
OUT.mkdir(parents=True,exist_ok=True)

def founder_demo():
    book=Book();book.seed_mass('goods:F001:wood',3);book.seed_energy('house',100);book.freeze()
    reg=FounderRegistry(book,seed=42)
    actor=reg.people['F001'];actor.inventory['wood']=3
    reg.learn('F001','crafting',2,'trained at House');reg.checkpoint('F001')
    reg.learn('F001','crafting',4,'practiced on world');actor.location='world'
    reborn=reg.die('F001');audit=book.audit()
    return dict(founders=len(reg.people),pairs=len({tuple(sorted((x.id,x.partner_id))) for x in reg.people.values()}),
                reborn=reborn,restored_skill=actor.skills['crafting'],
                retained_memories=actor.memories,dropped_material=book.mass['goods:dropped:world:wood'],
                checkpoint_version=actor.checkpoint_version,audit=audit)

def soul_demo():
    book=Book();book.seed_mass('background:world',0);book.seed_energy('actor:adept',12);book.freeze()
    s=SoulNetwork('adept',intrinsic_mode=4)
    for i in range(12):
        s.practice(f'node{i}',f'practice{i}:one');s.practice(f'node{i}',f'practice{i}:two')
        s.develop_state(f'state{i}',[f'node{i}'],schema_depth=.7)
    for k in range(4):
        states=[f'state{i}' for i in range(k*3,k*3+3)]
        s.kingdom(f'kingdom{k}',states,[(states[0],states[1]),(states[1],states[2])])
    s.nation('nation1',['state0','state4','state7','state11'])
    s.earn_emperor([f'practice{i}:one' for i in range(4)])
    s.realm('realm1',[f'kingdom{k}' for k in range(4)])
    r1=s.activate('state1',3,2,4,book,'actor:adept')
    r2=s.activate('state1',70,2,3,book,'actor:adept')
    r3=s.activate('state1',2,2,4,book,'actor:adept')
    return dict(states=len(s.states),kingdoms=len(s.kingdoms),nations=len(s.nations),realms=len(s.realms),
                outcomes=[r1.value,r2.value,r3.value],remaining_actor_energy=book.energy['actor:adept'],audit=book.audit())

def evolution_demo():
    rows=[]
    for seed in range(101,116):
        for climate in ('cold','mild'):
            p=Population(seed=seed,n=30,food_per_patch=250)
            initial=sum(o.genotype['cold_tolerance'] for o in p.people.values())/30
            p.people['G00001'].learned_routes.add('route:south')
            for generation in range(8):p.step(climate)
            q=p.summary()
            rows.append(dict(seed=seed,climate=climate,generations=8,
                             initial_cold_trait=initial,final_cold_trait=q['cold_tolerance_mean'],
                             surviving=q['alive'],births=q['births'],deaths=q['deaths'],
                             route_knowledge=q['route_knowledge'],
                             mass_error=q['mass_audit']['mass_error'],energy_error=q['mass_audit']['energy_error']))
    with (OUT/'evolution_trials.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    def avg(key,climate):
        data=[r[key] for r in rows if r['climate']==climate and r[key] is not None]
        return sum(data)/len(data)
    return dict(trials=len(rows),mean_cold_trait_cold=avg('final_cold_trait','cold'),
                mean_cold_trait_mild=avg('final_cold_trait','mild'),
                mean_final_population_cold=avg('surviving','cold'),
                mean_final_population_mild=avg('surviving','mild'),
                mean_births_cold=avg('births','cold'),
                max_abs_mass_error=max(abs(r['mass_error']) for r in rows),
                max_abs_energy_error=max(abs(r['energy_error']) for r in rows))

def construct_demo():
    results={}
    for mode in ('unfunded','refueled'):
        b=Book();b.seed_mass('stone:world',10);b.seed_energy('house',70);b.seed_energy('world_work',100);b.freeze()
        reg=ConstructRegistry(b)
        c=reg.build('dim','dimension','world_A','stone:world',mass=5,daily_energy=1,initial_reserve=0,
                    collapse_to='mist')
        statuses=[]
        for day in range(1,9):
            if mode=='refueled' and day==1:reg.top_up('dim',9)
            statuses.append(reg.tick('dim'))
        results[mode]=dict(final_status=c.status,days=statuses,
                           remnant_mass=b.mass['mist:dim'],tolls=b.toll_count,
                           audit=b.audit())
    return results

if __name__=='__main__':
    results=dict(founders=founder_demo(),soul=soul_demo(),evolution=evolution_demo(),constructs=construct_demo())
    (OUT/'sample_results.json').write_text(dumps(results,indent=2))
    print(dumps(results,indent=2))
    print('\nSaved:',OUT/'sample_results.json')
