"""New SOCIAL-021 regression tests. Runs on synthetic experimental policies."""
import unittest
from copy import deepcopy
from founders_civ.experimental.social_agents import SocialSimulation

class SocialArchitectureTests(unittest.TestCase):
    def test_100_founders_and_original_partners(self):
        s=SocialSimulation(seed=404)
        self.assertTrue(s.founders.integrity())
        self.assertEqual(len(s.states),100)
        self.assertEqual(len([x for x in s.states.values() if x.officer]),4)
        for i in range(1,9):
            self.assertEqual(sum(x.historical_squad==f'SQ{i:02}' for x in s.states.values()),12)
        self.assertEqual(sum(s.founders.people[a].partner_id==b for a in s.states for b in s.states),100)

    def test_role_never_blocks_training_other_skill(self):
        s=SocialSimulation(409)
        a='F001'
        old=s.founders.people[a].skills['navigation']
        s.founders.learn(a,'navigation',.2,'simulated_training')
        self.assertGreater(s.founders.people[a].skills['navigation'],old)

    def test_social_decisions_are_event_traced_and_funded(self):
        s=SocialSimulation(400)
        summary=s.run(12)
        self.assertEqual(summary['actions']['decision'],1200)
        self.assertLess(abs(summary['energy_mass_audit']['mass_error']),1e-7)
        self.assertLess(abs(summary['energy_mass_audit']['energy_error']),1e-7)
        self.assertTrue(any(e.get('parent_event_id') for e in s.events if e['action']!='decision'))
        self.assertTrue(any(e['action']=='coordinate' for e in s.events))
        self.assertTrue(all(t['transaction_id'] is not None for t in s.events if t['action'] in ('study','aid','practice')))

    def test_reproducible_by_seed(self):
        a=SocialSimulation(410)
        b=SocialSimulation(410)
        self.assertEqual(a.run(8),b.run(8))
        self.assertEqual(a.events,b.events)

    def test_different_seeds_vary(self):
        a=SocialSimulation(410);b=SocialSimulation(411)
        self.assertNotEqual(a.run(8)['actions'],b.run(8)['actions'])

    def test_teaching_requires_contact_and_does_not_grant_proficiency(self):
        s=SocialSimulation(402)
        a='F001';b='F002'
        sa=s.states[a];sb=s.states[b]
        sa.cognition.claim('house_history').understanding=.4
        f_b=s.founders.people[b]
        old=deepcopy(f_b.skills)
        s.tick=1
        s._do(a,(1,'teach',b,'house_history'),[b],s.rng,'manual-decision')
        self.assertGreater(sb.cognition.claim('house_history').exposures,0)
        self.assertEqual(f_b.skills,old)
        f_b.location='ridge'
        old_exposures=sb.cognition.claim('house_history').exposures
        s._do(a,(1,'teach',b,'house_history'),[],s.rng,'manual-decision')
        self.assertEqual(sb.cognition.claim('house_history').exposures,old_exposures)
        s.book.audit()

    def test_trust_is_directional_and_evidence_typed(self):
        s=SocialSimulation(403)
        a='F001';b='F002'
        before=s.states[a].cognition.partner(b).expectation('benevolence')
        s.tick=1
        s._do(b,(1,'aid',a,None),[a],s.rng,'manual-decision')
        self.assertGreater(s.states[a].cognition.partner(b).expectation('benevolence'),before)
        self.assertEqual(s.states[b].cognition.partner(a).expectation('benevolence'),.5)
        self.assertEqual(s.states[a].cognition.partner(b).expectation('integrity'),.5)
        s.book.audit()

    def test_promise_affects_integrity_on_expiry_and_on_fulfillment(self):
        s=SocialSimulation(403)
        s.tick=1
        s._do('F002',(1,'promise','F001',None),['F001'],s.rng,'manual-decision')
        self.assertEqual(len(s.promises),1)
        self.assertEqual(s.states['F001'].cognition.partner('F002').expectation('integrity'),.5)
        s._do('F002',(1,'aid','F001',None),['F001'],s.rng,'manual-decision')
        self.assertEqual(next(iter(s.promises.values())).status,'fulfilled')
        self.assertGreater(s.states['F001'].cognition.partner('F002').expectation('integrity'),.5)
        s._do('F003',(1,'promise','F004',None),['F004'],s.rng,'manual-decision')
        s.tick=5
        s.step() # expiry before next decision
        self.assertLess(s.states['F004'].cognition.partner('F003').expectation('integrity'),.5)
        s.book.audit()

    def test_factions_require_three_real_decisions(self):
        s=SocialSimulation(400)
        leader='F005';member_a='F011';member_b='F017'
        for a in (leader,member_a,member_b):
            s.states[a].main_goal='leadership'
        s.tick=5
        s._do(leader,(1,'organize',member_a,None),[member_a],s.rng,'manual-decision')
        self.assertEqual(len(s.factions),0)
        pid=next(iter(s.proposals))
        s._do(member_a,(1,'endorse',leader,pid),[leader],s.rng,'manual-decision')
        self.assertEqual(len(s.factions),0)
        s.states[member_b].known_proposals.add(pid)
        s._do(member_b,(1,'endorse',leader,pid),[leader],s.rng,'manual-decision')
        self.assertEqual(len(s.factions),1)
        self.assertEqual(len(next(iter(s.factions.values())).members),3)
        s.book.audit()

    def test_no_faction_ablated(self):
        a=SocialSimulation(407,'no_faction')
        self.assertEqual(a.run(22)['factions'],0)

    def test_no_teach_ablated(self):
        a=SocialSimulation(407,'no_teach')
        self.assertEqual(a.run(15)['actions'].get('teach',0),0)

    def test_checkpoint_rebirth_rolls_back_personal_not_world(self):
        s=SocialSimulation(414)
        a='F001';b='F002'
        s.states[a].cognition.claim('house_history').understanding=.26
        s.save_checkpoint(a)
        s.states[a].cognition.claim('house_history').understanding=.90
        s.states[b].cognition.partner(a).update('ability',False)
        s.founders.people[a].location='ridge'
        s.founders.learn(a,'craft',.3,'after_checkpoint')
        s.kill_and_rebirth(a)
        self.assertAlmostEqual(s.states[a].cognition.claim('house_history').understanding,.26)
        self.assertEqual(s.founders.people[a].location,'house')
        self.assertLess(s.states[b].cognition.partner(a).expectation('ability'),.5)
        s.book.audit()

    def test_ablation_preserves_physical_rules(self):
        for mode in ('full','no_partner','no_teach','no_faction','neutral_trust','isolated'):
            s=SocialSimulation(415,mode)
            out=s.run(10)
            self.assertEqual(out['founders'],100)
            self.assertEqual(out['energy_mass_audit']['rejections'],0)
            self.assertEqual(out['energy_mass_audit']['toll_events'],0)
            self.assertLess(abs(out['energy_mass_audit']['energy_error']),1e-7)

if __name__ == '__main__': unittest.main()
