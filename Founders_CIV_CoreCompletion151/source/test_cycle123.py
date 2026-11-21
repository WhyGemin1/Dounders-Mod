import tempfile,unittest,json
from pathlib import Path
from run_cycle123 import run,atomic_bytes
class DurableTests(unittest.TestCase):
 def test_atomic_replace(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';atomic_bytes(p,b'one');atomic_bytes(p,b'two');self.assertEqual(p.read_bytes(),b'two')
 def test_invalid_horizon(self):
  with self.assertRaises(ValueError):run(1,.5,'/tmp/unused_cycle123',45)
 def test_mismatched_partial_journal_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'seed9711_fraction0.5.jsonl';p.write_text(json.dumps({'seed':123,'floodplain_fraction':.5,'day':30})+'\n')
   with self.assertRaises(AssertionError):run(9711,.5,d,60)
if __name__=='__main__':unittest.main()
