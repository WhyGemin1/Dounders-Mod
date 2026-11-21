import tempfile,unittest,json
from pathlib import Path
from factorial_021126 import configuration
from factorial_021127 import run_milestones
class DurableTests(unittest.TestCase):
 def test_journal_and_resume(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   a=run_milestones(c,[1],d);b=run_milestones(c,[2],d)
   self.assertEqual([a[0]['day'],b[0]['day']],[1,2])
   self.assertEqual(len(list(Path(d).glob('*.jsonl'))),1)
 def test_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   run_milestones(c,[1],d)
   p=next(Path(d).glob('*.pkl'))
   with p.open('ab') as f:f.write(b'tamper')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):run_milestones(c,[2],d)
if __name__=='__main__':unittest.main()
