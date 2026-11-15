import unittest,tempfile,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integrity_audit_02164 import audit
class TestAudit(unittest.TestCase):
 def test_reports_actual_drift(self):
  root=Path(__file__).resolve().parents[2];r=audit(root)
  self.assertIn('founders_civ/experimental/world_trees.py',r['fingerprint_changed'])
  self.assertEqual(set(r['fingerprint_changed']),{'founders_civ/experimental/world_trees.py','founder_world.html'})
 def test_missing_modules_not_silently_patched(self):
  r=audit(Path(__file__).resolve().parents[2]);self.assertEqual(r['missing_source_dependencies'],[])
 def test_no_mutation(self):
  root=Path(__file__).resolve().parents[2];a=audit(root);self.assertEqual(a,audit(root))
