"""Opt-in reproducible microcell map for the five-guild bridge.

Cells are coordinates within the existing four WORLD-023 habitats, NOT new
physical habitats or Book accounts. Ecological interactions remain habitat-wide
until a separately validated spatial-encounter branch is implemented.
"""
from collections import Counter
from family_pair_02136 import HabitatBridge239
from unified_02136 import Unified239
from habitat_bridge import SPECIES

class SpatialBridge240(HabitatBridge239):
    def __init__(self, tree, seed=9711, counts=None, *, grid_size=6, **kwargs):
        if type(grid_size) is not int or not 2 <= grid_size <= 64:
            raise ValueError('grid_size must be an integer from 2 to 64')
        self.grid_size=grid_size
        self.seed=seed
        self.positions={}
        super().__init__(tree,seed,counts,**kwargs)
        self.sync_positions()

    def sync_positions(self):
        """Stable deterministic positions; children inherit mother's microcell."""
        for actor in self.actors.values():
            if actor.id in self.positions:continue
            parent=self.actors.get(actor.parent) if actor.parent else None
            if parent and parent.id in self.positions and parent.habitat==actor.habitat:
                xy=self.positions[parent.id][1:]
            else:
                # Avoid consuming the engine's biological RNG stream.
                n=int(actor.id.rsplit('-',1)[-1]); z=self.grid_size
                xy=((n*17+int(self.seed)*3)%z,(n*31+int(self.seed)*7+n//z)%z)
            self.positions[actor.id]=(actor.habitat,*xy)
        for actor in self.actors.values():
            old=self.positions[actor.id]
            if old[0]!=actor.habitat:
                self.positions[actor.id]=(actor.habitat,old[1],old[2])
        return self.positions

    def _birth(self,mother):
        result=super()._birth(mother)
        self.sync_positions()
        return result

    def step(self,tick):
        result=super().step(tick)
        self.sync_positions()
        return result

    def spatial_census(self):
        self.sync_positions()
        cells=Counter(self.positions[a.id] for a in self.actors.values() if a.alive)
        generations=Counter((a.species,a.generation) for a in self.actors.values() if a.alive)
        return {'grid_size':self.grid_size,'occupied_cells':len(cells),
                'living':sum(cells.values()),'cells':{str(k):v for k,v in sorted(cells.items())},
                'living_generations':{f'{s}:G{g}':n for (s,g),n in sorted(generations.items())},
                'second_generation_reproduced':any(e.get('event')=='birth' and
                    self.actors.get(e.get('mother')) and self.actors[e['mother']].generation>=1
                    for e in self.events)}

class Unified240(Unified239):
    def __init__(self,seed=9711,governance='collective',counts=None,*,grid_size=6,
                 family_benefits=False,**kwargs):
        from living_tree_runner import LivingTreeRunner
        self.seed=seed; self.days=0; self.history=[]
        self.founding_families=True; self.family_benefits=bool(family_benefits)
        self.predator_energy_adaptation=True; self.digestion=True
        self.predator_scavenging=bool(kwargs.pop('predator_scavenging',True))
        self.mate_search=bool(kwargs.pop('mate_search',True))
        self.mouse_hysteresis=bool(kwargs.pop('mouse_hysteresis',False))
        self.initial_hound_dispersion=bool(kwargs.pop('initial_hound_dispersion',False))
        if kwargs:raise TypeError(f'unknown options: {sorted(kwargs)}')
        self.host=LivingTreeRunner(seed=seed,governance=governance)
        self.bridge=SpatialBridge240(self.host.sim.world_trees.worlds[self.host.tree_id],
            seed,counts,grid_size=grid_size,family_benefits=family_benefits,
            mate_search=self.mate_search,mouse_hysteresis=self.mouse_hysteresis,
            initial_hound_dispersion=self.initial_hound_dispersion,
            predator_scavenging=self.predator_scavenging)
        self._check()

    def report(self):
        r=super().report();r['spatial_map']=self.bridge.spatial_census();return r
