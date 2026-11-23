import importlib.util
from collections import defaultdict, namedtuple
Recorded=namedtuple("Recorded", "energy")
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('c013_living_assets',Path(__file__).resolve().parents[1] / 'founders_civ' / 'core' / 'living_assets.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Book:
    def __init__(self):
        self.mass=defaultdict(float);self.energy=defaultdict(float);self.operations={}
    def ingest(self,material,energy,operation_id):
        return self._commit(material,energy,operation_id)
    def transform(self,material,source,work,energy_outputs,operation_id):
        return self._commit(material,energy_outputs+[(source,'metabolic_toll',work*.1)],operation_id,work=(source,work))
    def _commit(self,material,energy,op,work=None):
        signature=(tuple(material),tuple(energy),work)
        if op in self.operations:
            if self.operations[op][0]!=signature:raise ValueError('replay drift')
            return op
        for src,dst,amount in material:
            if self.mass[src]+1e-9<amount:raise ValueError('mass underflow')
        for src,dst,amount in energy:
            if self.energy[src]+1e-9<amount:raise ValueError('energy underflow')
        if work and self.energy[work[0]]+1e-9<work[1]+sum(v for s,d,v in energy if s==work[0]):
            raise ValueError('work underflow')
        for src,dst,amount in material:self.mass[src]-=amount;self.mass[dst]+=amount
        for src,dst,amount in energy:self.energy[src]-=amount;self.energy[dst]+=amount
        if work:self.energy[work[0]]-=work[1]-sum(v for s,d,v in energy if s==work[0])
        self.operations[op]=(signature,Recorded(tuple(energy)))
        return op

class LotIsolation(unittest.TestCase):
    def setUp(self):
        self.book=Book()
        tree=type('Tree',(),{})();tree.sim=type('Sim',(),{})();tree.sim.book=self.book
        tree.sim.founders=type('Founders',(),{})();tree.sim.founders.people={'f':object()}
        self.ops=m.TreeResourceOps(tree)
        for lot in ['a','b']:
            self.book.mass[f'portable_food:lot:{lot}:founder:f']=.08
            self.book.energy[f'food_energy:lot:{lot}:founder:f']=.02
        self.book.energy['founder:f']=.005
    def test_distinct_lots_are_distinct_accounts(self):
        self.ops.eat_food('a','f');self.ops.eat_food('b','f')
        self.assertEqual(self.book.mass['gut:founder:f:lot:a'],.08)
        self.assertEqual(self.book.mass['gut:founder:f:lot:b'],.08)
        self.ops.digest_food('a','f')
        self.assertAlmostEqual(self.book.mass['gut:founder:f:lot:a'],0)
        self.assertAlmostEqual(self.book.mass['gut:founder:f:lot:b'],.08)
        self.assertAlmostEqual(self.book.energy['gut_energy:founder:f:lot:b'],.02)
    def test_replay_does_not_consume_second_lot(self):
        self.ops.eat_food('a','f');self.ops.eat_food('b','f')
        self.ops.digest_food('a','f')
        before=(dict(self.book.mass),dict(self.book.energy))
        self.ops.digest_food('a','f')
        self.assertEqual(before,(dict(self.book.mass),dict(self.book.energy)))
    def test_wrong_lot_cannot_spend_other_lot(self):
        self.ops.eat_food('a','f');self.ops.eat_food('b','f')
        self.book.mass['gut:founder:f:lot:a']=0
        with self.assertRaisesRegex(ValueError,'underflow'):
            self.ops.digest_food('a','f')
        self.assertAlmostEqual(self.book.mass['gut:founder:f:lot:b'],.08)

if __name__=='__main__':unittest.main()
