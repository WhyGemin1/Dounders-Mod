import unittest
from unittest.mock import patch
from reproduction_02185 import ReproductiveBridge285

class TestGrazing(unittest.TestCase):
    def test_second_meal_only_for_enabled_juvenile(self):
        animal=type('Animal',(),{'species':'field_mouse','stage':'juvenile'})()
        b=object.__new__(ReproductiveBridge285)
        b.compensatory_grazing=True
        with patch('reproduction_02184.ReproductiveBridge284._feed_herbivore',return_value=True) as feed:
            self.assertTrue(b._feed_herbivore(animal))
            self.assertEqual(feed.call_count,2)
    def test_disabled_meal_once(self):
        animal=type('Animal',(),{'species':'field_mouse','stage':'juvenile'})()
        b=object.__new__(ReproductiveBridge285)
        b.compensatory_grazing=False
        with patch('reproduction_02184.ReproductiveBridge284._feed_herbivore',return_value=True) as feed:
            self.assertTrue(b._feed_herbivore(animal))
            self.assertEqual(feed.call_count,1)
    def test_no_second_meal_after_failed_first(self):
        animal=type('Animal',(),{'species':'field_mouse','stage':'juvenile'})()
        b=object.__new__(ReproductiveBridge285)
        b.compensatory_grazing=True
        with patch('reproduction_02184.ReproductiveBridge284._feed_herbivore',return_value=False) as feed:
            self.assertFalse(b._feed_herbivore(animal))
            self.assertEqual(feed.call_count,1)
if __name__=='__main__': unittest.main()
