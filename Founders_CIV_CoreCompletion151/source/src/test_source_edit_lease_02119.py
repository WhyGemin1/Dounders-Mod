"""Cycle006 source-edit coordination and failure safety tests."""
import tempfile, unittest
from pathlib import Path
from scripts.source_edit_lease import exclusive_source_edit

class TestSourceEditLease(unittest.TestCase):
    def test_exclusive_acquisition_rejects_second_writer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with exclusive_source_edit(root,'test-one'):
                self.assertTrue((root/'.source_edit.lock').is_file())
                with self.assertRaises(RuntimeError):
                    with exclusive_source_edit(root,'test-two'):pass
            self.assertFalse((root/'.source_edit.lock').exists())

    def test_exception_releases_owned_lease(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaisesRegex(ValueError,'synthetic'):
                with exclusive_source_edit(root,'test-exception'):
                    raise ValueError('synthetic')
            with exclusive_source_edit(root,'after-error'):pass
            self.assertFalse((root/'.source_edit.lock').exists())

if __name__=='__main__':unittest.main()
