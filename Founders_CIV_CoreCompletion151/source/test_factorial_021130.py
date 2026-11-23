import json,tempfile,unittest
from pathlib import Path
from factorial_021126 import configuration
from factorial_021130 import run_with_snapshots
from factorial_021130 import replay_verified,verified_snapshot,snapshot_key
class Tests(unittest.TestCase):
 def test_verified_replay(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   rows=run_with_snapshots(c,[1,2],d)
   self.assertEqual(replay_verified(c,1,2,d)['living'],rows[-1]['living'])
 def test_tampered_snapshot_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   run_with_snapshots(c,[1],d)
   p=Path(d)/(snapshot_key(c)+'.day1.pkl');p.write_bytes(p.read_bytes()+b'X')
   with self.assertRaises(ValueError):verified_snapshot(c,1,d)
 def test_mismatched_journal_tick_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   run_with_snapshots(c,[1],d)
   p=Path(d)/(snapshot_key(c)+'.day1.clock.json');r=json.loads(p.read_text());r['tick']+=1;p.write_text(json.dumps(r)+'\n')
   with self.assertRaises(ValueError):verified_snapshot(c,1,d)
if __name__=='__main__':unittest.main()
