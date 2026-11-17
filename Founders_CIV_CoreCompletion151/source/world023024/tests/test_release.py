from __future__ import annotations
import unittest, sys, json, subprocess, os
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from founders_civ.core.ledger import Book
from founders_civ.core.engine import Simulation
from founders_civ.observatory import ObservatorySimulation
from founders_civ.runner import run,write_package
from founders_civ.canon import SYSTEMS

class CanonTests(unittest.TestCase):
    def test_registry_coverage(self):
        self.assertGreaterEqual(len(SYSTEMS),18)
        self.assertEqual(len(set(x['id'] for x in SYSTEMS)),len(SYSTEMS))
        for rule in SYSTEMS:
            self.assertIn(rule['status'],('operational','partial','specified','experimental'))
            self.assertTrue(rule['canon'] and rule['gap'] and rule['code'])

    def test_unimplemented_rules_are_not_marked_operational(self):
        for key in ('founders','soul_hierarchy'):
            self.assertEqual(next(x for x in SYSTEMS if x['id']==key)['status'],'specified')

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.book=Book();b=self.book
        b.seed_mass('living:tree',12);b.seed_mass('felled:tree',0)
        b.seed_energy('reserve',100);b.seed_energy('world_toll',0)
        b.seed_energy('underworld:0',0);b.seed_energy('house',0);b.freeze()

    def test_owner_move_has_no_toll(self):
        b=self.book;b.move(material=[('living:tree','living:owner-2',1)])
        self.assertEqual(b.toll_count,0)
        self.assertEqual(b.audit()['mass_total'],12)

    def test_cannot_disguise_material_change_as_move(self):
        with self.assertRaisesRegex(ValueError,'material-state change'):
            self.book.move(material=[('living:tree','felled:tree',1)])

    def test_real_transformation_pays_one_toll(self):
        b=self.book;b.transform([('living:tree','felled:tree',2)],'reserve',10,[('reserve','heat',9)])
        self.assertEqual(b.toll_count,1)
        self.assertAlmostEqual(b.energy['house'],.7)
        self.assertAlmostEqual(b.energy['underworld:0'],.1)
        b.audit()

    def test_unfunded_operation_rolls_back(self):
        b=self.book;before=(dict(b.mass),dict(b.energy),b.seq)
        with self.assertRaises(ValueError):b.move(material=[('living:tree','felled:tree',10000)])
        self.assertEqual(before,(dict(b.mass),dict(b.energy),b.seq))

class ObservatoryTests(unittest.TestCase):
    def test_snapshot_is_read_only(self):
        sim=ObservatorySimulation(seed=8,days=2,arm='1111',trace=True)
        before=(dict(sim.book.mass),dict(sim.book.energy),len(sim.actors))
        sim.capture();sim.capture()
        self.assertEqual(before,(dict(sim.book.mass),dict(sim.book.energy),len(sim.actors)))

    def test_export_frame_schema_and_accounts(self):
        d=run(8,2,'1111')
        self.assertEqual(len(d['frames']),3)
        self.assertEqual(len(d['actors']),286)
        self.assertEqual(len(d['frames'][0]['actors']),len(d['actors']))
        self.assertAlmostEqual(d['audit']['energy_error'],0,delta=.0001)
        self.assertAlmostEqual(d['audit']['mass_error'],0,delta=.0001)
        self.assertEqual(d['results']['days'],2)
        self.assertEqual(len(d['frames'][2]['patches']),8)

    def test_same_seed_identical(self):
        a=run(42,2,'1111');b=run(42,2,'1111')
        self.assertEqual(a['frames'],b['frames']);self.assertEqual(a['events'],b['events'])

    def test_experiments_are_configurable(self):
        a=run(42,2,'0000');b=run(42,2,'1111')
        self.assertEqual(a['configuration']['arm'],'0000')
        self.assertEqual(b['configuration']['arm'],'1111')
        self.assertEqual(a['frames'][0]['patches'],b['frames'][0]['patches'])
        self.assertNotEqual(a['events'],b['events'])

    def test_boundaries(self):
        for bad in (0,721):
            with self.assertRaises(ValueError):run(1,bad,'1111')
        with self.assertRaises(ValueError):run(42,2,'1X11')

    def test_origin_provenance(self):
        d=run(42,15,'1111')
        for e in d['events']:
            if e['action']=='teach':
                self.assertIn('source_id',e);self.assertTrue(e['source_id'] in d['actors'])
                break
        else:self.fail('no teaching event found in pilot')

    def test_export_file_roundtrip(self):
        import tempfile
        d=run(3,1,'1111')
        with tempfile.TemporaryDirectory() as tmp:
            path=write_package(d,tmp)
            x=json.loads(Path(path).read_text())
            self.assertEqual(x['schema'],'founders-civ-observatory/1.0')
            self.assertTrue((Path(tmp)/'daily.csv').exists())

    def test_dashboard_assets_present(self):
        for name in ('index.html','app.js','styles.css','sample_run.json'):
            self.assertTrue((ROOT/'web'/name).is_file())
        sample=json.loads((ROOT/'web'/'sample_run.json').read_text())
        self.assertEqual(sample['results']['days'],30)

if __name__=='__main__':unittest.main()
