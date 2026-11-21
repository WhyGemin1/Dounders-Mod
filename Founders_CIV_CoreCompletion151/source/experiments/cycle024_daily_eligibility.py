"""Read-only actual-state demographic eligibility census; does not mutate Book."""
from collections import Counter
from species_life_02115 import PROFILES, MASS_SCALE, YEAR

def snapshot(sim):
    bridge=sim.bridge
    animals=tuple(a for a in bridge.actors.values() if a.alive)
    counts=Counter()
    by_species={}
    for species, profile in PROFILES.items():
        group=[a for a in animals if a.species==species]
        mature=[a for a in group if a.stage=='adult' and a.age>=profile.maturity]
        eligible=[a for a in mature if a.condition>=.65]
        males=[a for a in eligible if a.sex=='M']
        females=[a for a in eligible if a.sex=='F']
        funded=[a for a in females if bridge.book.mass[bridge.physical.maternal(a)]+1e-12>=profile.birth_cost*MASS_SCALE]
        pairs=sum(any(m.habitat==f.habitat or m.habitat in bridge.tree.habitats[f.habitat].neighbors for m in males) for f in funded)
        season=profile.breeding[0]<=bridge.day%YEAR<=profile.breeding[1]
        by_species[species]={'living':len(group),'adult':len(mature),'condition_eligible_male':len(males),'condition_eligible_female':len(females),'maternal_funded_female':len(funded),'colocated_funded_pairs':pairs,'season_open':bool(season),'season_eligible_pairs':pairs if season else 0}
        for key in ('condition_eligible_male','condition_eligible_female','maternal_funded_female','colocated_funded_pairs'):
            counts[key]+=by_species[species][key] if season else 0
    return {'day':int(getattr(sim,'days',0)),'bridge_day':int(bridge.day),'condition_eligible_male':counts['condition_eligible_male'],'condition_eligible_female':counts['condition_eligible_female'],'maternal_funded_female':counts['maternal_funded_female'],'colocated_funded_pairs':counts['colocated_funded_pairs'],'species':by_species,'semantics':'season-gated aggregates; species values are ungated'}
