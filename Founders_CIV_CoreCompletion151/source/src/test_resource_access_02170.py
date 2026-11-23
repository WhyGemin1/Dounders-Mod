import unittest
from integrated_02170 import Unified270

class ResourceAccessTests(unittest.TestCase):
    def test_same_authoritative_book(self):
        s=Unified270(seed=9711)
        self.assertIs(s.bridge.book,s.host.book)
        self.assertIs(s.bridge.tree.book,s.host.book)
    def test_disabled_control(self):
        s=Unified270(seed=9711,resource_access=False)
        self.assertFalse(s.resource_access)
        s.step();self.assertEqual(s.bridge.resource_access_metrics['guided_moves'],0)
    def test_abundant_food_preserves_baseline_fallback(self):
        from unittest.mock import patch
        from resource_access_02170 import ResourceAccessBridge270
        s=Unified270(seed=9711)
        b=s.bridge
        actor=next(a for a in b.actors.values() if a.species not in ('ridge_hound','carrion_bird') and a.stage!='dependent')
        here=actor.habitat
        source=b.physical.plant(actor)
        b.book.mass[source]=max(b.book.mass[source],.23)
        with patch.object(ResourceAccessBridge270.__mro__[1], '_migrate', return_value=True) as fallback:
            b._migrate(actor,'feed')
            fallback.assert_called_once_with(actor,'feed')

    def test_no_gradient_preserves_baseline_fallback(self):
        from unittest.mock import patch
        from resource_access_02170 import ResourceAccessBridge270
        s=Unified270(seed=9711)
        b=s.bridge
        actor=next(a for a in b.actors.values() if a.species not in ('ridge_hound','carrion_bird') and a.stage!='dependent')
        source=b.physical.plant(actor)
        b.book.mass[source]=max(b.book.mass[source],100.)
        with patch.object(ResourceAccessBridge270.__mro__[1], '_migrate', return_value=True) as fallback:
            b._migrate(actor,'feed')
            fallback.assert_called_once_with(actor,'feed')

    def test_conservation(self):
        s=Unified270(seed=9711)
        for _ in range(5):s.step()
        audit=s.host.book.audit()
        self.assertLess(abs(audit['mass_error']),1e-6)
        self.assertLess(abs(audit['energy_error']),1e-6)
if __name__=='__main__':unittest.main()
