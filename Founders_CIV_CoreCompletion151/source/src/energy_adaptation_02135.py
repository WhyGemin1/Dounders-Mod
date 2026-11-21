"""Cycle038 opt-in synthetic predator fasting, funded fat, rest, and needs policy.

The World Tree Book remains the sole energy authority. Rest lowers energy
expenditure and mobilizes energy from previously funded tissue-fat stores; it
never creates energy. Traits are fixed species adaptations, NOT evolved traits.
Retains the real tree and its native resident scheduler unchanged.
"""
from __future__ import annotations
from collections import Counter
from habitat_bridge_02123 import HabitatBridge223
from species_life_02115 import PROFILES, PREY, YEAR, MASS_SCALE

# Assumed, synthetic physiology; must be calibrated rather than presented as biology.
PREDATOR_ACTIVE_MULTIPLIER = 0.70
PREDATOR_REST_MULTIPLIER = 0.30
PREDATOR_FAT_CAP = 0.018
PREDATOR_FAT_MOBILIZE = 0.004
PREDATOR_FASTING_DAYS = 14
COURTSHIP_COST = .00015


class HabitatBridge238(HabitatBridge223):
    def __init__(self, tree, seed=9711, counts=None, *,
                 mate_search=False, mouse_hysteresis=False,
                 initial_hound_dispersion=False, predator_scavenging=False):
        self.fasting_days = {}
        self.predator_energy_fluxes = Counter()
        super().__init__(tree, seed=seed, counts=counts,
                         mate_search=mate_search,
                         mouse_hysteresis=mouse_hysteresis,
                         initial_hound_dispersion=initial_hound_dispersion,
                         predator_scavenging=predator_scavenging)

    @staticmethod
    def fat_account(a):
        return f'fat_energy:{a.id}'

    def _store_fat(self, a, reserve_before):
        """Fund a storage account from surplus net feeding energy only."""
        if a.species != 'ridge_hound' or not a.alive:
            return 0.0
        source = self.physical.reserve(a)
        net_gain = max(0.0, self.book.energy[source] - reserve_before)
        available = max(0.0, self.book.energy[source] - .012)
        capacity = max(0.0, PREDATOR_FAT_CAP-self.book.energy[self.fat_account(a)])
        stored = min(net_gain*.35, available*.60, capacity)
        if stored > 1e-12:
            self.book.move(energy=[(source,self.fat_account(a),stored)])
            self.predator_energy_fluxes['fat_stored'] += stored
            self.predator_energy_fluxes['fat_storage_events'] += 1
            self._log('fat_storage',actor=a.id,energy=stored,habitat=a.habitat)
        return stored

    def _feed_stock(self, a, source, kind):
        before = self.book.energy[self.physical.reserve(a)]
        result = super()._feed_stock(a, source, kind)
        if result:
            self._store_fat(a, before)
        return result

    def _hunt(self, a):
        before = self.book.energy[self.physical.reserve(a)]
        result = super()._hunt(a)
        if result:
            self._store_fat(a, before)
        return result

    def _metabolize(self, a):
        if a.species != 'ridge_hound':
            return super()._metabolize(a)
        reserve = self.physical.reserve(a)
        fat = self.fat_account(a)
        resting = self.needs_last.get(a.id) == 'rest'
        available = self.book.energy[reserve]
        if resting or available < .002:
            transfer = min(self.book.energy[fat],PREDATOR_FAT_MOBILIZE,
                           max(0.,.012-available) if resting else max(0.,.004-available))
            if transfer > 1e-12:
                self.book.move(energy=[(fat,reserve,transfer)])
                self.predator_energy_fluxes['fat_mobilized']+=transfer
                self._log('fat_mobilization',actor=a.id,energy=transfer,
                          resting=resting,habitat=a.habitat)
        p = PROFILES[a.species]
        basal = .001*(.5+.5*p.metabolism/.1)
        demand = basal*(PREDATOR_REST_MULTIPLIER if resting else PREDATOR_ACTIVE_MULTIPLIER)
        burn = min(self.book.energy[reserve],demand)
        if burn > 0:
            self.book.move(energy=[(reserve,'environment:heat',burn)])
            self.predator_energy_fluxes['metabolic_energy_paid']+=burn
        if resting:
            self.predator_energy_fluxes['rest_days']+=1
        if burn >= .8*demand:
            a.condition = min(1.,a.condition+(.012 if resting else .007))
        else:
            a.condition = max(0.,a.condition-.045)
        if self.book.energy[reserve]<.0005 and self.book.energy[fat]<.0005:
            self.fasting_days[a.id]=self.fasting_days.get(a.id,0)+1
            self.predator_energy_fluxes['fasting_days']+=1
        else:
            self.fasting_days[a.id]=0

    def evaluate_needs(self, a):
        prior = self.needs_last.get(a.id)
        action,hunger,danger = super().evaluate_needs(a)
        if a.species != 'ridge_hound' or a.stage == 'dependent':
            return action,hunger,danger
        reserve=self.book.energy[self.physical.reserve(a)]
        fat=self.book.energy[self.fat_account(a)]
        available=reserve+fat
        local_prey=any(x.alive and x.species in PREY[a.species]
                       and x.habitat==a.habitat for x in self.actors.values())
        local_carrion=(self.predator_scavenging_enabled and
                       self.book.mass[self.carrion(a.habitat)]>.0004)
        p=PROFILES[a.species]
        local_mate=(a.stage=='adult' and p.breeding[0]<=self.day%YEAR<=p.breeding[1]
                    and any(x.alive and x.id!=a.id and x.species==a.species
                            and x.sex!=a.sex and x.stage=='adult'
                            and x.condition>=.65 and x.habitat==a.habitat
                            for x in self.actors.values()))
        if available<.018:
            if local_prey or local_carrion:
                action='feed'
            elif fat>.0005 and a.condition<.80:
                action='rest'
            else:
                action='search'
        elif a.condition<.72 and available>.006:
            action='rest'
        elif (local_mate and a.condition>=.65 and reserve>=.012 and
              (a.sex=='M' or self.book.mass[self.physical.maternal(a)]>=p.birth_cost*MASS_SCALE)):
            action='mate'
        elif fat>.006 and reserve<.012:
            action='rest'
        if action != self.needs_last.get(a.id):
            # Parent has already accounted its chosen action; replace it.
            base=self.needs_last.get(a.id)
            if base is not None:
                self.needs_choices[f'{a.species}:{base}']-=1
            self.needs_choices[f'{a.species}:{action}']+=1
            self.needs_last[a.id]=action
            self.predator_energy_fluxes[f'prioritized_{action}']+=1
            self._log('predator_priority',actor=a.id,from_action=base,
                      action=action,energy=reserve,fat_energy=fat)
        return action,hunger,danger

    def _reproduce(self):
        """One extra, energy-costed *opportunity* after a deliberate mate choice.

        Keeps all original conception/gestation/maternal stock gates. Parent
        reproduction remains active for all other species and non-selected
        hounds. Neither choice nor courtship guarantees successful conception.
        """
        for mom in list(self.actors.values()):
            if (not mom.alive or mom.species != 'ridge_hound' or mom.sex!='F'
                or mom.pregnant_until is not None or mom.stage!='adult'
                or self.needs_last.get(mom.id)!='mate'):
                continue
            p=PROFILES[mom.species]
            if not (p.breeding[0] <= self.day%YEAR <= p.breeding[1]):
                continue
            reserve=self.physical.reserve(mom)
            if (mom.condition<.65 or self.book.mass[self.physical.live(mom)]<p.adult_mass()*.70
                or self.day-mom.last_birth_day<p.gestation+p.independence
                or self.book.mass[self.physical.maternal(mom)]<p.birth_cost*MASS_SCALE
                or self.book.energy[reserve]<.012+COURTSHIP_COST):
                continue
            mates=[x for x in self.actors.values() if x.alive and x.id!=mom.id
                   and x.species==mom.species and x.sex=='M' and x.stage=='adult'
                   and x.habitat==mom.habitat and x.condition>=.65]
            if not mates:
                continue
            self.book.move(energy=[(reserve,'environment:heat',COURTSHIP_COST)])
            self.predator_energy_fluxes['courtship_attempts']+=1
            self.predator_energy_fluxes['courtship_energy_paid']+=COURTSHIP_COST
            if self.rng.random()<.075:
                father=self.rng.choice(mates)
                mom.pregnancy_father=father.id
                mom.pregnant_until=self.day+p.gestation
                self.predator_energy_fluxes['priority_conceptions']+=1
                self._log('conception',mother=mom.id,father=father.id,
                          due=mom.pregnant_until,species=mom.species,
                          maternal_stock=self.book.mass[self.physical.maternal(mom)],
                          reason='funded_priority_courtship')
        return super()._reproduce()

    def _death(self, a, cause):
        if not a.alive:
            return
        if (a.species=='ridge_hound' and cause=='starvation' and a.condition>0
                and self.fasting_days.get(a.id,0)<PREDATOR_FASTING_DAYS):
            self.predator_energy_fluxes['starvation_deferred']+=1
            return
        fat=self.book.energy[self.fat_account(a)]
        if fat>1e-12:
            dest=(self.physical.carrion_energy(a.habitat)
                  if self.tree.state in ('active','germinating')
                  else 'environment:heat')
            self.book.move(energy=[(self.fat_account(a),dest,fat)])
            self.predator_energy_fluxes['fat_to_carcass_or_heat']+=fat
        return super()._death(a,cause)

    def _check_registry(self):
        super()._check_registry()
        for a in self.actors.values():
            if not a.alive:
                assert self.book.energy[self.fat_account(a)]<1e-9

    def census(self):
        data=super().census()
        data['predator_fat_total']=round(sum(self.book.energy[self.fat_account(a)]
                           for a in self.actors.values() if a.alive and a.species=='ridge_hound'),9)
        data['predator_fasting_days']={k:v for k,v in sorted(self.fasting_days.items()) if v>0}
        data['predator_energy_fluxes']={k:round(v,9) for k,v in sorted(self.predator_energy_fluxes.items())}
        return data
