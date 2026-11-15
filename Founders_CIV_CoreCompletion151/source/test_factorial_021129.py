import unittest,tempfile
from factorial_021126 import configuration
from factorial_021129 import run_with_snapshots,replay_snapshot
class SnapshotTests(unittest.TestCase):
 def test_snapshot_and_replay(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   rows=run_with_snapshots(c,[1,2],d)
   self.assertEqual(replay_snapshot(c,1,2,d)['living'],rows[-1]['living'])
 def test_duplicate_snapshot_fails(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   run_with_snapshots(c,[1],d)
   with self.assertRaises(ValueError):run_with_snapshots(c,[1],d)
if __name__=='__main__':unittest.main()
