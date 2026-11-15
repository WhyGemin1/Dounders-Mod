"""U026-C002: exact source hash approvals while retaining prior gates."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from founders_civ.integration.compat import TRACKED, reviewed_check, check

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/INTEGRATION_025/BASELINE_HASHES.json'
C001=ROOT/'docs/INTEGRATION_025/APPROVED_DRIFT_C001.json'
C002=ROOT/'docs/INTEGRATION_025/APPROVED_DRIFT_C002.json'
C003=ROOT/'docs/INTEGRATION_025/APPROVED_DRIFT_C003.json'
C004=ROOT/'docs/INTEGRATION_025/APPROVED_DRIFT_C004.json'
C015=ROOT/'docs/INTEGRATION_025/APPROVED_DRIFT_C015.json'
C016=ROOT/'docs/INTEGRATION_025/APPROVED_DRIFT_C016.json'
C017=ROOT/'docs/INTEGRATION_025/APPROVED_DRIFT_C017.json'


class C002ProvenanceTests(unittest.TestCase):
    def test_c017_candidate_exact_attestation_passes(self):
        r=reviewed_check(ROOT,BASE,C017)
        self.assertEqual(r['status'],'approved_drift')
        self.assertEqual(set(r['approved_files']),{
            'founders_civ/core/ledger.py','founders_civ/experimental/world_trees.py',
            'founders_civ/experimental/world_integration.py'})
        self.assertEqual(r['unapproved_files'],[])

    def test_c015_attestation_rejects_updated_scheduler(self):
        r=reviewed_check(ROOT,BASE,C015)
        self.assertEqual(r['status'], 'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py', r['unapproved_files'])

    def test_c016_attestation_rejects_updated_scheduler(self):
        r=reviewed_check(ROOT,BASE,C016)
        self.assertEqual(r['status'], 'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py', r['unapproved_files'])

    def test_c004_approval_is_stale_after_c015(self):
        r=reviewed_check(ROOT,BASE,C004)
        self.assertEqual(r['status'],'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py',r['unapproved_files'])

    def test_c003_approval_is_stale_after_c004(self):
        r=reviewed_check(ROOT,BASE,C003)
        self.assertEqual(r['status'],'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_integration.py',r['unapproved_files'])

    def test_c002_approval_is_stale_after_c003(self):
        r=reviewed_check(ROOT,BASE,C002)
        self.assertEqual(r['status'],'drift_requires_review')
        self.assertIn('founders_civ/experimental/world_trees.py',r['unapproved_files'])

    def test_previous_approval_is_not_reused_after_new_code(self):
        r=reviewed_check(ROOT,BASE,C001)
        self.assertEqual(r['status'],'drift_requires_review')
        self.assertIn('founders_civ/core/ledger.py',r['unapproved_files'])

    def test_reference_manifest_unchanged(self):
        assert json.loads(BASE.read_text())['hashes']['founders_civ/core/ledger.py']==(
            '8c2e859c1227690a15bceb7504c69c3cfa44218a49e84e35b47505c25629112a')
        self.assertEqual(check(ROOT,BASE)['status'],'drift_requires_review')

    def test_unauthorized_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            tr=Path(temp)
            for name in TRACKED:
                dst=tr/name;dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes((ROOT/name).read_bytes())
            (tr/'knowledge_architecture.py').write_text('tampered')
            r=reviewed_check(tr,BASE,C017)
            self.assertEqual(r['status'],'drift_requires_review')
            self.assertIn('knowledge_architecture.py',r['unapproved_files'])

    def test_missing_tracked_file_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            tr=Path(temp)
            for name in TRACKED:
                if name!='founder_world.html':
                    dst=tr/name;dst.parent.mkdir(parents=True,exist_ok=True)
                    dst.write_bytes((ROOT/name).read_bytes())
            r=reviewed_check(tr,BASE,C017)
            self.assertIn('founder_world.html',r['unapproved_files'])

if __name__=='__main__':unittest.main()
