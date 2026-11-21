"""Focused tests for Founder-funded World Tree energy throughput."""
import os,sys,pickle,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'src'))
from core_physiology_v2 import UnifiedCoreV2
from founder_world_energy_141 import FounderWorldSupport141, WorldEnergyFunding141

class FounderWorldEnergy141Tests(unittest.TestCase):
    def create(self,**kw):return UnifiedCoreV2(seed=100001,founder_world_support=True,**kw)

    def test_creation_requires_real_founder_endowment(self):
        baseline=UnifiedCoreV2(seed=100001)
        funded=self.create()
        b=baseline.host.book;f=funded.host.book;tree=funded.bridge.tree
        founders=tuple(funded.host.sim.founders.people)
        reduction=sum(b.energy['founder:'+i]-f.energy['founder:'+i] for i in founders)
        gain=sum(f.energy[tree.acct('sun',h)]-b.energy[tree.acct('sun',h)] for h in tree.habitats)
        self.assertAlmostEqual(reduction,6.0,places=8)
        self.assertAlmostEqual(gain,reduction,places=8)
        self.assertEqual(funded.world_support.creation_txn,f.last.seq)
        self.assertEqual(f.audit()['rejections'],0)

    def test_no_power_issued_to_animal_from_donation(self):
        baseline=UnifiedCoreV2(seed=100001)
        sim=self.create()
        before=baseline.bridge
        after=sim.bridge
        for aid,a in before.actors.items():
            self.assertAlmostEqual(before._fuel(a),after._fuel(after.actors[aid]))

    def test_no_governance_fails_closed(self):
        with self.assertRaises(ValueError):
            self.create(governance='none')

    def test_maintains_only_on_low_production_flow(self):
        sim=self.create();support=sim.world_support;tree=sim.bridge.tree;b=sim.host.book
        # A well-fueled world requires no extra backing on this examination.
        for h in tree.habitats:
            for typ in ('sun','chem'):
                target=tree.acct(typ,h)
                if b.energy[target]<2.:
                    donor='house';amt=2.-b.energy[target]
                    b.move(energy=[(donor,target,amt)])
        self.assertEqual(support.maintain(),0.)
        # Force a deficit in one biome by moving its *real* chemical energy
        # and sunlight away to the central House account.
        support.last_funding_day=None
        h='forest'
        for typ in ('sun','chem'):
            key=tree.acct(typ,h);q=b.energy[key]
            if q>0:b.move(energy=[(key,'house',q)])
        prior=sum(b.energy[f'founder:{fid}'] for fid in sim.host.sim.founders.people)
        transferred=support.maintain()
        after=sum(b.energy[f'founder:{fid}'] for fid in sim.host.sim.founders.people)
        self.assertGreater(transferred,0.)
        self.assertAlmostEqual(prior-after,transferred,places=8)
        self.assertAlmostEqual(b.energy[tree.acct('sun',h)],transferred,places=8)
        self.assertEqual(b.audit()['rejections'],0)

    def test_no_overdraw_or_force_when_donors_depleted(self):
        sim=self.create();support=sim.world_support;b=sim.host.book
        p=support.policy
        for fid,_ in support._donors():
            account='founder:'+fid;bal=b.energy[account]
            if bal>p.founder_floor:
                b.move(energy=[(account,'house',bal-p.founder_floor)])
        amounts,short=support._allocate(.4,support._donors())
        self.assertFalse(amounts)
        self.assertAlmostEqual(short,.4,places=8)
        self.assertEqual(b.audit()['rejections'],0)

    def test_failed_commitment_does_not_mutate_book(self):
        sim=UnifiedCoreV2(seed=100001)
        provider=FounderWorldSupport141(sim,WorldEnergyFunding141(creation_endowment=10000.))
        original=sim.host.book.audit()['transactions']
        with self.assertRaises(ValueError):provider.activate()
        self.assertEqual(sim.host.book.audit()['transactions'],original)

    def test_deterministic_checkpoint_replay(self):
        sim=self.create()
        for i in range(3):sim.step()
        restored=pickle.loads(pickle.dumps(sim))
        for i in range(3):sim.step();restored.step()
        self.assertEqual(sim.world_support.events,restored.world_support.events)
        self.assertEqual(dict(sim.host.book.energy),dict(restored.host.book.energy))
        self.assertEqual(sim.bridge.physiology_report(),restored.bridge.physiology_report())
        self.assertEqual(sim.host.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
