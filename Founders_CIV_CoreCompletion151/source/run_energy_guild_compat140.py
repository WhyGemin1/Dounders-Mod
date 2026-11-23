"""2x2 technical compatibility pilot only, not ecological calibration."""
import json,csv
from pathlib import Path
from energy_guild_compat140 import UnifiedGuildEnergy140
from habitat_bridge import SPECIES

rows=[]
for seed in (100001,100002):
 for g in (0,1):
  for e in (0,1):
   s=UnifiedGuildEnergy140(seed=seed,counts={species:8 for species in SPECIES},
      metabolism=True,spatial=True,juvenile=True,expanded_food_web=bool(g),energy_conservation=bool(e))
   for _ in range(30):s.step()
   bk=s.host.book.audit();b=s.bridge
   row=dict(seed=seed,expanded_guilds=g,energy_conservation=e,day=30,
      bridge_living=sum(a.alive for a in b.actors.values()),
      ridge_hound_alive=sum(a.alive and a.species=='ridge_hound' for a in b.actors.values()),
      rabbit_alive=sum(a.alive and a.species=='burrow_rabbit' for a in b.actors.values()),
      rabbit_births=sum(ev.get('event')=='birth' and ev.get('species')=='burrow_rabbit' for ev in b.events),
      book_rejections=bk['rejections'],mass_error=bk['mass_error'],energy_error=bk['energy_error'],
      energy_paid_maintenance=round(b.conservation_metrics['maintenance_paid'],6) if e else 0,
      energy_paid_exertion=round(b.conservation_metrics['exertion_paid'],6) if e else 0)
   rows.append(row)
   print(row,flush=True)
out=Path('/mnt/data/EnergyGuild_Integration_Review');out.mkdir(exist_ok=True)
(out/'compatibility_30d_pilot.json').write_text(json.dumps(rows,indent=2))
with (out/'compatibility_30d_pilot.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
