"""C081 source contract: same-object M05 native dual IDs, observational only.

These checks do not prove WorldBox compatibility or live actor identity.
The Windows C# smoke workflow compiles the source against test-only stubs.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "bridge" / "FoundersCIV_M05_Observer.cs"


class M05NativeDualIdentityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_event_carries_unresolved_by_default_native_data_id(self):
        self.assertIn('public string actor_data_id = "";', self.source)
        self.assertIn('public long actor_id = -1;', self.source)

    def test_same_actor_object_used_for_both_ids_on_nutrition_callbacks(self):
        for kind in ("nutrition_call", "resource_consume_call"):
            start = self.source.index('kind="' + kind + '"')
            fragment = self.source[start:start + 340]
            self.assertIn("actor_id=Id(__instance)", fragment)
            self.assertIn("actor_data_id=ActorDataId(__instance)", fragment)

    def test_identity_reads_actor_data_id_without_writing_game_state(self):
        start = self.source.index("private static string ActorDataId(object actor)")
        end = self.source.index("private static int SafeInt(object value)", start)
        body = self.source[start:end]
        self.assertIn('ReadActorMember(actor, "data")', body)
        self.assertIn('ReadActorMember(data, "id")', body)
        self.assertIn('return id == null ? ""', body)
        self.assertIn("CultureInfo.InvariantCulture", body)
        for banned in ("SetValue(", "InvokeMember(", "book.move(", "soul.practice("):
            self.assertNotIn(banned, body)

    def test_cannot_replace_native_authority_or_promote_soul_automatically(self):
        self.assertIn('native_nutrition_change_not_physical_energy', self.source)
        self.assertNotIn('new SoulNetwork(', self.source)


if __name__ == "__main__":
    unittest.main()
