"""WORLD-024 causal/mechanical tests: no artificial tree survival guarantee."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.experimental.world024 import CommonsWorld
from run_world024_stress import PROFILES


def make(seed=400, profile='commons'):
    sim,realm,tree=bootstrap(seed,simulator_class=lambda **kw:CommonsWorld(**kw,**PROFILES[profile]))
    sim.mark_shared(tree)
    return sim,realm,tree

class World024Tests(unittest.TestCase):
    def test_100_founders_50_pairs(self):
        sim,_,_=make()
        self.assertEqual(len(sim.founders.people),100)
        self.assertEqual(len({frozenset((a,f.partner_id)) for a,f in sim.founders.people.items()}),50)
    def test_shared_tree_has_four_habitats(self):
        sim,_,tid=make()
        self.assertEqual(len(sim.world_trees.worlds[tid].habitats),4)
        self.assertEqual(sim.world_trees.worlds[tid].population,16)
    def test_empty_council_and_unmaintained_policy(self):
        sim,_,_=make(profile='unmaintained')
        for _ in range(20):sim.step()
        self.assertEqual(len(sim.stewards),0)
        self.assertEqual(sum(sim.contributions.values()),0)
    def test_council_members_are_voluntary(self):
        sim,_,tid=make()
        for _ in range(30):sim.step()
        self.assertGreater(len(sim.stewards),0)
        self.assertTrue(all(a in sim.world_trees.worlds[tid].observations for a in sim.stewards))
    def test_owners_can_fail(self):
        sim,_,tid=make(profile='unmaintained')
        for _ in range(50):sim.step()
        self.assertEqual(sim.seeds.plants[tid]['status'],'collapsed')
    def test_food_harvest_and_consumption_conserved(self):
        sim,_,tid=make()
        a='F001'
        sim.founders.people[a].location='house'
        sim.world_trees.worlds[tid].observe(a)
        plant_before=sum(sim.book.mass[sim.world_trees.worlds[tid].acct('plant',p)] for p in sim.world_trees.worlds[tid].habitats)
        e_before=sim.book.energy[f'founder:{a}']
        res=sim._do(a,(2.,'tree_harvest',None,tid),[],None,'test-event')
        self.assertEqual(sim.events[-1]['action'],'tree_food_harvested')
        self.assertGreater(sim.book.mass[f'food:founder:{a}'],0)
        self.assertLess(sum(sim.book.mass[sim.world_trees.worlds[tid].acct('plant',p)] for p in sim.world_trees.worlds[tid].habitats),plant_before)
        res2=sim._do(a,(2.,'tree_eat',None,tid),[],None,'test-event')
        self.assertEqual(sim.events[-1]['action'],'tree_food_consumed')
        self.assertGreater(sim.book.energy[f'founder:{a}'],e_before)
        sim.book.audit()
    def test_rejects_unsupported_economic_mode(self):
        with self.assertRaises(ValueError):CommonsWorld(governance='immortal')
    def test_no_harvest_if_no_extraction(self):
        sim,_,_=make()
        sim.extraction='none'
        for _ in range(20):sim.step()
        self.assertEqual(sim.counter['tree_food_harvested'],0)
    def test_private_path_retains_seed_gate(self):
        sim,_,_=make(profile='private_option')
        for _ in range(45):sim.step()
        for c in sim.seeds.plants.values():
            if c['kind']=='world' and c['id']!=sim.shared_tree_id:
                bp=sim.seeds.blueprints[c['blueprint_id']]
                self.assertEqual(bp.stage,'planted')
                self.assertNotEqual(bp.author,bp.reviewer)
                self.assertGreaterEqual(len(bp.research_ticks),2)
        sim.book.audit()
    def test_stress_does_not_mint_energy(self):
        sim,_,_=make()
        before=sim.book.audit()
        sim.set_stress(upkeeps=2.0,rainfall=.2,founder_drain=.01,start=0,end=10)
        sim.step()
        after=sim.book.audit()
        self.assertGreater(after['external_wellspring'],before['external_wellspring'])
        self.assertLess(abs(after['mass_error']),1e-6)
        self.assertLess(abs(after['energy_error']),1e-5)
    def test_collapse_preserves_event_history(self):
        sim,_,tid=make(profile='unmaintained')
        for _ in range(50):sim.step()
        self.assertEqual(sim.world_trees.worlds[tid].state,'archived')
        self.assertGreater(len(sim.world_trees.worlds[tid].timeline),0)
        self.assertGreater(sim.world_trees.worlds[tid].counters['tree_death'],0)
    def test_world_trees_cannot_spawn_species_without_seed(self):
        sim,_,tid=make()
        self.assertEqual(len(sim.world_trees.worlds[tid].species_seed_ids),1)
        with self.assertRaises(ValueError):sim.world_trees.worlds[tid].admit_species({},None)
    def test_saturated_coordination_does_not_abort_long_runs(self):
        from random import Random
        sim,_,_=make()
        a='F001'; b=sim.founders.people[a].partner_id
        sim.founders.people[a].location='house'
        sim.founders.people[b].location='house'
        sim.founders.people[a].skills['coordination']=1.0
        sim.founders.people[b].skills['coordination']=1.0
        result=sim._do(a,(5.,'coordinate',b,None),[b],Random(1),'test-event')
        self.assertEqual(sim.events[-1]['action'],'coordinate')
        self.assertTrue(sim.events[-1]['success'])
        self.assertEqual(sim.founders.people[a].skills['coordination'],1.0)
        self.assertEqual(sim.founders.people[b].skills['coordination'],1.0)
        sim.book.audit()

    def test_deterministic_trajectory(self):
        a,_,tid=make(501)
        b,_,t2=make(501)
        for _ in range(12):a.step();b.step()
        self.assertEqual(a.summary_024()['shared_tree_population'],b.summary_024()['shared_tree_population'])
        self.assertEqual(a.book.audit()['transactions'],b.book.audit()['transactions'])
        self.assertEqual(a.summary_024()['enlisted'],b.summary_024()['enlisted'])

if __name__=='__main__':unittest.main()
