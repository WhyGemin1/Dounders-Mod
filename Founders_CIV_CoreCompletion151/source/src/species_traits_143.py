"""Cycle143 individual hereditary functional traits for all 13 bridge species.

Non-energy state; no hidden calories, survival subsidies or actor-owned time.
Values are deliberately SYNTHETIC hypotheses, not empirical measurements.
Each blueprint describes a functional niche and constrains individual variation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import isfinite

FIELDS=('basal','digestion','locomotion','endurance','sense','intake','vigilance','reproductive')
LIMITS={
    'basal':(.75,1.40), 'digestion':(.74,1.26),
    'locomotion':(.75,1.40), 'endurance':(.75,1.40),
    'sense':(.75,1.45), 'intake':(.75,1.45),
    'vigilance':(.75,1.45), 'reproductive':(.75,1.35)
}

@dataclass(frozen=True)
class Phenotype143:
    basal: float=1.
    digestion: float=1.
    locomotion: float=1.
    endurance: float=1.
    sense: float=1.
    intake: float=1.
    vigilance: float=1.
    reproductive: float=1.
    def __post_init__(self):
        for name in FIELDS:
            v=getattr(self,name);low,high=LIMITS[name]
            if not isfinite(v) or not low<=v<=high:
                raise ValueError('out-of-bound physiological trait '+name)
    def asdict(self):return asdict(self)

# These are mechanisms/niche hypotheses, not species measurements. Traits below
# affect rates and costs in the actual bridge implementation, NOT only metadata.
BLUEPRINTS={
 'field_mouse':       (.94,1.05,1.04,1.02,1.01,1.12,1.14,1.10),
 'meadow_grazer':     (1.,1.08,1.04,1.13,.95,1.10,1.08,.99),
 'forest_browser':    (1.03,1.07,.97,1.13,1.05,1.09,1.02,.97),
 'ridge_hound':       (1.07,1.12,1.16,1.19,1.14,1.08,.95,.89),
 'carrion_bird':      (.99,1.13,1.14,1.03,1.20,1.02,.94,.95),
 'burrow_rabbit':     (.93,1.07,1.12,1.09,1.13,1.16,1.22,1.16),
 'field_vole':        (.92,1.04,1.05,1.02,1.03,1.13,1.16,1.22),
 'ant_colony':        (.88,1.12,.83,1.12,1.11,1.11,1.12,1.17),
 'insectivore_shrew': (1.08,1.18,1.17,1.03,1.15,1.22,1.13,1.08),
 'red_fox':          (1.01,1.15,1.14,1.15,1.20,1.10,1.12,.94),
 'golden_jackal':    (1.00,1.14,1.16,1.20,1.18,1.10,1.10,.98),
 'forest_elephant':  (1.03,1.12,.81,1.22,.93,1.30,1.10,.78),
 'woolly_mammoth':   (1.08,1.11,.79,1.27,.94,1.33,1.09,.77),
}
assert all(len(v)==len(FIELDS) for v in BLUEPRINTS.values())
assert all(all(LIMITS[f][0]<=v<=LIMITS[f][1] for f,v in zip(FIELDS,row)) for row in BLUEPRINTS.values())

def founder_phenotype(species,rng):
    """Small, seeded founder variation; differences initially non-adaptive."""
    values=BLUEPRINTS[species]
    return Phenotype143(**{f:max(LIMITS[f][0],min(LIMITS[f][1],v*(1.+rng.uniform(-.045,.045))))
                           for f,v in zip(FIELDS,values)})

def descendant_phenotype(species,mother,father,rng,mutation=.025):
    """Biparental heritability + bounded non-directed variation (no fitness bonus)."""
    if mother is None:raise ValueError('offspring require mother')
    base=BLUEPRINTS[species]
    values={}
    for i,f in enumerate(FIELDS):
        maternal=getattr(mother,f)
        paternal=getattr(father,f) if father is not None else base[i]
        # Per-trait parental transmission, rather than copying the species mean.
        inherited=maternal if rng.random()<.5 else paternal
        v=inherited*(1.+rng.uniform(-mutation,mutation))
        low,high=LIMITS[f]
        values[f]=min(high,max(low,v))
    return Phenotype143(**values)
