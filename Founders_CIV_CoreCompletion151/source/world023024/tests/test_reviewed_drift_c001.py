"""U026-C001 tests: exact reviewed drift never weakens baseline protection."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from founders_civ.integration.compat import (TRACKED, fingerprint, check,
                                               reviewed_check, ReviewedDriftError)


def sha(data):
    return hashlib.sha256(data.encode('utf8')).hexdigest()


class ReviewedDriftC001Tests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        for path in TRACKED:
            item = self.root/path
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_text('original:'+path, encoding='utf8')
        self.baseline = self.root/'baseline.json'
        self.baseline.write_text(json.dumps({'hashes':fingerprint(self.root)}))
        self.original_baseline = self.baseline.read_bytes()
        self.approval = self.root/'approved.json'
        self.changed = ('founders_civ/core/ledger.py', 'founders_civ/experimental/world_trees.py')
        changes = {}
        for path in self.changed:
            (self.root/path).write_text('approved:'+path,encoding='utf8')
            changes[path] = {
                'baseline_sha256':json.loads(self.original_baseline)['hashes'][path],
                'approved_sha256':sha('approved:'+path),
                'rationale':'reviewed behavioral source delta',
            }
        self.manifest = {'schema':'founders-civ-reviewed-drift-v1','approved_changes':changes}
        self.save_review()

    def save_review(self):
        self.approval.write_text(json.dumps(self.manifest))

    def test_exact_reviewed_changes_pass(self):
        result=reviewed_check(self.root,self.baseline,self.approval)
        self.assertEqual(result['status'],'approved_drift')
        self.assertEqual(set(result['approved_files']),set(self.changed))
        self.assertEqual(result['unapproved_files'],[])

    def test_unapproved_third_file_rejected(self):
        (self.root/'knowledge_architecture.py').write_text('unauthorized')
        result=reviewed_check(self.root,self.baseline,self.approval)
        self.assertEqual(result['status'],'drift_requires_review')
        self.assertEqual(result['unapproved_files'],['knowledge_architecture.py'])

    def test_modified_approved_file_rejected(self):
        (self.root/self.changed[0]).write_text('tampered')
        self.assertIn(self.changed[0], reviewed_check(self.root,self.baseline,self.approval)['unapproved_files'])

    def test_deleted_tracked_file_rejected(self):
        (self.root/'founder_world.html').unlink()
        self.assertIn('founder_world.html',reviewed_check(self.root,self.baseline,self.approval)['unapproved_files'])

    def test_deleted_approved_file_rejected(self):
        (self.root/self.changed[0]).unlink()
        self.assertIn(self.changed[0],reviewed_check(self.root,self.baseline,self.approval)['unapproved_files'])

    def test_stale_baseline_hash_is_not_accepted(self):
        self.manifest['approved_changes'][self.changed[0]]['baseline_sha256']='0'*64
        self.save_review()
        with self.assertRaises(ReviewedDriftError):
            reviewed_check(self.root,self.baseline,self.approval)

    def test_untracked_approval_fails_schema(self):
        self.manifest['approved_changes']['untracked.py'] = dict(self.manifest['approved_changes'][self.changed[0]])
        self.save_review()
        with self.assertRaises(ReviewedDriftError):
            reviewed_check(self.root,self.baseline,self.approval)

    def test_bad_schema_rejected(self):
        self.manifest['schema']='other-schema'
        self.save_review()
        with self.assertRaises(ReviewedDriftError):
            reviewed_check(self.root,self.baseline,self.approval)

    def test_original_reference_preserved(self):
        reviewed_check(self.root,self.baseline,self.approval)
        self.assertEqual(self.baseline.read_bytes(),self.original_baseline)
        self.assertEqual(check(self.root,self.baseline)['status'],'drift_requires_review')

    def test_clean_tree_still_compatible(self):
        for path in self.changed:
            (self.root/path).write_text('original:'+path)
        self.assertEqual(reviewed_check(self.root,self.baseline,self.approval)['status'],'compatible_fingerprint')

if __name__=='__main__':unittest.main()
