"""Adapter compatibility, replay, and conservation tests (actual WORLD-024 host)."""
import unittest
from dataclasses import replace
from founders_civ.integration import (ScenarioSpec, StressWindow, IntegrationHost, Extension, CompatibilityError)
from founders_civ.integration.branches import describe_branch
from founders_civ.integration.extensions import resolve_extensions
from founders_civ.integration.compat import fingerprint,check,reviewed_check
from founders_civ.experimental.social_agents import SocialSimulation
from pathlib import Path

class AdapterCompatibilityTests(unittest.TestCase):
    def test_schema_version_rejected(self):
        with self.assertRaises(CompatibilityError):ScenarioSpec(schema_version='2.0')
    def test_unknown_fields_rejected(self):
        with self.assertRaises(ValueError):ScenarioSpec.from_dict({'foo':1})
    def test_governance_and_extraction_rejected(self):
        for d in ({'governance':'immortal'}, {'extraction':'infinite'}, {'cycles':-1},{'allow_private':1}):
            with self.subTest(d=d),self.assertRaises(ValueError):ScenarioSpec.from_dict(d)
    def test_stress_validation_rejected(self):
        for d in ({'disease':1.5},{'rainfall':float('nan')},{'start':7,'end':3},{'upkeeps':-1}):
            with self.subTest(d=d),self.assertRaises(ValueError):StressWindow.from_dict(d)
    def test_external_code_requires_explicit_optin(self):
        with self.assertRaises(CompatibilityError):resolve_extensions(('examples.extensions.archival_monitor:ArchiveMonitor',))
    def test_reviewed_local_extension(self):
        e=resolve_extensions(('examples.extensions.archival_monitor:ArchiveMonitor',),allow_local_code=True)
        self.assertEqual(e[0].id,'archive_monitor')
    def test_dependencies_checked(self):
        class NeedsExtra(Extension):
            id='needs_other'; requires=('unknown',)
        with self.assertRaises(CompatibilityError):IntegrationHost(ScenarioSpec(cycles=0),extensions=(NeedsExtra(),))
    def test_duplicate_extensions_rejected(self):
        class X(Extension):id='x'
        with self.assertRaises(CompatibilityError):IntegrationHost(ScenarioSpec(cycles=0),extensions=(X(),X()))
    def test_static_fingerprint(self):
        root=Path(__file__).resolve().parents[1]
        x=check(root,root/'docs/INTEGRATION_025/BASELINE_HASHES.json')
        # The immutable INTEGRATION-025 baseline must report experimental edits.
        # This branch deliberately modifies world_trees.py; never silently
        # bless the changed hash by regenerating the canonical manifest.
        self.assertEqual(x['status'],'drift_requires_review')
        self.assertEqual(set(x['changed_files']),{'founders_civ/experimental/world_trees.py','founders_civ/core/ledger.py','founders_civ/experimental/world_integration.py'})
        # Retain the historical C004 declaration unchanged: it must reject the
        # genuinely modified C015 scheduler instead of silently blessing drift.
        old=reviewed_check(root,root/'docs/INTEGRATION_025/BASELINE_HASHES.json',
                           root/'docs/INTEGRATION_025/APPROVED_DRIFT_C004.json')
        self.assertEqual(old['status'],'drift_requires_review')
        self.assertEqual(old['unapproved_files'],['founders_civ/experimental/world_integration.py'])
        historical=reviewed_check(root,root/'docs/INTEGRATION_025/BASELINE_HASHES.json',
                                  root/'docs/INTEGRATION_025/APPROVED_DRIFT_C015.json')
        self.assertEqual(historical['status'],'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py',historical['unapproved_files'])
        older=reviewed_check(root,root/'docs/INTEGRATION_025/BASELINE_HASHES.json',
                             root/'docs/INTEGRATION_025/APPROVED_DRIFT_C016.json')
        self.assertEqual(older['status'],'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py', older['unapproved_files'])
        c017=reviewed_check(root,root/'docs/INTEGRATION_025/BASELINE_HASHES.json',
                             root/'docs/INTEGRATION_025/APPROVED_DRIFT_C017.json')
        self.assertEqual(c017['status'],'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py',c017['unapproved_files'])
        candidate=reviewed_check(root,root/'docs/INTEGRATION_025/BASELINE_HASHES.json',
                                 root/'docs/INTEGRATION_025/APPROVED_DRIFT_C018.json')
        # C018 is immutable historical evidence, not approval for newer code.
        self.assertEqual(candidate['status'],'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py',candidate['unapproved_files'])
    def test_legacy_social_branch_readonly(self):
        s=SocialSimulation(seed=820)
        d=describe_branch(s)
        self.assertEqual(d['branch'],'SOCIAL-021')
        self.assertEqual(d['founders'],100)
        self.assertIn('world_trees',d['not_supported'])
    def test_commons_runs_and_balances(self):
        spec=ScenarioSpec(seed=820,cycles=4)
        host=IntegrationHost(spec)
        out=host.run()
        self.assertEqual(out['summary']['founders'],100)
        self.assertLess(abs(out['summary']['conservation']['mass_error']),1e-7)
        self.assertLess(abs(out['summary']['conservation']['energy_error']),1e-6)
        self.assertGreater(out['events_forwarded'],0)
        self.assertEqual(describe_branch(host.sim)['branch'],'WORLD-024')
        self.assertIn('counts',out['extensions']['event_tally'])
    def test_determinism(self):
        a=IntegrationHost(ScenarioSpec(seed=821,cycles=3)).run()
        b=IntegrationHost(ScenarioSpec(seed=821,cycles=3)).run()
        for k in ('summary','extensions','events_forwarded','final_observation','scenario_digest'):
            self.assertEqual(a[k],b[k],k)
    def test_variants(self):
        configs=[('owner','careful','full'),('fragmented','none','no_teach'),('none','intensive','isolated')]
        for gov,ex,mode in configs:
            with self.subTest(gov=gov,ex=ex,mode=mode):
                spec=ScenarioSpec(seed=822,cycles=3,governance=gov,extraction=ex,social_mode=mode,
                                  stress=(StressWindow(start=1,end=4,rainfall=.8),))
                o=IntegrationHost(spec).run()
                self.assertEqual(o['summary']['founders'],100)
                self.assertTrue(o['final_observation']['shared_tree_state'] in ('active','archived'))
    def test_snapshot_nonresumable(self):
        host=IntegrationHost(ScenarioSpec(seed=820,cycles=0))
        view=host.export_snapshot()
        self.assertIn('read-only',view['caveat'])
        self.assertEqual(view['observation']['founders'],100)
    def test_plugin_receives_immutable_dto(self):
        # Snapshot DTO is frozen; extensions do not receive Book or Agent objects.
        from dataclasses import FrozenInstanceError
        h=IntegrationHost(ScenarioSpec(seed=820,cycles=0,extensions=()))
        with self.assertRaises(FrozenInstanceError):h._observation().founders=0

if __name__=='__main__':unittest.main()
