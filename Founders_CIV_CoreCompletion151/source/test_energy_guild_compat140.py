import unittest
from collections import Counter
from energy_guild_compat140 import UnifiedGuildEnergy140
from trophic_guilds_cycle138 import UnifiedTrophicGuild138
from eco_factorial_cycle138 import EcoBridge138

KW=dict(seed=100001,counts={s:8 for s in ('field_mouse','meadow_grazer','forest_browser','ridge_hound','carrion_bird')},
        metabolism=True, spatial=True, juvenile=True)

def trial(E,G):return UnifiedGuildEnergy140(energy_conservation=E,expanded_food_web=G,**KW)

class Compat(unittest.TestCase):
 def test_alloff_unchanged(self):
  a=UnifiedTrophicGuild138(expanded_food_web=False,**KW)
  b=trial(False,False)
  for _ in range(3):a.step();b.step()
  self.assertEqual(a.host.book.audit(),b.host.book.audit())
  self.assertEqual(a.bridge.report(),b.bridge.report())
 def test_four_combinations_one_book(self):
  for E in (False,True):
   for G in (False,True):
    with self.subTest(E=E,G=G):
     s=trial(E,G)
     assert s.host.book is s.bridge.book is s.bridge.tree.book
     for _ in range(3):s.step()
     audit=s.host.book.audit()
     self.assertEqual(audit['rejections'],0)
     if G:self.assertEqual(s.bridge.guild_metrics['funded_founders'],28)
     if E:self.assertGreater(s.bridge.conservation_metrics['maintenance_paid'],0)
 def test_rest_lower_than_search_on_guild(self):
  s=trial(True,True);a=next(a for a in s.bridge.actors.values() if a.species=='burrow_rabbit' and a.alive)
  acct=s.bridge.physical.reserve(a)
  s.bridge.needs_last[a.id]='rest';before=s.host.book.energy[acct];s.bridge._metabolize(a);low=before-s.host.book.energy[acct]
  s.bridge.needs_last[a.id]='search';before=s.host.book.energy[acct];s.bridge._metabolize(a);high=before-s.host.book.energy[acct]
  self.assertGreater(high,low)
if __name__=='__main__':unittest.main()
