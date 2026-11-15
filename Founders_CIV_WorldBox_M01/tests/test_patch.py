import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apply_to_worldbox_bridge import apply,TARGET,ADDED,REL
class InstallerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.repo=Path(self.tmp.name)
  self.plugin=self.repo/'mod/src/WorldBoxBridge/Plugin.cs'
  self.query=self.repo/'mod/src/WorldBoxBridge/Commands/Read/QueryActorsCommand.cs'
  self.query.parent.mkdir(parents=True)
  self.plugin.write_text('using WorldBoxBridge.Commands.Read;\n'+TARGET+'\n')
  self.query.write_text('fake fixture for static installer test')
 def tearDown(self):self.tmp.cleanup()
 def test_applies_once_and_preserves_backup(self):
  out=apply(self.repo)
  self.assertIn('patched',out)
  self.assertTrue((self.repo/REL).exists())
  self.assertEqual(self.plugin.read_text().count(ADDED),1)
  self.assertIn(TARGET,self.plugin.with_name('Plugin.cs.M01_backup').read_text())
  self.assertEqual(apply(self.repo),'already applied')
 def test_refuses_upstream_drift(self):
  self.plugin.write_text('no expected marker')
  with self.assertRaises(ValueError):apply(self.repo)
 def test_refuses_modified_extension(self):
  (self.repo/REL).write_text('other data')
  with self.assertRaises(ValueError):apply(self.repo)
if __name__=='__main__':unittest.main()
