"""Faithful read-only views of the v0.17 live engine. No extra mechanics are invented.

Animated x/y scatter locations are provided by the browser only. Simulation ecology
runs on named habitat patches, not continuous coordinates.
"""
from __future__ import annotations
from collections import Counter
from .core.engine import Simulation, PATCH_NAMES, WORLD_NAMES, SPECIES
from .canon import SYSTEMS, EXPERIMENT, TOLL

IMPORTANT={'decision','teach','migrate','hunt_attempt','death','pledge_deposit',
           'institution_founded','shared_norm_formed','rule_revision','institution_monitor',
           'ritual','practice','observe_weather','institution_distribute','harvest',
           'photosynthesis','wellspring','sunlight','graze','scavenge'}

class ObservatorySimulation(Simulation):
    def __init__(self,seed=42,days=30,arm='1111',trace=True,progress=None):
        super().__init__(seed=seed,days=days,arm=arm,trace=trace)
        self.frames=[]
        self.progress=progress
        self.frames.append(self.capture())

    def capture(self):
        book=self.book
        actor_rows=[]
        for a in sorted(self.actors.values(),key=lambda x:x.id):
            actor_rows.append([a.id,a.patch,a.alive,round(a.health,2),
                               round(a.needs.get('phys',0.),1),
                               round(a.conviction,3),
                               round(book.energy[f'reserve:{a.id}'],3),
                               len(a.nodes),round(a.needs.get('safety',0.),1),round(a.needs.get('belonging',0.),1),round(a.needs.get('esteem',0.),1),round(a.needs.get('purpose',0.),1),round(a.fear,3)])
        patches={}
        for world in WORLD_NAMES:
            for patch in PATCH_NAMES:
                p=f'{world}:{patch}'
                patches[p]={k:round(book.mass[f'{k}:{p}'],3)
                    for k in ('plant','soil','water','detritus','carcass')}
        inst=[]
        for i in sorted(self.institutions.values(),key=lambda x:x.id):
            inst.append(dict(id=i.id,settlement=i.settlement,members=len(i.members),
                             founded=i.founded,pool=round(book.mass[i.pooled_account],4),
                             monitoring=i.monitoring_events,work=i.work_events,
                             norm=i.public_claim if i.shared_norm else '',revision=i.revised))
        return dict(day=self.day,actors=actor_rows,patches=patches,
                    house=round(book.energy['house'],3),
                    underworld=round(sum(book.energy[f'underworld:{j}'] for j in range(10)),4),
                    heat={w:round(book.energy[f'heat:{w}'],3) for w in WORLD_NAMES},
                    daylight=self.daylight.copy(),
                    institutions=inst,
                    claims=self.counter['claim_exposures'],
                    tolls=self.book.toll_count)

    def step(self):
        super().step()
        self.frames.append(self.capture())
        if self.progress:self.progress(self.day,self.days)

    def export(self):
        outcome=self.summary()
        # Keep a readable compact event log (large future runs are still bounded).
        interesting=[]
        for e in self.events:
            if e['action'] not in IMPORTANT:continue
            if e['action'] in ('sunlight','photosynthesis','wellspring','graze') and e['event_id']%29:continue
            if e['action']=='decision' and e['event_id']%11:continue
            row={k:e.get(k) for k in ('event_id','day','action','actor','world','patch',
                 'claim','recipient','source_id','partner','institution','target','cause',
                 'to_patch','from_patch','chosen_action','transaction_id') if e.get(k) is not None}
            interesting.append(row)
        catalog={a.id:{'species':a.species,'world':a.world,'group':a.group,
                 'age_at_export':a.age,'traits':{k:round(v,3) for k,v in a.traits.items()},
                 'skills':{k:round(v,3) for k,v in a.skills.items()},
                 'beliefs':a.beliefs,'goal':a.goal,'source_memories':len(a.source_memory),
                 'memory_events':len(a.memory),'developed_nodes':sorted(a.nodes)}
                 for a in sorted(self.actors.values(),key=lambda x:x.id)}
        edges=[dict(source=x.source,target=x.target,type=x.relation,
                    trust=round(x.trust,2),respect=round(x.respect,2))
               for target in sorted(self.edges) for x in self.edges[target]]
        return dict(schema='founders-civ-observatory/1.0',
            version='0.18-observatory-on-0.17-core',
            disclaimer='The animated cell coordinates are diagrammatic; only habitat patch movement is simulated.',
            configuration=dict(seed=self.seed,days=self.days,arm=self.arm,factors=EXPERIMENT['factors']),
            results=outcome,units=dict(mass='abstract mass',energy='experimental EU',time='days'),
            species={k:dict(v) for k,v in SPECIES.items()},
            actors=catalog,edges=edges,frames=self.frames,events=interesting,
            daily=self.daily,systems=SYSTEMS,toll=TOLL,
            event_counts=dict(self.counter),
            audit=outcome['physical_audit'])
