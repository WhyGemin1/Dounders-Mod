"""Stdlib-only first-integration validation; no full 720-day hypothesis test."""
from __future__ import annotations
import unittest
from copy import deepcopy
from ledger import Book
from engine import Simulation, SPECIES, PATCH_NAMES

class LedgerContract(unittest.TestCase):
    def setUp(self):
        self.b=Book()
        self.b.seed_mass('soil:area',15.)
        self.b.seed_mass('plant:area',0.)
        self.b.seed_mass('food:actor',0.)
        self.b.seed_energy('reserve:actor',30.)
        self.b.seed_energy('heat:area',0.)
        self.b.seed_energy('house',100.)
        self.b.seed_energy('world_toll',0.)
        for k in range(10):self.b.seed_energy(f'underworld:{k}',0.)
        self.b.freeze()

    def test_exactly_one_toll_for_state_change(self):
        tx=self.b.transform([('soil:area','plant:area',1.)],
            'reserve:actor',2.,[('reserve:actor','heat:area',1.8)])
        self.assertAlmostEqual(tx.toll,.2)
        self.assertEqual(self.b.toll_count,1)
        self.assertAlmostEqual(self.b.energy['house'],100.14)
        self.assertLess(abs(self.b.audit()['energy_error']),1e-8)

    def test_movements_and_ownership_have_no_toll(self):
        self.b.move(material=[('soil:area','soil:elsewhere',2.)])
        self.assertEqual(self.b.toll_count,0)
        self.assertEqual(self.b.mass['soil:elsewhere'],2.)
        self.assertEqual(self.b.audit()['mass_error'],0.)

    def test_bad_operations_roll_back_all_balances(self):
        m=dict(self.b.mass);e=dict(self.b.energy)
        with self.assertRaises(ValueError):
            self.b.move(material=[('soil:area','soil:elsewhere',1.),('soil:area','food:actor',100.)])
        self.assertEqual(dict(self.b.mass),m)
        self.assertEqual(dict(self.b.energy),e)
        with self.assertRaises(ValueError):
            self.b.apply('move',material=[('soil:area','plant:area',1.)],toll=.01)
        self.assertEqual(dict(self.b.mass),m)
        with self.assertRaises(ValueError):
            self.b.transform([('soil:area','soil:area',1.)], 'reserve:actor',1.,
                         [('reserve:actor','heat:area',.9)])
        self.assertEqual(dict(self.b.mass),m)

    def test_inflow_has_explicit_source_and_house_debit(self):
        self.b.wellspring(5.)
        self.b.move(energy=[('house','heat:area',3.)])
        self.assertAlmostEqual(self.b.energy['house'],102.)
        self.assertAlmostEqual(self.b.audit()['external_wellspring'],5.)

class IntegrationContract(unittest.TestCase):
    def test_286_individual_actor_profiles_and_ten_layers(self):
        s=Simulation(seed=8,days=2,arm='1111',trace=False)
        self.assertEqual(len(s.actors),286)
        self.assertTrue(all(f'underworld:{k}' in s.book.energy for k in range(10)))
        for sp in ('meadow_grazer','forest_browser','ridge_hound','shadow_stalker',
                   'carrion_bird','ground_scavenger','soil_fungus'):
            self.assertTrue(any(a.species==sp for a in s.actors.values()))
        self.assertEqual(len({a.id for a in s.actors.values()}),286)

    def test_matched_initial_physics_weather_traits(self):
        a=Simulation(seed=43,days=30,arm='0000',trace=False)
        b=Simulation(seed=43,days=30,arm='1111',trace=False)
        self.assertEqual(dict(a.book.mass),dict(b.book.mass))
        self.assertEqual(dict(a.book.energy),dict(b.book.energy))
        self.assertEqual(a.weather,b.weather)
        self.assertEqual([(x.id,x.needs,x.traits,x.skills) for x in a.actors.values()],
                         [(x.id,x.needs,x.traits,x.skills) for x in b.actors.values()])
        self.assertGreater(sum(map(len,b.edges.values())),sum(map(len,a.edges.values())))

    def test_death_transforms_body_when_usable_reserves_are_exhausted(self):
        s=Simulation(seed=8,days=2,arm='1111',trace=True);s.day=1
        a=s.actors['Solara:meadow_grazer:001']
        old=s.book.mass[f'body:{a.id}']
        reserve=f'reserve:{a.id}';en=s.book.energy[reserve]
        s.book.move(energy=[(reserve,f'heat:{a.world}',en)])
        before=s.book.toll_count
        s._die(a,'starvation')
        self.assertFalse(a.alive)
        self.assertAlmostEqual(s.book.mass[f'body:{a.id}'],0.)
        self.assertGreaterEqual(s.book.mass[f'carcass:{a.patch}'],old)
        self.assertEqual(s.book.toll_count,before+1)
        self.assertLess(abs(s.book.audit()['energy_error']),1e-6)

    def test_migration_changes_location_without_state_toll(self):
        s=Simulation(seed=8,days=2,arm='0000',trace=True);s.day=1
        a=s.actors['Solara:meadow_grazer:001']
        old=a.patch;index=__import__('collections').defaultdict(list)
        for x in s.actors.values():
            if x.alive:index[x.patch].append(x)
        before=s.book.toll_count
        self.assertTrue(s._migrate(a,index))
        self.assertNotEqual(old,a.patch)
        self.assertEqual(before,s.book.toll_count)
        self.assertEqual(s.book.audit()['mass_error'],0.)

    def test_memory_cannot_grant_ability_without_practice(self):
        s=Simulation(seed=4,days=2,arm='1111',trace=True)
        a=s.actors['Solara:S1:C00']
        initial=a.skills['build']
        e=s._record('test_observe',actor=a)
        s._experience(a,'build',e,practice=False)
        self.assertEqual(initial,a.skills['build'])
        self.assertNotIn('build_node',a.nodes)
        for _ in range(4):
            e=s._record('test_practice',actor=a)
            s._experience(a,'build',e,practice=True)
        self.assertGreater(a.skills['build'],initial)
        if a.skills['build']>=.25:self.assertIn('build_node',a.nodes)

    def test_group_has_real_commitments_and_funded_stock(self):
        s=Simulation(seed=42,days=2,arm='1111',trace=True)
        s.day=1
        members=[s.actors[f'Solara:S1:C{i:02d}'] for i in range(3)]
        self.assertEqual(len(s.institutions),0)
        self.assertTrue(s._pledge(members[0]))
        self.assertEqual(len(s.institutions),0)
        self.assertFalse(s._pledge(members[0]))
        self.assertTrue(s._pledge(members[1]))
        self.assertEqual(len(s.institutions),0)
        self.assertTrue(s._pledge(members[2]))
        self.assertEqual(len(s.institutions),1)
        inst=s.institutions['Solara:S1']
        self.assertEqual(len(inst.members),3)
        self.assertAlmostEqual(s.book.mass[inst.pooled_account],.135)
        self.assertEqual(s.book.toll_count,0)
        self.assertLess(abs(s.book.audit()['mass_error']),1e-8)

    def test_institution_monitoring_requires_I_and_evidence(self):
        s=Simulation(seed=42,days=2,arm='0001',trace=True);s.day=1
        members=[s.actors[f'Solara:S1:C{i:02d}'] for i in range(3)]
        for a in members:s._pledge(a)
        inst=s.institutions['Solara:S1']
        q=s.book.mass[inst.pooled_account]-.02
        chem=f'foodchem:Solara:S1:pool';en=s.book.energy[chem]*q/s.book.mass[inst.pooled_account]
        s.book.move(material=[(inst.pooled_account,f'food:{members[0].id}',q)],
             energy=[(chem,f'foodchem:{members[0].id}',en)])
        for a in members:a.traits['caution']=.8
        for _ in range(3):s._institution_monitor(members[0])
        self.assertGreaterEqual(inst.monitoring_events,3)
        self.assertEqual(inst.revised,1)
        self.assertTrue(any(e['action']=='rule_revision' for e in s.events))
        c=Simulation(seed=42,days=2,arm='0000',trace=False);c.day=1
        for i in range(3):c._pledge(c.actors[f'Solara:S1:C{i:02d}'])
        self.assertFalse(c._institution_monitor(c.actors['Solara:S1:C00']))

    def test_ritual_and_social_learning_cannot_change_physical_stocks_directly(self):
        s=Simulation(seed=42,days=2,arm='1111',trace=True);s.day=1
        a=s.actors['Solara:S1:C00'];m=dict(s.book.mass);e=dict(s.book.energy)
        ev=s._record('ritual',a,belief='ritual_makes_rain')
        s._experience(a,'symbolic_practice',ev,True,False)
        self.assertEqual(dict(s.book.mass),m)
        self.assertEqual(dict(s.book.energy),e)
        self.assertNotIn('symbolic_practice_node',a.nodes)

    def test_source_tagged_teaching_is_relationship_based(self):
        s=Simulation(seed=42,days=30,arm='1111',trace=True);s.run()
        taught=[e for e in s.events if e['action']=='teach']
        self.assertTrue(taught)
        for event in taught:
            recipient=s.actors[event['recipient']]
            self.assertIn((event['event_id'],event['source_id'],event['claim']),recipient.source_memory)
            self.assertTrue(any(edge.source==event['actor'] for edge in s.edges[recipient.id]))
        self.assertGreater(s.counter['shared_norm_formed'],0)

    def test_short_smoke_audits_and_determinism(self):
        for arm in ('0000','1111','0101','1010'):
            a=Simulation(seed=42,days=3,arm=arm,trace=False).run()
            b=Simulation(seed=42,days=3,arm=arm,trace=False).run()
            self.assertEqual(a,b)
            self.assertLess(abs(a['physical_audit']['mass_error']),1e-7)
            self.assertLess(abs(a['physical_audit']['energy_error']),1e-6)
            self.assertEqual(a['creation_deaths'],0)
            self.assertGreater(a['harvest_events'],0)
            self.assertGreater(a['photosynthesis_events'],0)
            self.assertEqual(a['physical_audit']['rejections'],0)

    def test_decisions_reference_qualifying_experience_and_followup_actions(self):
        s=Simulation(seed=42,days=4,arm='1111',trace=True);s.run()
        decisions=[e for e in s.events if e['action']=='decision']
        self.assertTrue(decisions)
        by_id={e['event_id']:e for e in s.events}
        linked=[e for e in s.events if e['parent_event_ids']]
        self.assertTrue(linked)
        self.assertTrue(all(by_id[pid]['action']=='decision' for e in linked for pid in e['parent_event_ids']))
        self.assertTrue(any(e['recent_memory_ids'] for e in decisions if e['day']>1))
        self.assertTrue(any(e['action']=='harvest' and e['parent_event_ids'] for e in linked))

    def test_integrated_physics_and_social_behavior_30days(self):
        low=Simulation(seed=42,days=30,arm='0000',trace=False).run()
        full=Simulation(seed=42,days=30,arm='1111',trace=False).run()
        self.assertGreater(full['pledges'],low['pledges'])
        self.assertEqual(low['institution_monitoring'],0)
        self.assertGreater(full['institution_monitoring'],0)
        self.assertGreater(full['claim_exposures'],0)
        self.assertGreater(full['shared_norms'],0)
        self.assertGreater(full['nodes'],0)
        self.assertGreater(full['hunting_attempts'],0)
        self.assertGreater(full['water_collection_events'],0)
        self.assertLess(abs(full['physical_audit']['mass_error']),1e-7)
        self.assertLess(abs(full['physical_audit']['energy_error']),1e-6)

if __name__=='__main__':unittest.main()
