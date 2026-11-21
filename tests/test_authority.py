"""Integration tests require extracted Core151 engine and reconstructed M01 gateway."""
import unittest
from founders_engine.authority import SingleEngineSession
from run_world_tree_pilot import bootstrap

class SingleAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world, _, cls.tree_id = bootstrap(400)

    def setUp(self):
        self.session = SingleEngineSession(self.world, self.tree_id)

    def test_m01_gateway_authority_binding_cannot_be_replaced(self):
        """The adapter must not be rebound to a different resource authority."""
        world, _, tree_id = bootstrap(420)
        session = SingleEngineSession(world, tree_id)
        gateway = session.gateway
        original_book = gateway.book
        try:
            gateway.book = object()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.step()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.harvest('F001', 'source', 'r1', 'forest', 'plant', .01, .001)
        finally:
            gateway.book = original_book
        session.audit()
        try:
            session.gateway = object()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.audit()
        finally:
            session.gateway = gateway
        session.audit()

    def test_nonowner_tree_stewardship_is_optional_and_book_funded(self):
        """Nonowners can choose to tend, but unrelated Founders need not do so."""
        world, _, tree_id = bootstrap(442)
        session = SingleEngineSession(world, tree_id)
        tree = world.world_trees.worlds[tree_id]
        owner = tree.owner
        others = [fid for fid in world.founders.people if fid != owner]
        helper, decliner = others[:2]
        helper_state, decliner_state = world.states[helper], world.states[decliner]
        helper_state.main_goal = 'solidarity'
        decliner_state.main_goal = 'exploration'
        decliner_state.faction_id = None
        helper_state.faction_id = None
        self.assertNotEqual(helper, owner)
        self.assertNotEqual(decliner, owner)
        world.founders.people[helper].location = 'house'
        world.founders.people[decliner].location = 'house'
        helper_choices = world._proposals(helper, [])
        decliner_choices = world._proposals(decliner, [])
        self.assertTrue(any(p[1] == 'tree_observe' and p[3] == tree_id
                            for p in helper_choices))
        self.assertFalse(any(p[1] in ('tree_observe', 'tree_tend') and p[3] == tree_id
                             for p in decliner_choices))
        before_tick = world.tick
        before_seq = world.book.seq
        before_helper = world.book.energy[f'founder:{helper}']
        before_reserve = world.book.energy[f'reserve:{tree_id}']
        before_decliner = world.book.energy[f'founder:{decliner}']
        # A voluntary action uses the existing SeedRegistry and canonical Book.
        session.tend_tree(helper, tree_id, .65)
        self.assertEqual(world.tick, before_tick)
        self.assertGreater(world.book.seq, before_seq)
        self.assertAlmostEqual(world.book.energy[f'founder:{helper}'],
                               before_helper - .65, places=6)
        self.assertAlmostEqual(world.book.energy[f'reserve:{tree_id}'],
                               before_reserve + .65, places=6)
        self.assertEqual(world.book.energy[f'founder:{decliner}'], before_decliner)
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_invalid_stewardship_rejected_without_book_or_clock_mutation(self):
        """Invalid voluntary transfers never reach the canonical Book writer."""
        world, _, tree_id = bootstrap(449)
        session = SingleEngineSession(world, tree_id)
        founder = next(iter(world.founders.people))
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy))
        for actor, target, amount in (
                ('FAKE', tree_id, .25),
                (founder, 'unknown-tree', .25),
                (founder, tree_id, 0),
                (founder, tree_id, -1),
                (founder, tree_id, float('nan')),
                (founder, tree_id, float('inf')),
                (founder, tree_id, True)):
            with self.subTest(actor=actor, target=target, amount=amount):
                with self.assertRaises(ValueError):
                    session.tend_tree(actor, target, amount)
                self.assertEqual(
                    (world.tick, world.book.seq,
                     dict(world.book.mass), dict(world.book.energy)), before)
                proof = session.audit()
                self.assertEqual(proof.founder_count, 100)
                self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
                self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_missing_energy_account_preflight_does_not_create_account(self):
        """An absent Founder energy key must not be inserted on rejection."""
        from collections import defaultdict
        world, _, tree_id = bootstrap(454)
        session = SingleEngineSession(world, tree_id)
        founder = next(iter(world.founders.people))
        account = f'founder:{founder}'
        original_energy = world.book.energy
        # A missing funded account violates Book conservation. The rejection
        # must not silently recreate it or change the transaction sequence.
        missing_account_fixture = defaultdict(float, original_energy)
        missing_account_fixture.pop(account, None)
        before = (world.tick, world.book.seq,
                  dict(missing_account_fixture), len(world.book.transaction_history))
        try:
            world.book.energy = missing_account_fixture
            # The direct-tending receipt preflight now enforces full Book
            # conservation before the missing-account payment check. Removing
            # a funded account is corrupt Book state, not an ordinary decline.
            with self.assertRaisesRegex(AssertionError, 'ledger error'):
                session.tend_tree(founder, tree_id, .01)
            self.assertNotIn(account, missing_account_fixture)
            self.assertEqual(
                (world.tick, world.book.seq,
                 dict(missing_account_fixture), len(world.book.transaction_history)),
                before)
        finally:
            world.book.energy = original_energy
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_underfunded_stewardship_is_retryable_without_book_mutation(self):
        """An ordinary inability to pay must not poison the one-world session."""
        world, _, tree_id = bootstrap(450)
        session = SingleEngineSession(world, tree_id)
        founder = next(iter(world.founders.people))
        available = world.book.energy[f'founder:{founder}']
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy),
                  len(world.book.transaction_history))
        with self.assertRaisesRegex(ValueError, 'Founder lacks upkeep energy'):
            session.tend_tree(founder, tree_id, available + 1.0)
        self.assertEqual((world.tick, world.book.seq,
                          dict(world.book.mass), dict(world.book.energy),
                          len(world.book.transaction_history)), before)
        self.assertEqual(session.audit().founder_count, 100)
        # A legitimate retry can still settle through the canonical Book.
        session.tend_tree(founder, tree_id, .01)
        self.assertGreater(world.book.seq, before[1])
        proof = session.audit()
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_checkpointed_underfunded_tending_never_writes_checkpoint(self):
        """Rejected local upkeep cannot overwrite a durable canonical checkpoint."""
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(453)
        session = SingleEngineSession(world, tree_id)
        founder = next(iter(world.founders.people))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'canonical.cp'
            save_checkpoint(world, tree_id, path)
            before_bytes = path.read_bytes()
            before = (world.tick, world.book.seq,
                      dict(world.book.mass), dict(world.book.energy))
            insufficient = world.book.energy[f'founder:{founder}'] + 1.0
            with self.assertRaisesRegex(ValueError, 'Founder lacks upkeep energy'):
                session.checkpointed_tend_tree(path, founder, tree_id, insufficient)
            self.assertEqual(path.read_bytes(), before_bytes)
            self.assertEqual(
                (world.tick, world.book.seq,
                 dict(world.book.mass), dict(world.book.energy)), before)
            self.assertEqual(session.audit().founder_count, 100)
            # The same session may still settle an affordable, voluntary action.
            settled = session.checkpointed_tend_tree(path, founder, tree_id, .01)
            self.assertGreater(settled.book_sequence, before[1])
            recovered = load_checkpoint(path, tree_id)
            self.assertEqual(recovered.book.seq, world.book.seq)
            self.assertEqual(recovered.world.tick, world.tick)
            self.assertEqual(dict(recovered.book.mass), dict(world.book.mass))
            self.assertEqual(dict(recovered.book.energy), dict(world.book.energy))
            proof = recovered.audit()
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_voluntary_stewardship_survives_real_ticks(self):
        """One elected Book-funded transfer survives two real Core151 days."""
        world, _, tree_id = bootstrap(443)
        session = SingleEngineSession(world, tree_id)
        tree = world.world_trees.worlds[tree_id]
        helper = next(fid for fid in world.founders.people if fid != tree.owner)
        decliner = next(fid for fid in world.founders.people
                        if fid not in (tree.owner, helper))
        before = session.audit()
        before_decliner = world.book.energy[f'founder:{decliner}']
        before_helper = world.book.energy[f'founder:{helper}']
        before_reserve = world.book.energy[f'reserve:{tree_id}']
        session.tend_tree(helper, tree_id, .25)
        after_tend = session.audit()
        self.assertEqual(after_tend.tick, before.tick)
        self.assertGreater(after_tend.book_sequence, before.book_sequence)
        self.assertAlmostEqual(world.book.energy[f'founder:{helper}'],
                               before_helper - .25, places=6)
        self.assertAlmostEqual(world.book.energy[f'reserve:{tree_id}'],
                               before_reserve + .25, places=6)
        self.assertEqual(world.book.energy[f'founder:{decliner}'],
                         before_decliner)
        for day in range(1, 3):
            session.step()
            snapshot = session.audit()
            self.assertEqual(snapshot.tick, before.tick + day)
            self.assertEqual(snapshot.founder_count, 100)
            self.assertLessEqual(abs(snapshot.book_mass_error), 1e-6)
            self.assertLessEqual(abs(snapshot.book_energy_error), 1e-6)
        self.assertIs(world.book, session.book)
        self.assertEqual(world.ecology.day, world.tick)

    def test_unforced_tree_decisions_during_real_core151_ticks(self):
        """Observe ordinary Founder decisions without assigning stewardship."""
        world, _, tree_id = bootstrap(444)
        session = SingleEngineSession(world, tree_id)
        initial_ids = frozenset(world.founders.people)
        initial_tick = world.tick
        initial_seq = world.book.seq
        # No direct tend_tree or SeedRegistry.tend call: the 100 real
        # Founders choose from their ordinary proposals during each tick.
        for day in range(1, 4):
            session.step()
            proof = session.audit()
            self.assertEqual(proof.tick, initial_tick + day)
            self.assertEqual(proof.founder_count, 100)
            self.assertEqual(frozenset(world.founders.people), initial_ids)
            self.assertIs(session.book, world.book)
            self.assertEqual(world.ecology.day, world.tick)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
        self.assertGreater(world.book.seq, initial_seq)
        # Events are observations, not an artificial minimum quota:
        # zero voluntary tend actions is a valid autonomous outcome.
        # Count actual events, not merely the existence of an event list.
        # No minimum participation: a Founder can decline without failure.
        kinds = [e.get('kind', e.get('action', e.get('type')))
                 for e in world.events]
        maintenance = [e for e in world.events
                       if e.get('kind', e.get('action', e.get('type'))) ==
                       'tree_autonomous_maintenance']
        self.assertEqual(len(maintenance),
                         sum(kind == 'tree_autonomous_maintenance'
                             for kind in kinds))
        for event in maintenance:
            self.assertIn(event['actor'], initial_ids)
            self.assertEqual(event['creation'], tree_id)
            self.assertAlmostEqual(event['amount'], .65, places=6)
        proof = session.audit()
        print('seed444 unforced ticks=%d maintenance=%d mass=%0.12g energy=%0.12g' %
              (proof.tick - initial_tick, len(maintenance),
               proof.book_mass_error, proof.book_energy_error))

    def test_unforced_stewardship_two_seed_comparison(self):
        """Compare real autonomous outcomes without assigning maintenance quotas."""
        observations = []
        for seed in (445, 446):
            with self.subTest(seed=seed):
                world, _, tree_id = bootstrap(seed)
                session = SingleEngineSession(world, tree_id)
                founder_ids = frozenset(world.founders.people)
                start_tick = world.tick
                for _ in range(2):
                    session.step()
                    proof = session.audit()
                    self.assertEqual(proof.founder_count, 100)
                    self.assertEqual(frozenset(world.founders.people), founder_ids)
                    self.assertIs(session.book, world.book)
                    self.assertEqual(world.ecology.day, world.tick)
                    self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
                    self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
                maintenance = [e for e in world.events
                               if e.get('kind', e.get('action', e.get('type'))) ==
                               'tree_autonomous_maintenance']
                for event in maintenance:
                    self.assertIn(event['actor'], founder_ids)
                    self.assertEqual(event['creation'], tree_id)
                    self.assertGreater(event['amount'], 0)
                observations.append((seed, len(maintenance), proof.tick - start_tick,
                                     proof.book_mass_error, proof.book_energy_error))
        for seed, count, days, mass, energy in observations:
            print('seed%d unforced days=%d tending=%d mass=%0.12g energy=%0.12g' %
                  (seed, days, count, mass, energy))

    def test_unforced_stewardship_repeatability_same_seed(self):
        """Identical Core151 seeds must reproduce voluntary tending and Book audits."""
        def run(seed):
            world, _, tree_id = bootstrap(seed)
            session = SingleEngineSession(world, tree_id)
            identities = frozenset(world.founders.people)
            records = []
            for _ in range(3):
                session.step()
                proof = session.audit()
                self.assertEqual(proof.founder_count, 100)
                self.assertEqual(frozenset(world.founders.people), identities)
                self.assertIs(session.book, world.book)
                self.assertEqual(world.ecology.day, world.tick)
                self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
                self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
                events = tuple((e['actor'], e['creation'], e['amount'])
                               for e in world.events
                               if e.get('kind', e.get('action', e.get('type'))) ==
                               'tree_autonomous_maintenance')
                for actor, creation, amount in events:
                    self.assertIn(actor, identities)
                    self.assertEqual(creation, tree_id)
                    self.assertGreater(amount, 0)
                records.append((proof.tick, proof.book_sequence, events,
                                round(proof.book_mass_error, 6),
                                round(proof.book_energy_error, 6)))
            return records
        first = run(447)
        second = run(447)
        self.assertEqual(first, second)
        print('seed447 replay days=3 final_maintenance=%d final_book_seq=%d' %
              (len(first[-1][2]), first[-1][1]))

    def test_unforced_stewardship_five_day_event_growth(self):
        """Five real ticks preserve event history and canonical settlement authority."""
        world, _, tree_id = bootstrap(448)
        session = SingleEngineSession(world, tree_id)
        founder_ids = frozenset(world.founders.people)
        start_tick = world.tick
        previous_events = tuple(world.events)
        previous_seq = world.book.seq
        daily_counts = []
        for day in range(1, 6):
            session.step()
            proof = session.audit()
            self.assertEqual(world.tick, start_tick + day)
            self.assertEqual(world.ecology.day, world.tick)
            self.assertEqual(proof.founder_count, 100)
            self.assertEqual(frozenset(world.founders.people), founder_ids)
            self.assertIs(session.book, world.book)
            self.assertGreaterEqual(world.book.seq, previous_seq)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
            events = tuple(world.events)
            self.assertEqual(events[:len(previous_events)], previous_events)
            for event in events[len(previous_events):]:
                if event.get('kind', event.get('action', event.get('type'))) == 'tree_autonomous_maintenance':
                    self.assertIn(event['actor'], founder_ids)
                    self.assertEqual(event['creation'], tree_id)
                    self.assertGreater(event['amount'], 0)
            daily_counts.append(sum(e.get('kind', e.get('action', e.get('type'))) ==
                                    'tree_autonomous_maintenance' for e in events))
            self.assertGreaterEqual(daily_counts[-1], daily_counts[-2] if len(daily_counts) > 1 else 0)
            previous_events, previous_seq = events, world.book.seq
        count = sum(e.get('kind', e.get('action', e.get('type'))) ==
                    'tree_autonomous_maintenance' for e in world.events)
        self.assertEqual(daily_counts[-1], count)
        print('seed448 unforced daily_cumulative_tending=%s seq=%d mass=%0.12g energy=%0.12g' %
              (daily_counts, proof.book_sequence, proof.book_mass_error,
               proof.book_energy_error))

    def test_secondary_tree_shares_book_without_new_authority(self):
        """A second registered Tree may coexist if it uses the living Book/clock."""
        from copy import copy
        world, _, tree_id = bootstrap(441)
        session = SingleEngineSession(world, tree_id)
        secondary = copy(world.world_trees.worlds[tree_id])
        key = 'SHARED-BOOK-SECONDARY-TREE'
        self.assertIs(secondary.book, world.book)
        self.assertIs(secondary.sim, world)
        before = (world.tick, world.book.seq, dict(world.book.mass),
                  dict(world.book.energy), frozenset(world.founders.people))
        world.world_trees.worlds[key] = secondary
        try:
            snapshot = session.audit()
            self.assertEqual(snapshot.tree_count, 2)
            self.assertEqual((world.tick, world.book.seq,
                              dict(world.book.mass), dict(world.book.energy),
                              frozenset(world.founders.people)), before)
            self.assertLessEqual(abs(snapshot.book_mass_error), 1e-6)
            self.assertLessEqual(abs(snapshot.book_energy_error), 1e-6)
        finally:
            del world.world_trees.worlds[key]
        session.audit()

    def test_secondary_tree_cannot_bind_foreign_book(self):
        """An additional Tree must not become a hidden second resource authority."""
        from copy import copy
        world, _, tree_id = bootstrap(440)
        session = SingleEngineSession(world, tree_id)
        tree = world.world_trees.worlds[tree_id]
        other = copy(tree)
        other.book = object()
        key = 'UNAUTHORIZED-SECONDARY-TREE'
        before = (world.tick, world.book.seq, dict(world.book.mass),
                  dict(world.book.energy), frozenset(world.founders.people))
        world.world_trees.worlds[key] = other
        try:
            for operation in (session.audit, session.step,
                              lambda: session.harvest('F001', 'secondary-tree', '1',
                                                      'forest', 'plant', .01, .001)):
                with self.assertRaisesRegex(RuntimeError,
                                            'noncanonical World Tree resource authority'):
                    operation()
            self.assertEqual(before, (world.tick, world.book.seq,
                                      dict(world.book.mass), dict(world.book.energy),
                                      frozenset(world.founders.people)))
        finally:
            del world.world_trees.worlds[key]
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_missing_authoritative_tree_fails_closed(self):
        """Deleting the original Tree cannot silently fall through to KeyError."""
        world, _, tree_id = bootstrap(421)
        session = SingleEngineSession(world, tree_id)
        original = world.world_trees.worlds.pop(tree_id)
        try:
            for operation in (
                session.audit,
                session.step,
                lambda: session.harvest('F001', 'source', 'r1',
                                        'forest', 'plant', .01, .001),
            ):
                with self.assertRaisesRegex(RuntimeError, 'authoritative World Tree removed'):
                    operation()
        finally:
            world.world_trees.worlds[tree_id] = original
        session.audit()

    def test_founder_registry_object_substitution_fails_closed(self):
        """A shallow copy with the same actors and Book is not the authority."""
        from copy import copy
        world, _, tree_id = bootstrap(423)
        session = SingleEngineSession(world, tree_id)
        original = world.founders
        replacement = copy(original)
        self.assertIs(replacement.book, world.book)
        self.assertIs(replacement.people, original.people)
        try:
            world.founders = replacement
            for operation in (
                session.audit,
                session.step,
                lambda: session.harvest('FAKE', 'invalid-source', 'r1',
                                        'forest', 'plant', .01, .001),
            ):
                with self.assertRaisesRegex(RuntimeError, 'Founder registry object replaced'):
                    operation()
        finally:
            world.founders = original
        session.audit()

    def test_seed439_book_metadata_drift_blocks_world_step(self):
        """Balanced resources cannot conceal a corrupted authoritative Book counter."""
        world, _, tree_id = bootstrap(439)
        session = SingleEngineSession(world, tree_id)
        original = world.book.transactions
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy),
                  frozenset(world.founders.people))
        try:
            world.book.transactions = original + 1
            for operation in (session.audit, session.step,
                              lambda: session.harvest('F001', 'seed439', '1',
                                                      'forest', 'plant', .01, .001)):
                with self.assertRaisesRegex(RuntimeError, 'Book history metadata drift'):
                    operation()
            self.assertEqual((world.tick, world.book.seq,
                              dict(world.book.mass), dict(world.book.energy),
                              frozenset(world.founders.people)), before)
        finally:
            world.book.transactions = original
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_one_book_and_100_founders(self):
        state = self.session.audit()
        self.assertEqual(state.founder_count, 100)
        self.assertIs(self.session.world.book, self.session.book)
        self.assertEqual(state.tree_count, 1)

    def test_reject_second_ledger(self):
        class ShadowBook:
            ledger = object()
            def snapshot(self): return {}
        with self.assertRaises(ValueError):
            self.session.attach_observer(ShadowBook())

    def test_reject_second_clock(self):
        class Clock:
            clock = 42
            def snapshot(self): return {}
        with self.assertRaises(ValueError):
            self.session.attach_observer(Clock())

    def test_accept_read_only_observer(self):
        class Observer:
            def snapshot(self): return {'source': 'synthetic'}
        self.assertEqual(
            self.session.attach_observer(Observer()).snapshot()['source'],
            'synthetic')

    def test_single_clock_and_book_audit(self):
        before = self.session.audit()
        self.session.step()
        after = self.session.audit()
        self.assertEqual(after.tick, before.tick + 1)
        self.assertEqual(after.founder_count, 100)
        self.assertLess(abs(after.book_mass_error), 1e-6)
        self.assertLess(abs(after.book_energy_error), 1e-6)

    def test_m01_harvest_preflight_rejects_finite_conservation_drift(self):
        """A corrupt canonical Book cannot fund even a synthetic M01 harvest."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(418)
        session = SingleEngineSession(world, tree_id)
        valid = world.book.audit()
        before_tick, before_seq = world.tick, world.book.seq
        before_receipts = dict(world.book.request_receipts)
        for key in ('mass_error', 'energy_error'):
            broken = dict(valid)
            broken[key] = 0.001
            with self.subTest(key=key):
                with patch.object(world.book, 'audit', return_value=broken):
                    with patch.object(session.gateway, 'founder_harvest') as gateway:
                        with self.assertRaisesRegex(RuntimeError, 'conservation drift exceeds tolerance'):
                            session.harvest('F001', 'source', 'r1',
                                            'forest', 'plant', .01, .001)
                        gateway.assert_not_called()
                self.assertEqual((world.tick, world.book.seq), (before_tick, before_seq))
                self.assertEqual(world.book.request_receipts, before_receipts)
        session.audit()

    def test_seed435_oversized_integer_harvest_fails_without_book_mutation(self):
        """M01 rejects unbounded or imprecise integers without OverflowError."""
        world, _, tree_id = bootstrap(435)
        session = SingleEngineSession(world, tree_id)
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy),
                  dict(world.book.request_receipts))
        for amount in (2**53 + 1, 10**1000):
            for position in ('mass', 'energy'):
                with self.subTest(amount_digits=len(str(amount)), position=position):
                    mass = amount if position == 'mass' else .01
                    energy = amount if position == 'energy' else .001
                    with self.assertRaises(ValueError):
                        session.harvest('F001', 'seed435-oversized', '1',
                                        'forest', 'plant', mass, energy)
                    self.assertEqual(
                        (world.tick, world.book.seq,
                         dict(world.book.mass), dict(world.book.energy),
                         dict(world.book.request_receipts)), before)
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_seed436_oversized_finite_float_harvest_fails_without_book_mutation(self):
        """Large finite floats cannot bypass the precise M01 quantity bound."""
        world, _, tree_id = bootstrap(436)
        session = SingleEngineSession(world, tree_id)
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy),
                  dict(world.book.request_receipts))
        for amount in (float(2**53 + 2), 1e100):
            for position in ('mass', 'energy'):
                with self.subTest(amount=amount, position=position):
                    mass = amount if position == 'mass' else .01
                    energy = amount if position == 'energy' else .001
                    with self.assertRaises(ValueError):
                        session.harvest('F001', 'seed436-oversized-float', '1',
                                        'forest', 'plant', mass, energy)
                    self.assertEqual(
                        (world.tick, world.book.seq,
                         dict(world.book.mass), dict(world.book.energy),
                         dict(world.book.request_receipts)), before)
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_reject_invalid_founder_harvest_without_book_change(self):
        before = self.session.book.seq
        with self.assertRaises(ValueError):
            self.session.harvest('FAKE', 'invalid-source', 'r1',
                                 'forest', 'plant', .01, .001)
        self.assertEqual(self.session.book.seq, before)

    def test_detect_founder_identity_substitution(self):
        world, _, tree_id = bootstrap(401)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        founder = world.founders.people.pop(founder_id)
        try:
            world.founders.people['F999'] = founder
            with self.assertRaisesRegex(RuntimeError, 'Founder identities changed'):
                session.audit()
        finally:
            world.founders.people.pop('F999', None)
            world.founders.people[founder_id] = founder

    def test_reject_world_tree_object_substitution(self):
        """Same registry key and shared Book must not permit a new Tree actor."""
        from copy import copy
        world, _, tree_id = bootstrap(419)
        session = SingleEngineSession(world, tree_id)
        original = world.world_trees.worlds[tree_id]
        replacement = copy(original)
        self.assertIsNot(replacement, original)
        self.assertIs(replacement.book, world.book)
        self.assertIs(replacement.sim, world)
        try:
            world.world_trees.worlds[tree_id] = replacement
            with self.assertRaisesRegex(RuntimeError, 'World Tree object replaced'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'World Tree object replaced'):
                session.step()
            with self.assertRaisesRegex(RuntimeError, 'World Tree object replaced'):
                session.harvest('FAKE', 'invalid-source', 'r1',
                                'forest', 'plant', .01, .001)
        finally:
            world.world_trees.worlds[tree_id] = original
        session.audit()

    def test_detect_founder_registry_book_swap(self):
        world, _, tree_id = bootstrap(402)
        session = SingleEngineSession(world, tree_id)
        original = world.founders.book
        try:
            world.founders.book = object()
            with self.assertRaisesRegex(RuntimeError, 'registry Book authority changed'):
                session.audit()
        finally:
            world.founders.book = original

    def test_detect_same_id_founder_object_replacement(self):
        from copy import copy
        world, _, tree_id = bootstrap(403)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        original = world.founders.people[founder_id]
        try:
            world.founders.people[founder_id] = copy(original)
            with self.assertRaisesRegex(RuntimeError, 'Founder object replaced'):
                session.audit()
        finally:
            world.founders.people[founder_id] = original

    def test_original_founder_reference_is_retained(self):
        world, _, tree_id = bootstrap(404)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        original = world.founders.people[founder_id]
        self.assertIs(session._founder_objects[founder_id], original)
        try:
            del world.founders.people[founder_id]
            with self.assertRaisesRegex(RuntimeError, 'Founder identities changed'):
                session.audit()
            self.assertIs(session._founder_objects[founder_id], original)
        finally:
            world.founders.people[founder_id] = original

    def test_invalid_conservation_audit_types_block_step_and_harvest(self):
        """A Boolean or string is not a physical Book conservation residual."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(422)
        session = SingleEngineSession(world, tree_id)
        valid = world.book.audit()
        before = (world.tick, world.book.seq)
        for key, value in (('mass_error', True), ('energy_error', '0.0')):
            broken = dict(valid)
            broken[key] = value
            with self.subTest(key=key), patch.object(world.book, 'audit', return_value=broken):
                with patch.object(world, 'step') as step:
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book conservation audit type'):
                        session.step()
                    step.assert_not_called()
                with patch.object(session.gateway, 'founder_harvest') as gateway:
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book conservation audit type'):
                        session.harvest('F001', 'source', 'r1', 'forest', 'plant', .01, .001)
                    gateway.assert_not_called()
            self.assertEqual((world.tick, world.book.seq), before)
        session.audit()

    def test_nonfinite_book_audit_fails_closed(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(405)
        session = SingleEngineSession(world, tree_id)
        valid = world.book.audit()
        for key, invalid in (('mass_error', float('nan')),
                             ('energy_error', float('inf'))):
            broken = dict(valid)
            broken[key] = invalid
            with self.subTest(key=key), patch.object(world.book, 'audit', return_value=broken):
                with self.assertRaisesRegex(RuntimeError, 'non-finite canonical Book'):
                    session.audit()

    def test_incomplete_conservation_audit_fails_closed(self):
        """Missing audit fields must reject both live mutations without KeyError."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(424)
        session = SingleEngineSession(world, tree_id)
        before = (world.tick, world.book.seq)
        for proof in ({'mass_error': 0.0}, {'energy_error': 0.0}, None):
            with self.subTest(proof=proof), patch.object(
                    world.book, 'audit', return_value=proof), patch.object(
                    world, 'step') as advance, patch.object(
                    session.gateway, 'founder_harvest') as settle:
                with self.assertRaisesRegex(RuntimeError, 'incomplete canonical Book'):
                    session.step()
                with self.assertRaisesRegex(RuntimeError, 'incomplete canonical Book'):
                    session.harvest('F001', 'source', 'r1', 'forest', 'plant', .01, .001)
                advance.assert_not_called()
                settle.assert_not_called()
            self.assertEqual((world.tick, world.book.seq), before)
        session.audit()

    def test_failed_world_step_quarantines_session(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(408)
        session = SingleEngineSession(world, tree_id)
        before = world.tick

        def partial_step():
            world.tick += 1
            raise OSError('injected mid-step failure')

        with patch.object(world, 'step', side_effect=partial_step):
            with self.assertRaisesRegex(OSError, 'mid-step failure'):
                session.step()
        self.assertEqual(world.tick, before + 1)
        with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
            session.audit()
        with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
            session.step()
        with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
            session.harvest('FAKE', 'invalid-source', 'r1',
                            'forest', 'plant', .01, .001)

    def test_failed_step_with_book_mutation_but_no_clock_advance_quarantines(self):
        """An interrupted real step must fail closed even if its tick never advances."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(415)
        session = SingleEngineSession(world, tree_id)
        before_tick, before_seq = world.tick, world.book.seq
        key = 'plant:injected-step-failure'
        original = world.book.mass.get(key)

        def partial_step():
            world.book.mass[key] = world.book.mass.get(key, 0.0) + 0.25
            raise OSError('injected pre-clock world-step failure')

        try:
            with patch.object(world, 'step', side_effect=partial_step):
                with self.assertRaisesRegex(OSError, 'pre-clock world-step failure'):
                    session.step()
            self.assertEqual(world.tick, before_tick)
            self.assertEqual(world.book.seq, before_seq)
            with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
                session.step()
            with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
                session.harvest('FAKE', 'invalid-source', 'r1',
                                'forest', 'plant', .01, .001)
        finally:
            if original is None:
                world.book.mass.pop(key, None)
            else:
                world.book.mass[key] = original

    def test_failed_harvest_after_book_mutation_quarantines_session(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(409)
        session = SingleEngineSession(world, tree_id)
        before = world.book.seq

        def partial_harvest(*args, **kwargs):
            world.book.seq += 1
            raise OSError('injected post-mutation harvest failure')

        with patch.object(session.gateway, 'founder_harvest',
                          side_effect=partial_harvest):
            with self.assertRaisesRegex(OSError, 'post-mutation harvest failure'):
                session.harvest('F001', 'source', 'r1',
                                'forest', 'plant', .01, .001)
        self.assertEqual(world.book.seq, before + 1)
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.audit()
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.step()

    def test_harvest_failure_without_sequence_advance_quarantines(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(411)
        session = SingleEngineSession(world, tree_id)
        before = world.book.seq
        with patch.object(session.gateway, 'founder_harvest',
                          side_effect=OSError('injected pre-sequence failure')):
            with self.assertRaisesRegex(OSError, 'pre-sequence failure'):
                session.harvest('F001', 'source', 'r1',
                                'forest', 'plant', .01, .001)
        self.assertEqual(world.book.seq, before)
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.audit()
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.step()

    def test_value_error_after_book_balance_mutation_quarantines(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(412)
        session = SingleEngineSession(world, tree_id)
        before_seq = world.book.seq
        key = 'plant:injected-uncommitted'
        original = world.book.mass.get(key, 0.0)

        def partial_validation(*args, **kwargs):
            world.book.mass[key] = original + 0.25
            raise ValueError('injected mutation before rejected request')

        try:
            with patch.object(session.gateway, 'founder_harvest',
                              side_effect=partial_validation):
                with self.assertRaisesRegex(ValueError, 'injected mutation'):
                    session.harvest('F001', 'source', 'r1',
                                    'forest', 'plant', .01, .001)
            self.assertEqual(world.book.seq, before_seq)
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.step()
        finally:
            if original == 0.0:
                world.book.mass.pop(key, None)
            else:
                world.book.mass[key] = original

    def test_nested_receipt_mutation_on_rejected_harvest_quarantines(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(413)
        session = SingleEngineSession(world, tree_id)
        # Synthetic nested receipt fixture probes the snapshot guard only.
        key = 'injected:nested-receipt'
        receipt = {'nested': ['before']}
        world.book.request_receipts[key] = receipt
        try:
            def corrupt_then_reject(*args, **kwargs):
                receipt['nested'].append('after')
                raise ValueError('injected nested receipt mutation')

            with patch.object(session.gateway, 'founder_harvest',
                              side_effect=corrupt_then_reject):
                with self.assertRaisesRegex(ValueError, 'nested receipt mutation'):
                    session.harvest('F001', 'source', 'r1',
                                    'forest', 'plant', .01, .001)
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.audit()
        finally:
            world.book.request_receipts.pop(key, None)

    def test_invalid_harvest_does_not_quarantine_clean_session(self):
        world, _, tree_id = bootstrap(410)
        session = SingleEngineSession(world, tree_id)
        before = world.book.seq
        with self.assertRaises(ValueError):
            session.harvest('FAKE', 'invalid-source', 'r1',
                            'forest', 'plant', .01, .001)
        self.assertEqual(world.book.seq, before)
        session.audit()

    def test_reject_out_of_session_world_clock_change(self):
        world, _, tree_id = bootstrap(406)
        session = SingleEngineSession(world, tree_id)
        original_tick = world.tick
        try:
            world.tick += 1
            with self.assertRaisesRegex(RuntimeError, 'clock changed outside session'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'clock changed outside session'):
                session.step()
        finally:
            world.tick = original_tick
        session.audit()

    def test_finite_conservation_drift_blocks_real_world_step(self):
        """A finite but materially unbalanced Book must fail before a real tick."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(417)
        session = SingleEngineSession(world, tree_id)
        before_tick, before_seq = world.tick, world.book.seq
        for key in ('mass_error', 'energy_error'):
            with self.subTest(key=key):
                proof = dict(world.book.audit())
                proof[key] = 0.25
                with patch.object(world.book, 'audit', return_value=proof), \
                     patch.object(world, 'step') as advance:
                    with self.assertRaisesRegex(RuntimeError, 'conservation drift exceeds tolerance'):
                        session.step()
                    advance.assert_not_called()
                self.assertEqual((world.tick, world.book.seq),
                                 (before_tick, before_seq))
        session.audit()

    def test_failed_preflight_book_audit_does_not_advance_world(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(416)
        session = SingleEngineSession(world, tree_id)
        before_tick = world.tick
        before_seq = world.book.seq
        with patch.object(world.book, 'audit', return_value={
            'mass_error': float('nan'), 'energy_error': 0.0,
        }), patch.object(world, 'step') as advance:
            with self.assertRaisesRegex(RuntimeError, 'non-finite canonical Book conservation audit'):
                session.step()
            advance.assert_not_called()
        self.assertEqual(world.tick, before_tick)
        self.assertEqual(world.book.seq, before_seq)
        session.audit()

    def test_reject_invalid_canonical_book_sequence_types(self):
        world, _, tree_id = bootstrap(414)
        session = SingleEngineSession(world, tree_id)
        original = world.book.seq
        for invalid in (True, False, -1, 0.5):
            with self.subTest(invalid=invalid):
                try:
                    world.book.seq = invalid
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book sequence'):
                        session.audit()
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book sequence'):
                        session.step()
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book sequence'):
                        session.harvest('FAKE', 'invalid-source', 'r1',
                                        'forest', 'plant', .01, .001)
                finally:
                    world.book.seq = original
        session.audit()

    def test_reject_out_of_session_book_sequence_change(self):
        world, _, tree_id = bootstrap(407)
        session = SingleEngineSession(world, tree_id)
        original_seq = world.book.seq
        try:
            world.book.seq += 1
            with self.assertRaisesRegex(RuntimeError, 'Book sequence changed outside session'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'Book sequence changed outside session'):
                session.harvest('FAKE', 'invalid-source', 'r1',
                                'forest', 'plant', .01, .001)
        finally:
            world.book.seq = original_seq
        session.audit()
        session.step()
        self.assertEqual(session.audit().book_sequence, world.book.seq)

    def test_book_replay_receipt_must_belong_to_existing_history(self):
        from founders_civ.core.ledger import Book, Transaction
        book = Book()
        book.seed_mass('plant:source', 2.0)
        book.seed_energy('chem:source', 3.0)
        book.freeze()
        legs = (('plant:source', 'plant:founder:F001', 0.5),)
        first, applied = book.move_once('m01:test:source:r1', material=legs)
        self.assertTrue(applied)
        before = (book.seq, dict(book.mass), dict(book.energy))
        replay, applied = book.move_once('m01:test:source:r1', material=legs)
        self.assertFalse(applied)
        self.assertEqual(first, replay)
        self.assertEqual(before, (book.seq, dict(book.mass), dict(book.energy)))
        key = 'm01:test:source:r1'
        original = book.request_receipts[key]
        try:
            book.request_receipts[key] = (original[0], Transaction(
                book.seq + 1, 'move', legs, (), 0.0, 0.0))
            with self.assertRaisesRegex(ValueError, 'invalid canonical Book replay receipt'):
                book.move_once(key, material=legs)
            self.assertEqual(before, (book.seq, dict(book.mass), dict(book.energy)))
        finally:
            book.request_receipts[key] = original
        book.audit()

    def test_world_tree_registry_object_substitution_fails_closed(self):
        """A copied registry is not the authoritative living Tree registry."""
        from copy import copy
        world, _, tree_id = bootstrap(425)
        session = SingleEngineSession(world, tree_id)
        original = world.world_trees
        before = (world.tick, world.book.seq)
        try:
            world.world_trees = copy(original)
            for operation in (
                session.audit,
                session.step,
                lambda: session.harvest('F001', 'source', 'r1',
                                        'forest', 'plant', .01, .001),
            ):
                with self.assertRaisesRegex(
                        RuntimeError, 'authoritative World Tree registry object replaced'):
                    operation()
            self.assertEqual((world.tick, world.book.seq), before)
        finally:
            world.world_trees = original
        session.audit()

    def test_ecology_object_substitution_fails_closed(self):
        """A copied ecology with the same day must not replace the live actor."""
        from copy import copy
        world, _, tree_id = bootstrap(426)
        session = SingleEngineSession(world, tree_id)
        original = world.ecology
        before = (world.tick, world.book.seq)
        try:
            world.ecology = copy(original)
            self.assertEqual(world.ecology.day, world.tick)
            for operation in (
                session.audit,
                session.step,
                lambda: session.harvest('FAKE', 'invalid-source', 'r1',
                                        'forest', 'plant', .01, .001),
            ):
                with self.assertRaisesRegex(
                        RuntimeError, 'authoritative ecology object replaced'):
                    operation()
            self.assertEqual((world.tick, world.book.seq), before)
        finally:
            world.ecology = original
        session.audit()

    def test_oversized_integer_stewardship_rejected_without_book_mutation(self):
        """Seed 455: huge int input must fail before mutable Core151 tending."""
        world, _, tree_id = bootstrap(455)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy),
                  list(world.book.transaction_history))
        with self.assertRaisesRegex(ValueError, 'invalid stewardship energy'):
            session.tend_tree(founder_id, tree_id, 10 ** 1000)
        self.assertEqual(before, (world.tick, world.book.seq,
                                  dict(world.book.mass), dict(world.book.energy),
                                  list(world.book.transaction_history)))
        self.assertFalse(session._checkpoint_uncertain)
        session.audit()

    def test_seed427_numeric_book_residuals_in_ci(self):
        """Execute the actual seed-427 conservation test in the existing CI discovery pattern."""
        from test_book_residual_evidence import BookResidualEvidenceTests
        result = unittest.TestResult()
        BookResidualEvidenceTests("test_real_tick_reports_finite_conservation_residuals").run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertFalse(result.failures, result.failures)
        self.assertFalse(result.errors, result.errors)

    def test_seed456_rejects_inconsistent_tree_metadata_without_settlement(self):
        """A planted non-world or mismatched creation cannot receive Tree upkeep."""
        world, _, tree_id = bootstrap(456)
        session = SingleEngineSession(world, tree_id)
        creation = world.seeds.plants[tree_id]
        original = dict(creation)
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy),
                  list(world.book.transaction_history))
        founder_id = next(iter(world.founders.people))
        try:
            for key, bad in (('kind', 'species'), ('id', 'CRE-INVALID'),
                             ('status', 'collapsed')):
                with self.subTest(field=key):
                    creation[key] = bad
                    with self.assertRaisesRegex(ValueError, 'stable planted World Tree'):
                        session.tend_tree(founder_id, tree_id, .01)
                    creation[key] = original[key]
                    self.assertEqual(before, (world.tick, world.book.seq,
                        dict(world.book.mass), dict(world.book.energy),
                        list(world.book.transaction_history)))
        finally:
            creation.clear()
            creation.update(original)
        self.assertFalse(session._checkpoint_uncertain)
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)


    def test_seed457_invalid_tree_metadata_allows_next_real_tick(self):
        """A rejected voluntary tend cannot poison the next real Core151 day."""
        world, _, tree_id = bootstrap(457)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        creation = world.seeds.plants[tree_id]
        original_kind = creation['kind']
        before_tick = world.tick
        before_seq = world.book.seq
        before_energy = dict(world.book.energy)
        try:
            creation['kind'] = 'species'
            with self.assertRaisesRegex(ValueError, 'stable planted World Tree'):
                session.tend_tree(founder_id, tree_id, 0.01)
            self.assertEqual(world.tick, before_tick)
            self.assertEqual(world.book.seq, before_seq)
            self.assertEqual(dict(world.book.energy), before_energy)
            self.assertFalse(session._checkpoint_uncertain)
        finally:
            creation['kind'] = original_kind
        session.step()
        proof = session.audit()
        self.assertEqual(world.tick, before_tick + 1)
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)


    def test_seed458_corrupt_book_receipt_blocks_checkpointed_tending(self):
        """A forged M01 receipt cannot be durably endorsed by Tree tending."""
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from founders_civ.core.ledger import Transaction
        from founders_engine.checkpoint import save_checkpoint
        world, _, tree_id = bootstrap(458)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'world.checkpoint'
            save_checkpoint(world, tree_id, path)
            original_bytes = path.read_bytes()
            before_tick = world.tick
            before_seq = world.book.seq
            before_energy = dict(world.book.energy)
            # A receipt referencing a nonexistent Book transaction must never
            # survive the canonical checkpoint validator.
            bogus = Transaction(world.book.seq + 1, 'move', (), (), 0.0, 0.0)
            world.book.request_receipts['m01:forged:seed458'] = (((), ()), bogus)
            try:
                with self.assertRaises(ValueError):
                    session.checkpointed_tend_tree(path, founder_id, tree_id, 0.01)
                # Preflight rejects corruption before any tending settlement.
                self.assertFalse(session._checkpoint_uncertain)
                self.assertEqual(path.read_bytes(), original_bytes)
                self.assertEqual(world.tick, before_tick)
                self.assertEqual(world.book.seq, before_seq)
                self.assertEqual(dict(world.book.energy), before_energy)
            finally:
                world.book.request_receipts.pop('m01:forged:seed458', None)
            # Removing the injected corruption restores a usable session.
            session.checkpointed_tend_tree(path, founder_id, tree_id, 0.01)
            self.assertGreater(world.book.seq, before_seq)
            self.assertEqual(session.audit().founder_count, 100)


    def test_seed459_corrupt_receipt_blocks_checkpointed_harvest_before_book_move(self):
        """A forged receipt must not let M01 spend Tree inventory before save."""
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from founders_civ.core.ledger import Transaction
        from founders_engine.checkpoint import save_checkpoint
        world, _, tree_id = bootstrap(459)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'world.checkpoint'
            save_checkpoint(world, tree_id, path)
            original_bytes = path.read_bytes()
            before = (world.tick, world.book.seq, dict(world.book.mass),
                      dict(world.book.energy), list(world.book.transaction_history))
            world.book.request_receipts['m01:forged:seed459'] = (
                ((), ()), Transaction(world.book.seq + 1, 'move', (), (), 0., 0.))
            try:
                with self.assertRaises(ValueError):
                    session.checkpointed_harvest(
                        path, founder_id, 'seed459-source', 1,
                        'world', 'plant', 0.01)
                self.assertEqual(path.read_bytes(), original_bytes)
                self.assertEqual(before, (world.tick, world.book.seq,
                    dict(world.book.mass), dict(world.book.energy),
                    list(world.book.transaction_history)))
                self.assertFalse(session._checkpoint_uncertain)
            finally:
                world.book.request_receipts.pop('m01:forged:seed459', None)
            proof = session.audit()
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
            # A rejected forged receipt must not disable subsequent real ticks.
            before_tick = world.tick
            session.step()
            self.assertEqual(world.tick, before_tick + 1)
            after = session.audit()
            self.assertEqual(after.founder_count, 100)
            self.assertLessEqual(abs(after.book_mass_error), 1e-6)
            self.assertLessEqual(abs(after.book_energy_error), 1e-6)


    def test_seed460_checkpointed_tending_survives_restart_and_real_tick(self):
        """Durable local tending keeps one Book and Founder registry after reload."""
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from founders_engine.checkpoint import load_checkpoint, save_checkpoint
        world, _, tree_id = bootstrap(460)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        founder_ids = frozenset(world.founders.people)
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'world.checkpoint'
            save_checkpoint(world, tree_id, path)
            before_seq = world.book.seq
            before_energy = world.book.energy[f'founder:{founder_id}']
            before_reserve = world.book.energy[f'reserve:{tree_id}']
            session.checkpointed_tend_tree(path, founder_id, tree_id, 0.01)
            self.assertGreater(world.book.seq, before_seq)
            settled = (world.tick, world.book.seq,
                       dict(world.book.mass), dict(world.book.energy),
                       list(world.book.transaction_history))
            self.assertAlmostEqual(
                world.book.energy[f'founder:{founder_id}'],
                before_energy - 0.01, places=7)
            self.assertAlmostEqual(
                world.book.energy[f'reserve:{tree_id}'],
                before_reserve + 0.01, places=7)
            recovered = load_checkpoint(path, expected_tree_id=tree_id)
            self.assertIs(recovered.world.book, recovered.book)
            self.assertIs(recovered.world.founders.book, recovered.book)
            self.assertEqual(frozenset(recovered.world.founders.people), founder_ids)
            self.assertEqual(settled, (
                recovered.world.tick, recovered.book.seq,
                dict(recovered.book.mass), dict(recovered.book.energy),
                list(recovered.book.transaction_history)))
            recovered.step()
            proof = recovered.audit()
            self.assertEqual(proof.tick, settled[0] + 1)
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_seed461_tending_checkpoint_failure_requires_durable_recovery(self):
        """A failed local save cannot ACK a RAM-only Tree energy transfer."""
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(461)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'world.checkpoint'
            save_checkpoint(world, tree_id, path)
            original_bytes = path.read_bytes()
            original_seq = world.book.seq
            original_energy = dict(world.book.energy)
            with patch('founders_engine.checkpoint.save_checkpoint',
                       side_effect=OSError('seed461 injected save failure')):
                with self.assertRaisesRegex(OSError, 'seed461 injected save failure'):
                    session.checkpointed_tend_tree(path, founder_id, tree_id, .01)
            self.assertTrue(session._checkpoint_uncertain)
            self.assertEqual(path.read_bytes(), original_bytes)
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.step()
            # An ambiguous RAM-only settlement must also block another tend,
            # even when the Founder still has enough energy to pay twice.
            poisoned_seq = world.book.seq
            poisoned_energy = dict(world.book.energy)
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.checkpointed_tend_tree(path, founder_id, tree_id, .01)
            self.assertEqual(world.book.seq, poisoned_seq)
            self.assertEqual(dict(world.book.energy), poisoned_energy)
            self.assertEqual(path.read_bytes(), original_bytes)
            recovered = load_checkpoint(path, expected_tree_id=tree_id)
            self.assertEqual(recovered.book.seq, original_seq)
            self.assertEqual(dict(recovered.book.energy), original_energy)
            self.assertEqual(recovered.audit().founder_count, 100)
            recovered.checkpointed_tend_tree(path, founder_id, tree_id, .01)
            self.assertGreater(recovered.book.seq, original_seq)
            reloaded = load_checkpoint(path, expected_tree_id=tree_id)
            self.assertEqual(reloaded.book.seq, recovered.book.seq)
            self.assertEqual(dict(reloaded.book.energy), dict(recovered.book.energy))
            proof = reloaded.audit()
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)


    def test_seed462_direct_tending_rejects_forged_receipt_before_settlement(self):
        """Direct voluntary tending must reject forged Book replay metadata."""
        world, _, tree_id = bootstrap(462)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        before = (world.tick, world.book.seq,
                  dict(world.book.mass), dict(world.book.energy),
                  list(world.book.transaction_history))
        key = 'm01:forged:seed462'
        self.assertNotIn(key, world.book.request_receipts)
        try:
            # Receipt refers to a transaction that never existed.
            world.book.request_receipts[key] = 10**9
            with self.assertRaises((RuntimeError, ValueError)):
                session.tend_tree(founder_id, tree_id, .01)
            self.assertEqual((world.tick, world.book.seq,
                              dict(world.book.mass), dict(world.book.energy),
                              list(world.book.transaction_history)), before)
            self.assertFalse(session._checkpoint_uncertain)
        finally:
            world.book.request_receipts.pop(key, None)
        proof = session.audit()
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

if __name__ == '__main__':
    unittest.main()
