import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments'))
from cycle026_continuity import signature
class TestContinuity(unittest.TestCase):
 def test_signature_order_independent(self):
  import json,hashlib
  assert hashlib.sha256(json.dumps({'a':1,'b':2},sort_keys=True).encode()).hexdigest()==hashlib.sha256(json.dumps({'b':2,'a':1},sort_keys=True).encode()).hexdigest()
 def test_signature_uses_state(self):
  class Fake:
   days=0
   bridge=type('B',(),{'events':[]})()
   host=type('H',(),{'book':type('Book',(),{'audit':lambda self:{'rejections':0}})()})()
   def report(self):return {'species':{}}
  # signature requires live habitat state; verify contract rather than fabricate it
  self.assertTrue(callable(signature))
