"""Executable acceptance probes for the v2 candidate; not ecological validation."""
import os,sys,unittest,pickle
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'src'))
from core_physiology_v2 import UnifiedCoreV2,PhysiologyBridgeV2
from species_life_02115 import PROFILES

def make(seed=100001):return UnifiedCoreV2(seed=seed)
def subject(sim,species='burrow_rabbit'):
    return next(a for a in sim.bridge.actors.values() if a.alive and a.species==species)

def fingerprint(sim):
    b=sim.bridge
    return (sim.days,len(b.events),tuple(sorted(b.stats.items())),
        tuple(sorted((k,round(v,10)) for k,v in sim.host.book.energy.items() if abs(v)>1e-9)),
        tuple(sorted((k,round(v,10)) for k,v in sim.host.book.mass.items() if abs(v)>1e-9)),
        tuple(sorted((a.id,a.species,a.age,a.alive,a.generation,a.habitat,
          round(b._state(a).fatigue,8),round(b._state(a).readiness,8),
          round(b._state(a).starvation_debt,8)) for a in b.actors.values())))

class CoreV2Tests(unittest.TestCase):
    def test_T09_no_actor_owned_time_currency(self):
        sim=make()
        self.assertIsInstance(sim.bridge,PhysiologyBridgeV2)
        for actor in sim.bridge.actors.values():
            for name in ('time_budget','time_wallet','action_points','time_credits'):
                self.assertFalse(hasattr(actor,name))
        sim.step();self.assertEqual(sim.days,1)
        self.assertEqual(sim.host.sim.tick,sim.host.sim.ecology.day)

    def test_T16_delayed_assimilation_and_paired_lot(self):
        sim=make();b=sim.bridge;a=subject(sim)
        reserve=b.book.energy[b.physical.reserve(a)]
        short=b.book.energy[b._short(a)]
        gut_before=b.book.mass[b.physical.gut(a)]
        source=b.physical.plant(a)
        self.assertTrue(b._feed_stock(a,source,'plant'))
        self.assertAlmostEqual(b.book.energy[b.physical.reserve(a)],reserve)
        self.assertAlmostEqual(b.book.energy[b._short(a)],short)
        self.assertGreater(b.book.mass[b.physical.gut(a)],gut_before)
        self.assertGreater(b.book.energy[b._gut_energy(a)],0)
        b._digest(a)
        self.assertGreater(b.book.energy[b._short(a)],short)
        self.assertGreater(b.book.mass[b.physical.gut(a)],0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_T17_digestion_awake_and_asleep(self):
        sim=make();b=sim.bridge;a=subject(sim)
        self.assertTrue(b._feed_stock(a,b.physical.plant(a),'plant'))
        slept=pickle.loads(pickle.dumps(sim));awake=pickle.loads(pickle.dumps(sim))
        sb=slept.bridge;ab=awake.bridge
        sa=subject(slept);aa=subject(awake)
        sb._state(sa).last_behavior='sleep';ab._state(aa).last_behavior='search'
        sb._digest(sa);ab._digest(aa)
        self.assertAlmostEqual(sb.book.energy[sb._short(sa)],ab.book.energy[ab._short(aa)],places=11)
        self.assertAlmostEqual(sb.book.mass[sb.physical.gut(sa)],ab.book.mass[ab.physical.gut(aa)],places=11)

    def test_T18_recovery_without_energy_mint(self):
        sim=make();b=sim.bridge;a=subject(sim);s=b._state(a)
        s.fatigue=.84;s.readiness=.25;a.condition=1.
        before=sum(b.book.energy.values());stock=b._fuel(a)
        b._finish_behavior(a,'sleep')
        self.assertLess(s.fatigue,.84)
        self.assertGreater(s.readiness,.25)
        self.assertAlmostEqual(sum(b.book.energy.values()),before,places=8)
        self.assertAlmostEqual(b._fuel(a),stock,places=11)

    def test_T19_equal_reserves_different_performance(self):
        u=make();v=pickle.loads(pickle.dumps(u))
        a=subject(u);b=subject(v)
        x=u.bridge._state(a);y=v.bridge._state(b)
        x.fatigue=0.;x.readiness=1.;x.experience=1.
        y.fatigue=.85;y.readiness=.30;y.experience=0.
        self.assertAlmostEqual(u.bridge._fuel(a),v.bridge._fuel(b))
        self.assertTrue(u.bridge._work(a,'test_travel',effort=.8))
        self.assertTrue(v.bridge._work(b,'test_travel',effort=.8))
        e1=u.bridge.physiology_metrics['resolved_work_energy']
        e2=v.bridge.physiology_metrics['resolved_work_energy']
        self.assertGreater(e2,e1)

    def test_T20_intention_without_flat_action_tax(self):
        sim=make();b=sim.bridge;a=subject(sim)
        before=dict(b.book.energy)
        b._choose(a)
        self.assertEqual(dict(b.book.energy),before)
        self.assertTrue(b._work(a,'actual_travel',effort=.6))
        self.assertGreater(b.physiology_metrics['resolved_work_energy'],0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_T21_digestion_and_movement_can_overlap(self):
        sim=make();b=sim.bridge;a=subject(sim)
        self.assertTrue(b._feed_stock(a,b.physical.plant(a),'plant'))
        old=b.book.mass[b.physical.gut(a)]
        self.assertTrue(b._work(a,'actual_travel',effort=.5))
        b._digest(a)
        self.assertLess(b.book.mass[b.physical.gut(a)],old)
        self.assertGreater(b.physiology_metrics['resolved_work_energy'],0)
        self.assertGreater(b.physiology_metrics['digested_mass'],0)

    def test_T22_progressive_not_instant_starvation(self):
        sim=make();b=sim.bridge;a=subject(sim)
        for key in (b._short(a),b.physical.reserve(a)):
            e=b.book.energy[key]
            if e:b.book.move(energy=[(key,'environment:heat',e)])
        b._metabolize(a)
        self.assertTrue(a.alive)
        self.assertGreater(b._state(a).starvation_debt,0)
        self.assertGreater(a.condition,0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_T23_checkpoint_replay(self):
        original=make()
        for _ in range(4):original.step()
        replay=pickle.loads(pickle.dumps(original))
        for _ in range(4):original.step();replay.step()
        self.assertEqual(fingerprint(original),fingerprint(replay))
        self.assertEqual(original.host.book.audit()['rejections'],0)

    def test_single_book_founders_and_ecological_schedulers(self):
        sim=make()
        self.assertIs(sim.host.book,sim.bridge.book)
        self.assertIs(sim.host.book,sim.bridge.tree.book)
        self.assertEqual(len(sim.host.sim.founders.people),100) # preserve 100 Founders
        self.assertEqual(sim.bridge.census()['distinct_biological_schedulers'],2)

    def test_all_13_species_share_v2(self):
        sim=make()
        self.assertEqual(len({x.species for x in sim.bridge.actors.values()}),13)
        for a in sim.bridge.actors.values():
            self.assertIn(a.species,PROFILES)
            self.assertTrue(hasattr(sim.bridge._state(a),'fatigue'))
            self.assertGreaterEqual(sim.bridge._maintenance_demand(a),0)

    def test_finite_resource_pressure_and_book(self):
        sim=make();b=sim.bridge;a=subject(sim)
        stock=b.book.mass[b.physical.plant(a)]
        self.assertTrue(b._feed_stock(a,b.physical.plant(a),'plant'))
        self.assertLess(b.book.mass[b.physical.plant(a)],stock)
        for _ in range(5):sim.step()
        audit=sim.host.book.audit()
        self.assertEqual(audit['rejections'],0)
        self.assertLess(abs(audit['mass_error']),1e-5)
        self.assertLess(abs(audit['energy_error']),1e-5)

    def test_no_previous_action_exertion_tax(self):
        sim=make();b=sim.bridge;a=subject(sim)
        b.needs_last[a.id]='hunt'
        before=b.physiology_metrics['resolved_work_energy']
        b._metabolize(a)
        self.assertEqual(before,b.physiology_metrics['resolved_work_energy'])
        self.assertGreater(b.physiology_metrics['maintenance_energy'],0)

    def test_no_work_partial_debit_when_power_limited(self):
        sim=make();b=sim.bridge;a=subject(sim)
        for key in (b._short(a),b.physical.reserve(a)):
            e=b.book.energy[key]
            if e:b.book.move(energy=[(key,'environment:heat',e)])
        old=b.book.energy[b._short(a)]
        self.assertFalse(b._work(a,'expensive_travel',effort=100))
        self.assertEqual(old,b.book.energy[b._short(a)])

if __name__=='__main__':unittest.main()
