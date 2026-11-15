"""C006: ingestion uses owned Book assets, not magic energy or time tokens."""
import unittest, pickle
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest, propose_ingestion, perform_ingestion

class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.sim,_,self.tid=bootstrap(seed=821)
        self.tree=self.sim.world_trees.worlds[self.tid]
        self.tree.enable_provisioning()
        for _ in range(17):self.sim.step()
        self.sim.founder_harvest_enabled=True
        self.f='F001'
        self.sim.founders.people[self.f].location='riverbank'
        self.tree.observe(self.f)
        self.tree.observations[self.f]['known_lots']=observed_lots(self.tree)
        self.lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='food')
    def harvest(self):
        perform_harvest(self.sim,self.f,(self.tid,self.lot,'food'))
    def test_cannot_ingest_unowned_food(self):
        self.assertEqual(propose_ingestion(self.sim,self.f),[])
        seq=self.sim.book.seq
        with self.assertRaises(ValueError):perform_ingestion(self.sim,self.f,(self.tid,self.lot))
        self.assertEqual(self.sim.book.seq,seq)
    def test_ingestion_conserves_and_does_not_recharge(self):
        self.harvest()
        book=self.sim.book
        actor_before=book.energy[f'founder:{self.f}']
        old_mass=book.mass[f'gut:founder:{self.f}']
        old_energy=book.energy[f'gut_energy:founder:{self.f}']
        self.assertTrue(any(p[1]=='tree_ingest' for p in propose_ingestion(self.sim,self.f)))
        perform_ingestion(self.sim,self.f,(self.tid,self.lot))
        self.assertAlmostEqual(book.mass[f'gut:founder:{self.f}']-old_mass,.08)
        self.assertAlmostEqual(book.energy[f'gut_energy:founder:{self.f}']-old_energy,.02)
        self.assertEqual(book.energy[f'founder:{self.f}'],actor_before)
        self.assertAlmostEqual(book.audit()['mass_error'],0,places=5)
        self.assertAlmostEqual(book.audit()['energy_error'],0,places=4)
        self.assertEqual(propose_ingestion(self.sim,self.f),[])
        seq=book.seq
        perform_ingestion(self.sim,self.f,(self.tid,self.lot))
        self.assertEqual(book.seq,seq)
    def test_low_energy_does_not_block_ingestion(self):
        self.harvest()
        self.sim.book.energy[f'founder:{self.f}']=.01
        choices=self.sim._proposals(self.f,[])
        self.assertTrue(any(p[1]=='tree_ingest' for p in choices))
    def test_checkpoint_replay(self):
        self.harvest()
        frozen=pickle.loads(pickle.dumps(self.sim))
        perform_ingestion(self.sim,self.f,(self.tid,self.lot))
        perform_ingestion(frozen,self.f,(self.tid,self.lot))
        self.assertEqual(dict(self.sim.book.mass),dict(frozen.book.mass))
        self.assertEqual(dict(self.sim.book.energy),dict(frozen.book.energy))
        self.assertEqual(self.sim.book.seq,frozen.book.seq)
    def test_disabled_policy_rejects_ingestion(self):
        self.harvest();self.sim.founder_harvest_enabled=False
        self.assertEqual(propose_ingestion(self.sim,self.f),[])
        with self.assertRaisesRegex(ValueError,'disabled'):perform_ingestion(self.sim,self.f,(self.tid,self.lot))

if __name__=='__main__':unittest.main()
