"""Focused correctness checks for local population controls and checkpoints."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from habitat_bridge import SPECIES
from trophic_guilds_cycle138 import GUILD_FOUNDERS
from core_completion_143 import UnifiedCoreCompletion143
from run_local_core143 import BASE_CORE, DEFAULT_TOTAL, ALL_SPECIES, custom_counts, distribute_animals

HERE=Path(__file__).resolve().parent
RUN=HERE/'run_local_core143.py'


def execute(*args):
    env=dict(os.environ, PYTHONHASHSEED='0', PYTHONPATH=os.pathsep.join((str(HERE/'src'),str(HERE/'world023024'))))
    return subprocess.run([sys.executable, str(RUN), *map(str,args)],
                          cwd=HERE,env=env, text=True, capture_output=True,timeout=75)

class PopulationControls(unittest.TestCase):
    def test_reference_counts(self):
        self.assertEqual(sum(distribute_animals(DEFAULT_TOTAL).values()),DEFAULT_TOTAL)
        self.assertEqual(distribute_animals(DEFAULT_TOTAL),{**BASE_CORE,**GUILD_FOUNDERS})
        self.assertEqual(sum(distribute_animals(40).values()),40)
        self.assertEqual(sum(distribute_animals(80).values()),80)
        self.assertEqual(len(ALL_SPECIES),13)

    def test_validation_minimum_and_sex_pairs(self):
        with self.assertRaises(ValueError):distribute_animals(39)
        with self.assertRaises(ValueError):custom_counts(['ridge_hound=7'])
        with self.assertRaises(ValueError):custom_counts(['ridge_hound=9'])
        with self.assertRaises(ValueError):custom_counts(['made_up=5'])

    def test_start_run_and_replay_from_checkpoint(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            straight=root/'straight'; divided=root/'divided'
            x=execute('--days', '5', '--animals','40','--seed','100003',
                      '--report-every','1','--checkpoint-every','2','--output',straight,'--quiet')
            self.assertEqual(x.returncode,0,msg=x.stderr)
            y=execute('--days','3','--animals','40','--seed','100003',
                      '--report-every','1','--checkpoint-every','2','--output',divided,'--quiet')
            self.assertEqual(y.returncode,0,msg=y.stderr)
            z=execute('--days','2','--resume',divided/'latest_checkpoint.pkl',
                      '--report-every','1','--output',divided,'--quiet')
            self.assertEqual(z.returncode,0,msg=z.stderr)
            r1=json.loads((straight/'summary.json').read_text())
            r2=json.loads((divided/'summary.json').read_text())
            self.assertEqual(r1['final']['day'],5)
            self.assertEqual(r2['final']['day'],5)
            keys=['bridge_living','native_living','world_state','book_transactions',
                  'g1_births','g2_births','mass_residual','energy_residual']
            self.assertEqual({k:r1['final'][k] for k in keys},{k:r2['final'][k] for k in keys})
            with (divided/'timeline.csv').open(newline='') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual([int(x['day']) for x in rows],list(range(6)))
            self.assertEqual(r1['final']['book_rejections'],0)

    def test_failed_underfunded_megaherbivore_not_minted(self):
        with tempfile.TemporaryDirectory() as root:
            res=execute('--days','0','--species','forest_elephant=2','--output',root)
            self.assertEqual(res.returncode,2)
            self.assertIn('insufficient REAL plant and chemical stocks',res.stderr)

if __name__=='__main__':unittest.main()
