"""Read-only reproductive gate diagnostics; never modifies Book or actor state."""
from collections import Counter
from species_life_02115 import PROFILES, MASS_SCALE, YEAR

def trace_hound_gates(bridge):
    p=PROFILES['ridge_hound']
    h=[a for a in bridge.actors.values() if a.alive and a.species=='ridge_hound']
    males=[a for a in h if a.sex=='M']
    females=[a for a in h if a.sex=='F']
    out=Counter(population=len(h), females=len(females), males=len(males))
    out['season_open']=int(p.breeding[0]<=bridge.day%YEAR<=p.breeding[1])
    for f in females:
        if f.age<p.maturity or f.stage!='adult':out['female_immature']+=1;continue
        if f.condition<.65:out['female_low_condition']+=1;continue
        if bridge.book.mass[bridge.physical.maternal(f)]+1e-12<p.birth_cost*MASS_SCALE:
            out['female_low_maternal_stock']+=1;continue
        out['female_ready']+=1
        eligible=[m for m in males if m.age>=p.maturity and m.stage=='adult' and m.condition>=.65]
        if not eligible:out['ready_without_eligible_male']+=1;continue
        if not any(m.habitat==f.habitat or m.habitat in bridge.tree.habitats[f.habitat].neighbors for m in eligible):
            out['ready_without_local_male']+=1;continue
        out['local_ready_females']+=1
    return dict(out)
