import unittest
from unittest.mock import patch
from integrated_02170 import Unified270
from resource_access_02170 import ResourceAccessBridge270
class PressureTests(unittest.TestCase):
 def test_shared_book_and_metrics(self):
  s=Unified270(seed=9711);self.assertIs(s.host.book,s.bridge.book)
  self.assertEqual(s.bridge.resource_access_metrics['pressure_moves'],0)
 def test_pressure_fallback_if_abundant(self):
  s=Unified270(seed=9711);b=s.bridge
  a=next(x for x in b.actors.values() if x.species=='field_mouse' and x.stage!='dependent')
  acct=b.physical.plant(a)
  # This is an isolated policy unit test, not a physical transaction.
  with patch.dict(b.book.mass,{acct:100.0}):
   with patch.object(ResourceAccessBridge270.__mro__[1],'_migrate',return_value=False) as f:
    b._migrate(a,'feed');f.assert_called_once()
