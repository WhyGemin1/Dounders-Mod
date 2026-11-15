"""A-022: read-only demographic and spatial opportunity accounting; no energy writes."""
from collections import Counter
from species_life_02115 import PROFILES, MASS_SCALE, YEAR

def encounter_opportunities(bridge, species='ridge_hound'):
    p=PROFILES[species]; animals=[a for a in bridge.actors.values() if a.alive and a.species==species]
    out=Counter(population=len(animals), adult=0, female=0, female_maternal_ready=0,
                adjacent_pairs=0, same_habitat_pairs=0, physically_eligible_pairs=0)
    adults=[a for a in animals if a.stage=='adult' and a.age>=p.maturity and a.condition>=.65]
    out['adult']=len(adults);out['female']=sum(a.sex=='F' for a in adults)
    females=[a for a in adults if a.sex=='F'];males=[a for a in adults if a.sex=='M']
    for female in females:
        stock=bridge.book.mass[bridge.physical.maternal(female)]
        ready=stock+1e-12>=p.birth_cost*MASS_SCALE
        out['female_maternal_ready']+=int(ready)
        for male in males:
            same=male.habitat==female.habitat
            adjacent=male.habitat in bridge.tree.habitats[female.habitat].neighbors
            out['same_habitat_pairs']+=int(same)
            out['adjacent_pairs']+=int(adjacent)
            out['physically_eligible_pairs']+=int(ready and (same or adjacent))
    out['in_breeding_season']=int(p.breeding[0]<=bridge.day%YEAR<=p.breeding[1])
    return dict(out)
