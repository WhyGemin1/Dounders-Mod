"""Founders-CIV WORLD-022, coupled SOCIAL-021 and ecological core.

One Book, one cycle, physically funded planting. 100 Founder identities live in
FounderRegistry while the two v0.18 Founder placeholders remain inert contextual
records. Creation-tree/island/flower visualization is a symbolic ontology: a planted
world is not yet a separately simulated biosphere.

Provisional mechanics do NOT assert empirical realism or canon numeric thresholds.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from copy import deepcopy
from collections import Counter
from math import isfinite
from random import Random
from typing import Optional

from founders_civ.core.engine import Simulation as EcologicalSimulation
from founders_civ.experimental.constructs import ConstructRegistry
from founders_civ.experimental.social_agents import SocialSimulation, stable_seed
from founders_civ.experimental.world_trees import WorldTreeRegistry, WorldTree

SEED_KINDS={
    'realm': {'symbol':'island','material':2.5,'daily_energy':.13,'initial_reserve':1.2,'binding':1.25},
    'world': {'symbol':'tree','material':1.1,'daily_energy':.11,'initial_reserve':1.0,'binding':1.25},
    'underworld': {'symbol':'flower','material':.5,'daily_energy':.095,'initial_reserve':.90,'binding':1.25},
    'species': {'symbol':'sprout','material':.28,'daily_energy':.055,'initial_reserve':.65,'binding':1.25},
    'dimension': {'symbol':'portal','material':.75,'daily_energy':.16,'initial_reserve':1.3,'binding':1.25},
}
RULE_DEFAULTS={
    'daylight':.55, 'moisture':.60, 'biodiversity':.45, 'stability':.75,
    'recycling':.60, 'openness':.50, 'lifespan':.65,
}
PARENTS={'realm':None,'world':'realm','underworld':'world','species':'world','dimension':'realm'}
SITE_TO_PATCH={'house':'Solara:grassland','riverbank':'Solara:wetland',
               'fields':'Solara:forest','ridge':'Solara:ridge'}

@dataclass
class SeedBlueprint:
    id:str
    author:str
    kind:str
    name:str
    parent_id:Optional[str]
    rules:dict[str,float]
    created_tick:int
    x:float=0.0
    y:float=0.0
    stage:str='draft'
    research_ticks:set[int]=field(default_factory=set)
    evidence_ids:list[str]=field(default_factory=list)
    reviewer:Optional[str]=None
    validation_event:Optional[str]=None
    planted_id:Optional[str]=None
    notes:list[str]=field(default_factory=list)

class SeedRegistry:
    """Information-first creation process; its physical effects use the core Book."""
    def __init__(self,sim):
        self.sim=sim
        self.blueprints={}
        self.constructs=ConstructRegistry(sim.book)
        self.plants={}
        self.owner_reserve_knowledge={}
        self.events=[]

    def _event(self,kind,actor,bp,txn=None,**data):
        event=self.sim.log(kind,actor,parent=getattr(self.sim,'_current_parent',None),txn=txn,blueprint=bp.id,creation=bp.planted_id,**data)
        self.events.append(event)
        return event

    def _need_actor(self,actor):
        f=self.sim.founders.people.get(actor)
        if f is None or not f.alive:raise ValueError('active Founder required')
        return f

    def _pay_effort(self,actor,q):
        self._need_actor(actor)
        if self.sim.book.energy[f'founder:{actor}']<q:raise ValueError('not enough Founder energy')
        return self.sim.book.move(energy=[(f'founder:{actor}','environment:heat',q)])

    def _parent(self,kind,parent_id,require_active=True):
        required=PARENTS[kind]
        if required is None:
            if parent_id is not None:raise ValueError('realm must be planted in the Sea, no parent')
            return None
        if not parent_id or parent_id not in self.plants:
            raise ValueError(f'{kind} requires a planted parent {required}')
        p=self.plants[parent_id]
        if p['kind']!=required:raise ValueError(f'{kind} requires parent {required}')
        if require_active and p['status']!='stable':raise ValueError('parent has collapsed')
        return p

    def draft(self,actor,kind,name,parent_id=None,rules=None,x=0.,y=0.):
        self._need_actor(actor)
        if kind not in SEED_KINDS:raise ValueError('invalid seed kind')
        if not isinstance(name,str) or not 2<=len(name.strip())<=52:raise ValueError('name must contain 2–52 characters')
        if not isfinite(float(x)) or not isfinite(float(y)):raise ValueError('invalid position')
        if not all(isfinite(float(v)) for v in (x,y)):raise ValueError('nonfinite position')
        if not 0<=float(x)<=100 or not 0<=float(y)<=100:raise ValueError('position outside Sea canvas')
        vals=dict(RULE_DEFAULTS)
        if rules:
            if not isinstance(rules,dict) or any(k not in RULE_DEFAULTS for k in rules):raise ValueError('unknown blueprint rules')
            for k,v in rules.items():
                if isinstance(v,bool) or not isinstance(v,(float,int)) or not isfinite(float(v)) or not 0<=v<=1:
                    raise ValueError(f'invalid rule {k}: expected finite 0–1')
                vals[k]=float(v)
        self._parent(kind,parent_id)
        if kind=='realm' and not (12<=x<=88 and 10<=y<=90):raise ValueError('realm must be within navigable Sea')
        if kind=='realm' and any((float(x)-p['x'])**2+(float(y)-p['y'])**2<64 for p in self.plants.values() if p['kind']=='realm' and p['status']=='stable'):
            raise ValueError('island too close to existing island')
        # A draft is information, not a created physical island/tree/flower.
        txn=self._pay_effort(actor,.08)
        ident=f'SEED-{len(self.blueprints)+1:05d}'
        b=SeedBlueprint(ident,actor,kind,name.strip(),parent_id,vals,self.sim.tick,x=float(x),y=float(y))
        self.blueprints[ident]=b
        self._event('seed_drafted',actor,b,txn,symbol=SEED_KINDS[kind]['symbol'],rules=deepcopy(vals))
        return b

    def research(self,actor,seed_id):
        b=self.blueprints[seed_id]
        self._need_actor(actor)
        if b.stage not in ('draft','researching'):raise ValueError('only unvalidated seeds can be researched')
        if self.sim.tick in b.research_ticks:raise ValueError('research requires a distinct cycle')
        if actor!=b.author and self.sim.founders.people[actor].location!=self.sim.founders.people[b.author].location:
            raise ValueError('researcher not at blueprint workspace')
        txn=self._pay_effort(actor,.18)
        b.stage='researching';b.research_ticks.add(self.sim.tick)
        self.sim.founders.learn(actor,'research',.006,f'blueprint:{b.id}:cycle:{self.sim.tick}')
        ev=self._event('seed_researched',actor,b,txn,research_cycles=len(b.research_ticks))
        b.evidence_ids.append(ev)
        return b

    def validate(self,actor,seed_id):
        b=self.blueprints[seed_id]
        self._need_actor(actor)
        if b.stage!='researching' or len(b.research_ticks)<2:raise ValueError('requires >=2 distinct research cycles')
        if actor==b.author:raise ValueError('independent peer review required')
        if self.sim.founders.people[actor].location!=self.sim.founders.people[b.author].location:
            raise ValueError('review requires colocated Founders')
        self._parent(b.kind,b.parent_id)
        # This is structural verification, NOT omniscient guarantee of physics.
        if b.rules['stability']<.15 or b.rules['recycling']<.10:
            raise ValueError('unstable or incomplete operating blueprint')
        if b.rules['biodiversity']>.82 and b.rules['moisture']<.22:
            raise ValueError('specified ecology exceeds water design assumptions')
        txn=self._pay_effort(actor,.11)
        b.reviewer=actor;b.stage='validated'
        b.validation_event=self._event('seed_validated',actor,b,txn,author=b.author)
        return b

    def plant(self,actor,seed_id):
        b=self.blueprints[seed_id]
        self._need_actor(actor)
        if b.stage!='validated':raise ValueError('validated blueprint must exist before planting')
        if actor!=b.author:raise ValueError('only author may plant seed in pilot')
        self._parent(b.kind,b.parent_id)
        if b.kind=='realm' and any((b.x-p['x'])**2+(b.y-p['y'])**2<64 for p in self.plants.values() if p['kind']=='realm' and p['status']=='stable'):
            raise ValueError('island planting site occupied by a realm')
        recipe=SEED_KINDS[b.kind]
        book=self.sim.book
        if b.kind=='world':
            WorldTree.preflight(book)
            if getattr(self.sim, 'founder_tree_independence_enabled', False):
                # A planning/review decision is free to fail; a physical World
                # requires an identified, previously harvested Creation fruit.
                if f'seed:fund:{b.id}' not in book.operations:
                    raise ValueError('World Tree needs a funded Creation fruit seed')
                if (book.mass.get(f'world_seed:{b.id}', 0.) < .10-1e-8 or
                        book.energy.get(f'ce:seed:{b.id}', 0.) < 1.-1e-8):
                    raise ValueError('funded fruit material/CE already spent')
        if b.kind=='species':
            tree=self.sim.world_trees.worlds.get(b.parent_id)
            if tree is None or tree.species_seed_ids or tree.state=='archived':
                raise ValueError('Species Seed requires an unpopulated active World Tree')
            tree.preflight_species()
        f_acct=f'founder:{actor}'
        mat='soil:Solara:grassland'
        reserve=recipe['initial_reserve']*(.75+.5*b.rules['stability'])
        binding=recipe['binding']
        # Prevalidate all balances before moving work energy: no partial planting.
        if book.energy[f_acct]<1.0000001:raise ValueError('not enough Founder work energy')
        if book.mass[mat]+1e-9<recipe['material']:raise ValueError('insufficient physical substrate')
        if book.energy['house']+1e-9<reserve+binding:raise ValueError('insufficient House reserve')
        cid=f'CRE-{len(self.plants)+1:05d}'
        work_acct=f'work:{actor}'
        txn=book.move(energy=[(f_acct,work_acct,1.)])
        cost=recipe['daily_energy']*(.8+.4*b.rules['openness'])
        # Substrate changes physical state. One toll from the Founder's funded work.
        construct=self.constructs.build(cid,'dimension' if b.kind in ('realm','world','dimension') else 'construct',
            b.parent_id or 'sea',mat,recipe['material'],cost,
            initial_reserve=reserve,binding_energy=binding,work_source=work_acct)
        b.stage='planted';b.planted_id=cid
        item={'id':cid,'kind':b.kind,'symbol':recipe['symbol'],'name':b.name,'blueprint_id':b.id,
              'parent':b.parent_id,'owner':b.author,'rules':deepcopy(b.rules),'x':b.x,'y':b.y,
              'status':'stable','created_tick':self.sim.tick,'mass':recipe['material'],
              'reserve':reserve,'upkeep':cost,'inhabitants':0}
        self.plants[cid]=item
        self.owner_reserve_knowledge[cid]={b.author:{'tick':self.sim.tick,'reserve':reserve}}
        if b.kind=='world':
            self.sim.world_trees.add(item,b)
            if getattr(self.sim, 'founder_tree_independence_enabled', False):
                # Named fruit biomass and finite CE are *bound* to this new
                # Tree, not duplicated in a second creation inventory.
                book.move(material=[(f'world_seed:{b.id}',f'world_seed:planted:{cid}',.10)],
                          energy=[(f'ce:seed:{b.id}',f'ce:world:{cid}',1.)],
                          operation_id=f'world:seed_germinated:{b.id}')
                self.sim.world_trees.worlds[cid].enable_provisioning()
        if b.kind=='species':self.sim.world_trees.worlds[b.parent_id].admit_species(item,b)
        self._event('seed_planted',actor,b,book.last,material=recipe['material'],
                    binding=round(binding,3),reserve=round(reserve,3),host_parent=b.parent_id)
        return item

    def tend(self,actor,creation_id,amount=.6):
        self._need_actor(actor)
        if creation_id not in self.plants:raise ValueError('unknown creation')
        c=self.plants[creation_id]
        if c['status']!='stable':raise ValueError('cannot maintain collapsed creation')
        if amount<=0 or not isfinite(float(amount)):raise ValueError('invalid amount')
        # Unlike the old scripted top-up, named Founder must actively fund upkeep.
        if self.sim.book.energy[f'founder:{actor}']<amount:raise ValueError('Founder lacks upkeep energy')
        self.constructs.top_up(creation_id,amount,source=f'founder:{actor}')
        self.owner_reserve_knowledge.setdefault(creation_id,{})[actor]={'tick':self.sim.tick,'reserve':self.sim.book.energy[f'reserve:{creation_id}']}
        self.sim.log('creation_tended',actor,txn=self.sim.book.last,creation=creation_id,amount=round(amount,5))
        return c

    def advance(self):
        # Running world age / maintenance after every integrated core-social cycle.
        for cid,c in list(self.plants.items()):
            before=c['status']
            parent=c['parent']
            if parent and self.plants[parent]['status']!='stable' and before=='stable':
                self.constructs.collapse(cid)
            else:
                self.constructs.tick(cid)
            state=self.constructs.items[cid]
            c['status']=state.status
            c['integrity']=round(state.integrity,5)
            c['reserve']=round(self.sim.book.energy[f'reserve:{cid}'],5)
            if state.status=='collapsed' and before!='collapsed':
                self.sim.world_trees.collapsed(cid,'parent_collapse' if parent and self.plants[parent]['status']!='stable' else 'unfunded_upkeep')
                self.sim.log('creation_collapsed',c['owner'],creation=cid,
                             cause=('parent_collapse' if parent and self.plants[parent]['status']!='stable' else 'unfunded_upkeep'),host_parent=parent)

    def export(self):
        return {'blueprints':[dict(asdict(b),research_ticks=sorted(b.research_ticks)) for b in self.blueprints.values()],
                'creations':list(self.plants.values())}

class IntegratedWorld(SocialSimulation):
    """One Book + one tick, with social choices and actual ecological consequences.

    The original v0.18 ecology runs first, social actions second, physical seed
    upkeep last. No fake material or direct belief->biomass update is permitted.
    The two v0.18 'founder' placeholders are inert: 100 FounderRegistry actors
    are the decision-making Founder population here.
    """
    def __init__(self,seed=400,capture=False,social_mode='full',days=400):
        self.ecology=EcologicalSimulation(seed=seed,days=days,trace=True)
        super().__init__(seed=seed,social_mode=social_mode,capture=capture,host_world=self.ecology)
        self.seeds=SeedRegistry(self)
        self.world_trees=WorldTreeRegistry(self)
        self.integrated_events=[]
        self.creation_limit=12  # trial workload cap, not fictional canon
        self.founder_harvest_enabled=False  # C004 experimental arm; C003 control unchanged
        self.founder_community_foraging_enabled=False  # C017 opt-in local food perception
        self.founder_tree_independence_enabled=False  # C017 opt-in independent fruit-funded World Trees
        self.founder_nutrition_enabled=False  # C015 opt-in ingestion/digestion; control unchanged
        # C016 opt-in: Book-funded food-to-work recovery, no legacy river recharge.
        self.founder_recovery_enabled=False
        # None: strict food-only under recovery, historical source otherwise.
        # Explicit 'legacy' or 'food_only' is for controlled causal ablations,
        # NOT a declaration that legacy charging is physically valid.
        self.founder_recharge_source_policy=None
        from founders_civ.core.founder_recovery import RecoveryState
        self.recovery_states={fid:RecoveryState() for fid in self.founders.people}
        self.recovery_receipts={}  # decision-id replay guard; no independent energy ledger
        for fid in self.ecology.founders.values():
            # Legacy model's two founders are metadata placeholders, not actors
            # participating alongside the authoritative set of 100.
            self.ecology.actors[fid].alive=False
        self.mapping=SITE_TO_PATCH.copy()

    def _legacy_recharge_allowed(self):
        mode=self.founder_recharge_source_policy
        if mode not in (None,'legacy','food_only'):
            raise ValueError('unrecognized Founder recharge source policy')
        return mode=='legacy' or (mode is None and not self.founder_recovery_enabled)

    def _pay(self,a,action,extra=0):
        if not self.founder_recovery_enabled:
            return super()._pay(a,action,extra)
        from founders_civ.experimental.social_agents import COST
        from founders_civ.core.founder_recovery import paid_work
        return paid_work(self,a,action,COST[action]+extra)

    def _next_kind_parent(self):
        plants=self.seeds.plants
        if not any(c['kind']=='realm' and c['status']=='stable' for c in plants.values()):return ('realm',None)
        active=[c for c in plants.values() if c['status']=='stable']
        realms=[c for c in active if c['kind']=='realm']
        worlds=[c for c in active if c['kind']=='world']
        unders=[c for c in active if c['kind']=='underworld']
        if len(worlds)<len(realms)*2:return ('world',realms[0]['id'])
        if worlds and len(unders)<len(worlds):return ('underworld',worlds[0]['id'])
        return ('realm',None)

    def _proposals(self,a,contacts):
        props=super()._proposals(a,contacts)
        founder=self.founders.people[a];state=self.states[a]
        if self.founder_recovery_enabled:
            from founders_civ.core.founder_recovery import propose_rest
            # Legacy rest spends fuel. C016 rest has a separate Book transition.
            props=[p for p in props if p[1]!='rest']
            props.extend(propose_rest(self,a))
        if not self._legacy_recharge_allowed():
            props=[p for p in props if p[1]!='recharge']
        # C015: physically owned food can be ingested without an arbitrary
        # decision-energy permission. Digestion itself requires funded work.
        from founders_civ.core.founder_nutrition import propose_nutrition
        from founders_civ.core.founder_harvesting import propose_harvest
        if self.founder_nutrition_enabled:
            props.extend(propose_nutrition(self,a))
        if self.founder_harvest_enabled:
            props.extend(propose_harvest(self,a))
        if self.founder_community_foraging_enabled:
            from founders_civ.core.community_foraging import propose_community_scan, prioritize_food
            props.extend(propose_community_scan(self,a))
            props=prioritize_food(self,a,props)
        if self.founder_tree_independence_enabled:
            from founders_civ.core.founder_tree_agency import propose_self_trees, prioritize_propagation
            own_tree_plan = propose_self_trees(self,a,contacts)
            # Prioritize an actual fruit acquisition, *then* a personal Tree.
            # A single productive Tree cannot finance everyone planning one.
            props=prioritize_propagation(self,a,props)
            props.extend(own_tree_plan)
        if self._energy(a)<.19:return props
        mine=[b for b in self.seeds.blueprints.values() if b.author==a and b.stage!='planted']
        agenda=state.main_goal
        if mine:
            b=mine[0]
            if b.stage in ('draft','researching') and self.tick not in b.research_ticks:
                if not (self.founder_tree_independence_enabled and b.kind=='world' and len(b.research_ticks)>=2):
                    props.append((2.15+.85*(agenda in ('research','mastery'))+.25*state.ambition,'seed_research',None,b.id))
            if b.stage=='validated' and self._energy(a)>=1.02:
                if not (self.founder_tree_independence_enabled and b.kind=='world' and
                        f'seed:fund:{b.id}' not in self.book.operations):
                    props.append((3.15+.5*state.ambition,'seed_plant',None,b.id))
            if b.stage=='researching' and len(b.research_ticks)>=2:
                reviewers=[q for q in contacts if q!=a]
                if reviewers:
                    props.append((2.65+.9*(agenda=='research'),'seed_request_review',reviewers[0],b.id))
        elif len(self.seeds.plants)<self.creation_limit and len(self.seeds.blueprints)<self.creation_limit+8:
            if agenda in ('research','exploration','leadership') and state.ambition>.56:
                kind,parent=self._next_kind_parent()
                if kind=='realm' or parent:
                    props.append((.10+.48*state.ambition+.18*(agenda=='research'),'seed_design',None,(kind,parent)))
        for cid,cr in self.seeds.plants.items():
            if cr['status']=='stable' and (cr['owner']==a or state.faction_id and state.faction_id==self.states[cr['owner']].faction_id):
                if self._energy(a)>.65 and self.book.energy[f'reserve:{cid}']<cr['upkeep']*3:
                    props.append((1.25+.35*(agenda=='solidarity'),'seed_tend',None,cid))
                    break
        if founder.location=='fields' and self._energy(a)>.7 and self.book.mass['soil:Solara:forest']>.1:
            props.append((.40+.5*(agenda=='solidarity'),'cultivate',None,None))
        # WORLD-023: decisions depend on each Founder's *last observation*,
        # not direct omniscient access to the actual world.
        # Replace the WORLD-022 omniscient reserve check with an actor's
        # own last-known creation reserve and predictable upkeep schedule.
        props=[p for p in props if p[1]!='seed_tend']
        for cid,plant in self.seeds.plants.items():
            if plant['status']!='stable' or plant['owner']!=a:continue
            intel=self.seeds.owner_reserve_knowledge.get(cid,{}).get(a)
            if intel is None:continue
            forecast=max(0.,intel['reserve']-(self.tick-intel['tick'])*plant['upkeep'])
            if forecast<plant['upkeep']*5.5 and self._energy(a)>.70:
                props.append((4.15+.25*state.caution,'creation_steward',None,cid))

        for cid,tree in self.world_trees.worlds.items():
            if tree.state!='active' or self.seeds.plants[cid]['status']!='stable':continue
            if tree.owner!=a:continue  # first slice: the creator is the responsible steward
            intel=tree.observations.get(a)
            if founder.location in ('house','riverbank') and self._energy(a)>.12:
                if intel is None or self.tick-intel['seen_tick']>=5:
                    urgency=.4 if intel and intel['population']<10 else 0.
                    props.append((2.2+urgency+.5*(agenda=='research')+.25*state.curiosity,
                                  'tree_observe',None,cid))
                if intel and self.tick-intel['seen_tick']<=6 and self.tick-tree.research.get(a,-100)>=6:
                    props.append((1.95+.9*(agenda=='research')+.2*state.ambition,
                                  'tree_research',None,cid))
            if intel is not None:
                plant=self.seeds.plants[cid]
                # Reserve is a cached *model estimate*, not perfect live knowledge.
                last=intel['seen_tick']; prior=intel.get('maintenance_reserve',plant['reserve'])
                estimate=max(0.,prior-(self.tick-last)*plant['upkeep'])
                if estimate < plant['upkeep']*5 and self._energy(a)>.68:
                    props.append((3.70+.4*(agenda in ('security','solidarity')),
                                  'tree_tend',None,cid))
        return props

    def _do(self,a,choice,contacts,rng,parent):
        self._current_parent=parent
        score,action,target,meta=choice
        if self.founder_recovery_enabled:
            if action=='rest':
                from founders_civ.core.founder_recovery import perform_rest
                return perform_rest(self,a,parent)
        if action=='recharge' and not self._legacy_recharge_allowed():
            return self.log('legacy_recharge_blocked',a,parent,
                            reason='Founder work cannot be minted from river/House energy')
        try:
            if action=='creation_steward':
                result=self.seeds.tend(a,meta,.67)
                self.log('creation_autonomous_stewardship',a,parent,creation=meta,amount=.67)
                return result
            if action=='tree_observe':
                tree=self.world_trees.worlds[meta]
                result=tree.observe(a)
                result['maintenance_reserve']=self.book.energy[f'reserve:{meta}']
                # This is only what the individual saw at the observatory.
                from founders_civ.core.founder_harvesting import observed_lots
                result['known_lots']=observed_lots(tree)
                return result
            if action=='seed_fund':
                from founders_civ.core.founder_tree_agency import fund_own_tree
                return fund_own_tree(self,a,meta)
            if action=='food_scan':
                from founders_civ.core.community_foraging import perform_community_scan
                return perform_community_scan(self,a,meta)
            if action=='tree_harvest':
                if not self.founder_harvest_enabled:
                    raise ValueError('Founder harvest policy disabled')
                from founders_civ.core.founder_harvesting import perform_harvest
                return perform_harvest(self,a,meta)
            if action in ('food_ingest','food_digest'):
                from founders_civ.core.founder_nutrition import perform_nutrition
                return perform_nutrition(self,a,action,meta)
            if action=='tree_research':return self.world_trees.worlds[meta].study(a)
            if action=='tree_tend':
                result=self.seeds.tend(a,meta,.65)
                # The actor updates their *estimate* after observing the top-up.
                intel=self.world_trees.worlds[meta].observations.get(a)
                if intel:intel['maintenance_reserve']=self.book.energy[f'reserve:{meta}'];intel['seen_tick']=self.tick
                self.log('tree_autonomous_maintenance',a,parent,creation=meta,amount=.65)
                return result
            if action=='seed_design':
                kind,pid=meta
                offset=len(self.seeds.blueprints)
                x=25+((offset*19+int(a[1:]))%50)
                y=25+((offset*11+int(a[1:]))%50)
                if kind=='realm':
                    for i in range(20):
                        trialx=16+((offset*17+i*19+int(a[1:]))%67)
                        trialy=13+((offset*23+i*13+int(a[1:]))%74)
                        if all((trialx-c['x'])**2+(trialy-c['y'])**2>=64 for c in self.seeds.plants.values() if c['kind']=='realm' and c['status']=='stable'):
                            x,y=trialx,trialy;break
                if pid:
                    par=self.seeds.plants[pid]
                    x=max(0.,min(100.,par['x']+rng.uniform(-5,5)))
                    y=max(0.,min(100.,par['y']+rng.uniform(-5,5)))
                self.seeds.draft(a,kind,f'{kind.title()} of {a}',pid,x=x,y=y)
                return None
            if action=='seed_research':return self.seeds.research(a,meta)
            if action=='seed_request_review':
                # Another Founder must genuinely spend attention/energy on review.
                # Self-interested approval is not permitted. Review is actor-specific.
                if not self._contact(a,target):raise ValueError('peer review unavailable')
                return self.seeds.validate(target,meta)
            if action=='seed_plant':return self.seeds.plant(a,meta)
            if action=='seed_tend':return self.seeds.tend(a,meta,.60)
            if action=='cultivate':
                # Actor's real effort creates biomass only by transforming funded
                # physical substrate with the existing universal toll.
                if self.book.energy[f'founder:{a}']<.20:raise ValueError('insufficient work')
                if self.book.mass['soil:Solara:forest']<.04:raise ValueError('no material')
                if self.book.mass['water:Solara:forest']<.10:raise ValueError('insufficient water available')
                if self.book.energy['sun:Solara:forest']<.05:raise ValueError('insufficient sunlight')
                src=f'work:{a}'
                self.book.move(energy=[(f'founder:{a}',src,.20)])
                self.book.transform([('soil:Solara:forest','plant:Solara:forest',.04)],
                  source=src,work=.20,energy_outputs=[(src,'environment:heat',.18)])
                return self.log('cultivate',a,parent,txn=self.book.last,material=.04,patch='Solara:forest')
        except (ValueError,KeyError) as exc:
            return self.log('world_action_rejected',a,parent,attempted=action,reason=str(exc))
        return super()._do(a,choice,contacts,rng,parent)

    def step(self):
        if self.tick>=self.ecology.days:raise ValueError('configured run horizon exceeded')
        self.ecology.step()      # existing environmental engine
        self.world_trees.step()  # four-habitat environments inside planted World Trees
        result=super().step()    # 100 boundedly rational social Founders
        self.seeds.advance()     # physical construct upkeep/collapse
        if self.tick!=self.ecology.day:raise AssertionError('clock desynchronization')
        self.book.audit()
        return result

    def merged_events(self,limit=60):
        # Unified observable timeline preserving each subsystem's original IDs.
        # All physical causality is tied to one Book via transaction_id.
        social=[dict(e,origin='founder',cycle=e['tick']) for e in self.events[-limit:]]
        physical=[dict(e,origin='ecology',cycle=e['day']) for e in self.ecology.events[-limit:]]
        return sorted(social+physical,key=lambda e:(e['cycle'],0 if e['origin']=='ecology' else 1,str(e['event_id'])))[-limit:]

    def status(self,include_actors=True,history=60):
        out={'version':'WORLD-023A/B experimental','tick':self.tick,'seed':self.seed,
             'ecology':self.ecology._snapshot(),'social':self.summary(include_events=False),
             'creation_system':self.seeds.export(),'tree_worlds':self.world_trees.export(include_residents=True),'latest_events':self.events[-history:],
             'combined_events':self.merged_events(history),
             'physical_ledger':self.book.audit()}
        if include_actors:
            out['actors']=self.observation()['actors']
            for a in out['actors']:
                a['energy']=round(self.book.energy[f'founder:{a["id"]}'],5)
        return out
