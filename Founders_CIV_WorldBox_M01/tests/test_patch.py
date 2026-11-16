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
 def test_migrates_only_known_missing_namespace_version(self):
  self.assertIn('patched',apply(self.repo))
  source=(self.repo/REL).read_text(encoding='utf8')
  line='using WorldBoxBridge.Commands.Action;' + chr(10)
  self.assertEqual(source.count(line),1)
  legacy=source.replace(line,'')
  (self.repo/REL).write_text(legacy,encoding='utf8')
  output=apply(self.repo)
  self.assertIn('migrated reviewed legacy M01 namespace',output)
  self.assertEqual((self.repo/REL).read_text(encoding='utf8'),source)
  backup=(self.repo/REL).with_name('QueryActorIdentitiesCommand.cs.before-namespace-fix.bak')
  self.assertEqual(backup.read_text(encoding='utf8'),legacy)
  self.assertEqual(self.plugin.read_text().count(ADDED),1)
  self.assertEqual(apply(self.repo),'already applied')
 def test_refuses_unknown_edit_of_legacy_extension(self):
  apply(self.repo)
  source=(self.repo/REL).read_text(encoding='utf8')
  old=source.replace('using WorldBoxBridge.Commands.Action;' + chr(10),'')
  (self.repo/REL).write_text(old+'// local behavioral change'+chr(10),encoding='utf8')
  with self.assertRaisesRegex(ValueError,'refusing to overwrite'):
   apply(self.repo)
 def test_refuses_conflicting_backup_during_namespace_migration(self):
  apply(self.repo)
  source=(self.repo/REL).read_text(encoding='utf8')
  legacy=source.replace('using WorldBoxBridge.Commands.Action;' + chr(10),'')
  (self.repo/REL).write_text(legacy,encoding='utf8')
  backup=(self.repo/REL).with_name('QueryActorIdentitiesCommand.cs.before-namespace-fix.bak')
  backup.write_text('unrelated backup')
  with self.assertRaisesRegex(ValueError,'unexpected bytes'):
   apply(self.repo)
  self.assertEqual((self.repo/REL).read_text(encoding='utf8'),legacy)
if __name__=='__main__':unittest.main()
