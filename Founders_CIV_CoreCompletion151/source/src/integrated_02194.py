"""Cycle094 experimental causal access audit; no scheduler/canonical mutation."""
from integrated_02193 import Unified293

class Unified294(Unified293):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.access_snapshots=[]

    def step(self):
        super().step()
        if self.days in (30,60,120,180):
            book=self.host.book
            tree=self.bridge.tree
            actors=list(self.bridge.actors.values())
            by_habitat={}
            for habitat in tree.habitats:
                residents=[a for a in actors if a.alive and getattr(a,'habitat',None)==habitat]
                by_habitat[habitat]={
                    'living':len(residents),
                    'juveniles':sum(getattr(a,'stage',None)=='juvenile' for a in residents),
                    'browse':float(book.mass.get(f'forage:browse:{habitat}',0)),
                    'seeds':float(book.mass.get(f'forage:seeds:{habitat}',0)),
                }
            self.access_snapshots.append({'day':self.days,'habitats':by_habitat,
                'living':sum(a.alive for a in actors),
                'g1_adults':sum(a.alive and a.generation==1 and a.stage=='adult' for a in actors),
                'g2_births':sum(a.generation>=2 for a in actors),
                'funded_events':sum(bool(e.get('funded')) for e in self.edible_events)})
