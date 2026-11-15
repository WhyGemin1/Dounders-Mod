"""WORLD-024 experimental extension: tree commons, harvestable resources,
voluntary stewardship and optional independently researched private World Trees.

This extension preserves the single v0.18 Book; no energy or matter is minted.
Coefficients and social behavior are exploratory, not empirically calibrated.
"""
from __future__ import annotations
from collections import Counter
from random import Random
from .world_integration import IntegratedWorld
from .social_agents import stable_seed

class CommonsWorld(IntegratedWorld):
    def __init__(self, seed=400, capture=False, social_mode='full', days=400,
                 governance='collective', extraction='careful', allow_private=False):
        if governance not in {'collective','owner','fragmented','none'}:
            raise ValueError('unknown governance')
        if extraction not in {'careful','intensive','none'}:
            raise ValueError('unknown extraction')
        super().__init__(seed=seed,capture=capture,social_mode=social_mode,days=days)
        self.governance=governance
        self.extraction=extraction
        self.allow_private=allow_private
        self.shared_tree_id=None
        self.stewards=set()
        self.contributions=Counter()
        self.harvest_mass=0.
        self.consumed_mass=0.
        self.food_energy=0.
        self.private_blueprints=set()
        self.temporary_shocks=[]
        self.disease_events=0

    def mark_shared(self,tree_id):
        if tree_id not in self.world_trees.worlds: raise ValueError('unknown shared tree')
        self.shared_tree_id=tree_id
        # Allow Founders to explore one or two additional private World Trees.
        self.creation_limit=9 if self.allow_private else 3

    def set_stress(self, upkeeps=1., rainfall=1., disease=0., founder_drain=0., start=0, end=None):
        """Scenario shock: modifies *demands* and hazard probabilities, never stocks."""
        if any(x<0 for x in (upkeeps,rainfall,disease,founder_drain)) or disease>1:
            raise ValueError('invalid stress')
        self.temporary_shocks.append(dict(start=start,end=end,upkeeps=upkeeps,
           rainfall=rainfall,disease=disease,founder_drain=founder_drain))

    def _eligible_volunteer(self,a,tree):
        s=self.states[a]
        if self.governance=='none':return False
        if self.governance=='owner':return a==tree.owner
        if a==tree.owner:return True
        if self.governance=='fragmented' and (
           not s.faction_id or s.faction_id != self.states[tree.owner].faction_id):return False
        # Volunteering depends on goals and the Founder's perceived trust.
        return (s.ambition>=.34 and (s.main_goal in ('solidarity','security','leadership','research')
               or s.empathy>.69) and self._trust(a,tree.owner)>.39)

    def _on_duty(self,a):
        order=sorted(self.stewards)
        # A three-person rotating watch provides redundancy without requiring
        # all volunteers to abandon their own work.
        return bool(order) and a in {order[(self.tick+j)%len(order)] for j in range(min(3,len(order)))}

    def _proposals(self,a,contacts):
        ps=super()._proposals(a,contacts)
        # Replace owner's WORLD-023 maintenance rule with one evidence-bound
        # stewardship policy, and leave unrelated base social actions intact.
        ps=[p for p in ps if p[1] not in ('creation_steward','tree_tend')]
        # WORLD-023 automatically designs unrelated underworlds; controlled
        # WORLD-024 tests keep one common tree unless private creation is enabled.
        ps=[p for p in ps if p[1]!='seed_design']
        s=self.states[a]; f=self.founders.people[a]
        if self.shared_tree_id is None:return ps
        tree=self.world_trees.worlds[self.shared_tree_id]
        if tree.state!='active' or self.seeds.plants[tree.id]['status']!='stable':return ps
        near=f.location in ('house','riverbank')
        e=self._energy(a)
        intel=tree.observations.get(a)
        age=(self.tick-intel['seen_tick']) if intel else 1000
        goal=s.main_goal
        # Every living Founder can independently observe the shared world, but
        # must expend an action and energy. No direct read of true plant stocks.
        if near and e>.14 and (intel is None or age>=8):
            motive=.6*(goal in ('research','security','solidarity','exploration'))+.35*s.curiosity
            ps.append((1.02+motive,'commons_observe',None,tree.id))
        if self.governance in ('collective','fragmented') and near and intel and a not in self.stewards:
            if self._eligible_volunteer(a,tree) and e>.22:
                ps.append((1.48+.35*(goal in ('solidarity','security','leadership')),
                           'commons_enlist',None,tree.id))
        eligible=self._eligible_volunteer(a,tree) if self.governance=='owner' else a in self.stewards
        if eligible and intel and age<=18 and e>.75 and self.governance!='none':
            # Explicit public duty roster; an assigned volunteer may skip upkeep
            # because of energy, competing goals, attention or stale evidence.
            duty = a==tree.owner if self.governance=='owner' else self._on_duty(a)
            if duty:
                for target_id in (self.shared_tree_id,tree.realm_id):
                    cr=self.seeds.plants[target_id]
                    if cr['status']!='stable':continue
                    prior = intel.get('realm_reserve',0.) if target_id==tree.realm_id else intel.get('maintenance_reserve',0.)
                    prior_tick = intel['seen_tick']
                    forecast=max(0.,prior-(self.tick-prior_tick)*cr['upkeep'])
                    if forecast<cr['upkeep']*7.5:
                        priority=2.9 + .4*(goal in ('security','solidarity')) + .25*s.caution
                        if forecast<cr['upkeep']*2:priority+=.6
                        ps.append((priority,'commons_tend',None,target_id))
        # Tree product access is physical and goal dependent, not an automatic
        # passive energy bonus from owning the World Tree.
        if self.extraction!='none':
            food=self.book.mass[f'food:founder:{a}']
            if food>=.035 and e<2.35:
                ps.append((3.15+.3*(goal=='security'),'tree_eat',None,tree.id))
            if near and intel and age<=9 and e>.11 and food<.16:
                if self.extraction=='intensive':
                    base=2.95
                else:
                    base=1.30 + (1.0 if e<.90 else 0.)
                ps.append((base+.35*(goal in ('security','mastery')),'tree_harvest',None,tree.id))
        # Voluntary independent world creation requires the same original seed
        # research, independent review, and funded planting requirements.
        if self.allow_private and near and e>.40:
            owned=[c for c in self.seeds.plants.values() if c['kind']=='world' and
                    c['owner']==a and c['id']!=self.shared_tree_id]
            private_seeds=[b for b in self.seeds.blueprints.values() if
                           b.kind=='world' and b.id in self.private_blueprints]
            if not owned and len(private_seeds)<2 and not any(b.author==a and b.kind=='world' for b in private_seeds):
                if s.ambition>.72 and goal in ('leadership','research','exploration'):
                    ps.append((1.35+.9*s.ambition,'private_seed',None,tree.realm_id))
            for cr in owned:
                w=self.world_trees.worlds.get(cr['id'])
                if w and not w.species_seed_ids and not any(b.kind=='species' and b.parent_id==w.id for b in self.seeds.blueprints.values()):
                    ps.append((2.20+.65*(goal=='research'),'private_species_seed',None,w.id))
        return ps

    def _do(self,a,choice,contacts,rng,parent):
        self._current_parent=parent
        _,act,target,meta=choice
        if act in ('commons_observe','commons_enlist','commons_tend','tree_harvest','tree_eat','private_seed','private_species_seed'):
            try:
                if act=='commons_observe':
                    tree=self.world_trees.worlds[meta]
                    result=tree.observe(a)
                    intel=tree.observations[a]
                    intel['maintenance_reserve']=self.book.energy[f'reserve:{tree.id}']
                    intel['realm_reserve']=self.book.energy[f'reserve:{tree.realm_id}']
                    self.log('commons_observed',a,parent,creation=tree.id)
                    return result
                if act=='commons_enlist':
                    tree=self.world_trees.worlds[meta]
                    if a in self.stewards or not self._eligible_volunteer(a,tree):raise ValueError('not eligible')
                    if a not in tree.observations:raise ValueError('must observe the tree')
                    txn=self.book.move(energy=[(f'founder:{a}','environment:heat',.025)])
                    self.stewards.add(a)
                    return self.log('commons_enlisted',a,parent,txn,creation=meta)
                if act=='commons_tend':
                    if self.governance=='none' or (self.governance=='owner' and a!=self.world_trees.worlds[self.shared_tree_id].owner):
                        raise ValueError('maintenance disabled')
                    if self.governance!='owner' and a not in self.stewards:
                        raise ValueError('must volunteer')
                    tree=self.world_trees.worlds[self.shared_tree_id]
                    if a not in tree.observations or self.tick-tree.observations[a]['seen_tick']>18:
                        raise ValueError('stale knowledge')
                    self.seeds.tend(a,meta,.65)
                    self.contributions[a]+=.65
                    intel=tree.observations[a]
                    key='realm_reserve' if meta==tree.realm_id else 'maintenance_reserve'
                    intel[key]=self.book.energy[f'reserve:{meta}']
                    intel['seen_tick']=self.tick
                    return self.log('commons_maintained',a,parent,creation=meta,amount=.65)
                if act=='tree_harvest':
                    tree=self.world_trees.worlds[meta]
                    if tree.state!='active':raise ValueError('not active')
                    if self.founders.people[a].location not in ('house','riverbank'):raise ValueError('must access tree gateway')
                    intel=tree.observations.get(a)
                    if intel is None or self.tick-intel['seen_tick']>9:raise ValueError('need recent observation')
                    # Keep minimum biomass as habitat refuge, but intensive
                    # collection permits a much smaller buffer.
                    floor=.8 if self.extraction=='careful' else .20
                    p=max(tree.habitats,key=lambda k:self.book.mass[tree.acct('plant',k)])
                    stock=self.book.mass[tree.acct('plant',p)]
                    q=min(.07 if self.extraction=='careful' else .14,max(0.,stock-floor))
                    if q<.025:raise ValueError('insufficient harvestable plant biomass')
                    source=f'founder:{a}'
                    if self._energy(a)<.03:raise ValueError('no harvesting work energy')
                    # Harvest converts plant biomass into a physically carried
                    # food inventory with a funded transformation toll.
                    txn=self.book.transform([(tree.acct('plant',p),f'food:founder:{a}',q)],
                         source=source,work=.018,
                         energy_outputs=[(source,'environment:heat',.0162)])
                    self.harvest_mass+=q
                    return self.log('tree_food_harvested',a,parent,txn,creation=meta,habitat=p,mass=q)
                if act=='tree_eat':
                    tree=self.world_trees.worlds[meta]
                    q=min(.07,self.book.mass[f'food:founder:{a}'])
                    if q<.035:raise ValueError('no carried food')
                    p='forest'
                    chem=tree.acct('chem',p)
                    available=self.book.energy[chem]
                    work=min(.048,available)
                    if work<.012:raise ValueError('tree food energy temporarily depleted')
                    # Metabolism transforms consumed food into physical detritus
                    # and transfers ONLY energy already present in habitat stock.
                    txn=self.book.transform([(f'food:founder:{a}',tree.acct('detritus',p),q)],
                         source=chem,work=work,
                         energy_outputs=[(chem,f'founder:{a}',work*.9)])
                    self.consumed_mass+=q
                    self.food_energy+=work*.9
                    return self.log('tree_food_consumed',a,parent,txn,creation=meta,energy=work*.9,mass=q)
                if act in ('private_seed','private_species_seed'):
                    kind='world' if act=='private_seed' else 'species'
                    world=self.world_trees.worlds[self.shared_tree_id]
                    x=max(0,min(100,self.seeds.plants[world.id]['x']+rng.uniform(-4,4)))
                    y=max(0,min(100,self.seeds.plants[world.id]['y']+rng.uniform(-4,4)))
                    seed=self.seeds.draft(a,kind,f'Independent {kind} by {a}',parent_id=meta,x=x,y=y)
                    if kind=='world':self.private_blueprints.add(seed.id)
                    return self.log('private_blueprint_drafted',a,parent,blueprint=seed.id,kind=kind)
            except (ValueError,KeyError) as exc:
                return self.log('world_action_rejected',a,parent,attempted=act,reason=str(exc))
        return super()._do(a,choice,contacts,rng,parent)

    def step(self):
        # Temporary environmental shocks increase physical costs and biological
        # risks, never injecting untracked stocks.
        modifiers={}
        for event in self.temporary_shocks:
            if self.tick>=event['start'] and (event['end'] is None or self.tick<event['end']):
                modifiers=event;break
        mult=modifiers.get('upkeeps',1.)
        rain=modifiers.get('rainfall',1.)
        disease=modifiers.get('disease',0.)
        for tree in self.world_trees.worlds.values():
            tree.precipitation_factor=rain
            tree.disease_risk=disease
        # Store intrinsic costs once, avoiding multiplicative inflation.
        for cid,construct in self.seeds.constructs.items.items():
            if not hasattr(construct,'nominal_upkeep'):
                construct.nominal_upkeep=construct.daily_energy
            construct.daily_energy=construct.nominal_upkeep*mult
            if cid in self.seeds.plants:
                self.seeds.plants[cid]['upkeep']=construct.daily_energy
        if modifiers.get('founder_drain',0)>0:
            q=modifiers['founder_drain']
            # A storm makes coordination/work more expensive. Every debited unit
            # moves to the heat reservoir, preserving energy accounting.
            legs=[]
            for a in self.founders.people:
                have=self.book.energy[f'founder:{a}']
                charge=min(have,q)
                if charge>0:legs.append((f'founder:{a}','environment:heat',charge))
            if legs:self.book.move(energy=legs)
        return super().step()

    def summary_024(self):
        shared=self.world_trees.worlds[self.shared_tree_id]
        return dict(seed=self.seed,ticks=self.tick,governance=self.governance,
           extraction=self.extraction,private_allowed=self.allow_private,
           founders=len(self.founders.people),enlisted=len(self.stewards),
           distinct_contributors=len(self.contributions),total_contributions=round(sum(self.contributions.values()),4),
           harvested_mass=round(self.harvest_mass,5),eaten_mass=round(self.consumed_mass,5),
           energy_from_tree=round(self.food_energy,5),
           shared_tree_state=shared.state,shared_tree_age=shared.age,
           shared_tree_population=shared.population,
           shared_tree_births=shared.counters['tree_birth'],
           shared_tree_deaths=shared.counters['tree_death'],
           shared_tree_diseases=shared.counters['tree_disease'],
           shared_tree_plants=shared.timeline[-1]['plants'],
           shared_realm_status=self.seeds.plants[shared.realm_id]['status'],
           shared_tree_status=self.seeds.plants[shared.id]['status'],
           private_worlds=sum(c['kind']=='world' and c['id']!=shared.id for c in self.seeds.plants.values()),
           private_worlds_active=sum(c['kind']=='world' and c['id']!=shared.id and c['status']=='stable' for c in self.seeds.plants.values()),
           private_worlds_with_species=sum(w.id!=shared.id and bool(w.species_seed_ids) for w in self.world_trees.worlds.values()),
           post_bootstrap_blueprints=len(self.seeds.blueprints)-3,
           house_energy=round(self.book.energy['house'],4),
           total_food_inventories=round(sum(v for k,v in self.book.mass.items() if k.startswith('food:founder:')),5),
           decisions=self.counter['decision'],events=len(self.events),
           conservation=self.book.audit())
