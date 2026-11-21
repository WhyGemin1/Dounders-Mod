"""Experimental read-only cohort bottleneck audit; no demographic scheduler changes."""
from species_life_02115 import PROFILES

def cohort_audit(sim):
    bridge=sim.bridge; book=sim.host.book; physical=bridge.physical
    rows=[]
    for a in bridge.actors.values():
        if a.generation < 1: continue
        p=PROFILES[a.species]
        mass=book.mass.get(physical.live(a),0.0)
        rows.append(dict(id=str(a.id),species=a.species,generation=a.generation,
                         alive=bool(a.alive),stage=a.stage,age=a.age,
                         maturity_age=p.maturity,age_fraction=a.age/max(p.maturity,1e-12),
                         body_mass=mass,adult_mass=p.adult_mass(),
                         mass_fraction=mass/max(p.adult_mass(),1e-12),
                         habitat=a.habitat))
    living=[r for r in rows if r['alive']]
    return dict(day=sim.days,born=len(rows),living=len(living),dead=len(rows)-len(living),
                g1_adults=sum(r['generation']==1 and r['stage']=='adult' for r in living),
                g2_born=sum(r['generation']>=2 for r in rows),
                age_eligible=sum(r['age_fraction']>=1 for r in living),
                mass_eligible=sum(r['mass_fraction']>=1 for r in living),
                cohorts=rows)
