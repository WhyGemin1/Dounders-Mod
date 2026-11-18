"""C066 source-backed escape behavior regression tests."""
import unittest
from collections import Counter
from types import SimpleNamespace
from core_physiology_v2 import PhysiologyBridgeV2
from habitat_bridge import PREY

class EscapeSafetyTests(unittest.TestCase):
    def make_bridge(self, spatial=True):
        predator_species=next(iter(PREY))
        prey_species=next(iter(PREY[predator_species]))
        prey=SimpleNamespace(id="prey",species=prey_species,habitat="h",stage="adult",alive=True)
        predator=SimpleNamespace(id="predator",species=predator_species,habitat="h",stage="adult",alive=True)
        b=object.__new__(PhysiologyBridgeV2)
        b.actors={"prey":prey,"predator":predator}
        b.positions={"prey":("h",1,1),"predator":("h",1,0)}
        b._pos=lambda actor:b.positions[actor.id]
        b._neighbors=lambda pos:[("h",0,1),("h",1,0),("h",2,1)]
        b._refresh_quota=lambda:None
        b._work=lambda *args,**kwargs:True
        b.eco_flags=SimpleNamespace(spatial=spatial)
        b.tree=SimpleNamespace(habitats={"h":SimpleNamespace(neighbors=["other"])})
        b.physiology_metrics=Counter()
        b.day=3
        return b,prey,predator

    def test_escape_never_crosses_habitat_for_food(self):
        b,prey,_=self.make_bridge(spatial=False)
        self.assertFalse(PhysiologyBridgeV2._migrate(b,prey,"escape"))
        self.assertEqual(prey.habitat,"h")

    def test_escape_selects_cell_farther_from_predator(self):
        b,prey,_=self.make_bridge()
        self.assertTrue(PhysiologyBridgeV2._migrate(b,prey,"escape"))
        self.assertEqual(b.positions["prey"],("h",2,1))

    def test_escape_without_predator_does_not_seek_food(self):
        b,prey,_=self.make_bridge()
        b.actors.pop("predator")
        self.assertFalse(PhysiologyBridgeV2._migrate(b,prey,"escape"))
        self.assertEqual(b.positions["prey"],("h",1,1))

    def test_large_animal_escape_bypasses_routine_migration_cooldown(self):
        from unittest.mock import patch
        b,prey,_=self.make_bridge()
        calls=[]
        b._neighbors=lambda pos:(calls.append(pos) or [("h",0,1),("h",1,0),("h",2,1)])
        # Force this actor into the large-animal policy without altering
        # global species definitions; day 3 is outside its 9-day interval.
        with patch("core_physiology_v2.MEGA", {prey.species}), patch(
            "core_physiology_v2.ALLOWED_HABITATS", {prey.species: {"h"}}
        ):
            self.assertTrue(PhysiologyBridgeV2._migrate(b,prey,"escape"))
        self.assertEqual(len(calls),1)
        self.assertEqual(b.positions["prey"],("h",2,1))

    def test_large_animal_routine_migration_still_obeys_cooldown(self):
        from unittest.mock import patch
        b,prey,_=self.make_bridge()
        b._neighbors=lambda pos:self.fail("routine movement bypassed cooldown")
        with patch("core_physiology_v2.MEGA", {prey.species}), patch(
            "core_physiology_v2.ALLOWED_HABITATS", {prey.species: {"h"}}
        ):
            self.assertFalse(PhysiologyBridgeV2._migrate(b,prey,"search"))

if __name__=="__main__":
    unittest.main()
