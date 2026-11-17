"""Pre-integration observability and canonical coverage test suite."""
import unittest,json,tempfile,csv,sys
from pathlib import Path
from founders_civ.canon import SYSTEMS,TOLL,EXPERIMENT
from founders_civ.core.ledger import Book
from founders_civ.runner import run,write_package
from founders_civ.server import WEB

ROOT=Path(__file__).resolve().parents[1]

class CanonCoverage(unittest.TestCase):
 def test_unique_system_entries_and_statuses(self):
  self.assertEqual(len(SYSTEMS),25)
  self.assertEqual(len({r['id'] for r in SYSTEMS}),25)
  self.assertTrue(all(r['status'] in ('operational','partial','specified','experimental') for r in SYSTEMS))
  self.assertTrue(all(all(r.get(k) for k in ('group','name','canon','code','gap')) for r in SYSTEMS))
 def test_speculative_rules_never_labeled_operational(self):
  for name in ('founders','soul_hierarchy','evolution','maintained_constructs'):
   self.assertEqual(next(r['status'] for r in SYSTEMS if r['id']==name),'specified')
 def test_registered_factorial_design_is_not_marked_executed(self):
  self.assertEqual(EXPERIMENT['registered_arms']*EXPERIMENT['registered_seeds'],480)
  self.assertEqual(EXPERIMENT['status'],'planned_not_executed')
 def test_toll_parameters_explicitly_provisional(self):
  self.assertEqual(TOLL['status'],'experimental')
 def test_live_sample_metadata(self):
  x=json.loads((WEB/'sample_run.json').read_text(encoding='utf8'))
  self.assertEqual(x['configuration']['arm'],'1111')
  self.assertEqual(x['configuration']['seed'],42)
  self.assertEqual(x['frames'][-1]['day'],30)
  self.assertEqual(len(x['systems']),25)
  self.assertEqual(len(x['actors']),286)

class EngineViews(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.a=run(42,3,'1111');cls.b=run(42,3,'1111')
 def test_reproducible_snapshots(self):
  self.assertEqual(self.a['frames'],self.b['frames'])
  self.assertEqual(self.a['results'],self.b['results'])
 def test_living_actor_roster_and_frames(self):
  self.assertEqual(len(self.a['frames']),4)
  self.assertEqual(len(self.a['actors']),286)
  self.assertTrue(all(len(f['actors'])==286 for f in self.a['frames']))
 def test_need_scores_are_recorded_in_snapshots(self):
  row=self.a['frames'][1]['actors'][12]
  self.assertEqual(len(row),13)
  self.assertTrue(all(0<=row[i]<=100 for i in (4,8,9,10,11)))
 def test_multiple_habitat_patches_not_new_material(self):
  self.assertEqual(len(self.a['frames'][0]['patches']),8)
  self.assertEqual(len(self.a['frames'][3]['patches']),8)
 def test_physical_balances(self):
  report=self.a['audit']
  self.assertLess(abs(report['mass_error']),1e-6)
  self.assertLess(abs(report['energy_error']),1e-5)
  self.assertGreater(report['transactions'],0)
  self.assertGreater(report['toll_events'],0)
 def test_source_relations_and_events(self):
  self.assertTrue(any(e['type']=='family' for e in self.a['edges']))
  self.assertTrue(any(x.get('action') in ('harvest','ritual','teach','pledge_deposit') for x in self.a['events']))
 def test_export_files(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(write_package(self.a,t))
   self.assertTrue(p.exists());self.assertTrue((p.parent/'daily.csv').exists())
   self.assertEqual(json.loads(p.read_text())['configuration']['seed'],42)
 def test_invalid_cli_parameters(self):
  for opts in ((42,0,'1111'),(42,31,'10xx'),(10**12,1,'1111')):
   with self.assertRaises(ValueError):run(*opts)

class VisualContract(unittest.TestCase):
 def test_ui_has_required_live_controls(self):
  html=(WEB/'index.html').read_text()
  for widget in ('world-map','trend-chart','day-slider','inspector','event-list','institutions','system-list','run-btn'):
   self.assertIn('id="'+widget+'"',html)
 def test_animation_discloses_schematic_coordinates(self):
  js=(WEB/'app.js').read_text()
  self.assertIn('illustrative',js)
  self.assertIn('requestAnimationFrame',js)
  self.assertIn('dataset.frames',js)
 def test_windows_launchers_exist(self):
  self.assertTrue((ROOT/'START_DASHBOARD.bat').exists())
  self.assertTrue((ROOT/'RUN_TESTS.bat').exists())

if __name__=='__main__':unittest.main()
