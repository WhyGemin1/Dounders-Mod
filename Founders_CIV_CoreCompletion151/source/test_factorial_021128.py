import unittest,tempfile,json
from pathlib import Path
from factorial_021126 import configuration
from factorial_021128 import run_verified
class VerifiedMilestones(unittest.TestCase):
 def test_ordering(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   for days in ([2,1],[1,1],[0],[]):
    with self.assertRaises(ValueError):run_verified(c,days,d)
 def test_journal_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   run_verified(c,[1],d)
   j=next(Path(d).glob('*.jsonl'));r=json.loads(j.read_text());r['day']=0;j.write_text(json.dumps(r)+'\n')
   with self.assertRaisesRegex(ValueError,'divergence'):run_verified(c,[2],d)
 def test_resume(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,funded=False,family=False,memory=False)
   run_verified(c,[1],d);r=run_verified(c,[2],d)
   self.assertEqual(r[-1]['day'],2)
if __name__=='__main__':unittest.main()
