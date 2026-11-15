"""Cycle136 isolated juvenile feeding candidate; no second ecology or Book.

Only dependent animals with an alive co-located caregiver may take an
additional meal from a species-compatible *existing* World Tree account.
One guardian pays a finite energy handling cost per successful meal; actual
food mass and chemical/embodied energy move through existing Book methods.
All baseline behavior remains unchanged unless bridge is explicitly opted in.
This is an experimental caregiver-assisted solid-food proxy, NOT calibrated milk.
"""
from collections import Counter
from knowledge_family_02142 import KnowledgeFamilyBridge242
from species_life_02115 import PROFILES

ASSIST_GUARDIAN_WORK = .00010
ASSIST_GUARDIAN_FLOOR = .003
ASSIST_CHILD_RESERVE_TARGET = .006

class JuvenileSupportBridge136(KnowledgeFamilyBridge242):
    """Same instance/clock/scheduler as KnowledgeFamilyBridge242; opt-in override."""
    def evaluate_needs(self, a):
        if a.alive and a.stage == 'dependent' and a.generation >= 1:
            self._try_assisted_feed(a)
        return super().evaluate_needs(a)

    def _try_assisted_feed(self, child):
        metrics = self.juvenile_support_metrics
        metrics['dependent_opportunities'] += 1
        if self.book.energy[self.physical.reserve(child)] >= ASSIST_CHILD_RESERVE_TARGET:
            metrics['child_reserve_sufficient'] += 1
            return False
        guardians = [self.actors[i] for i in sorted(child.caregiver_ids)
                     if i in self.actors and self.actors[i].alive
                     and self.actors[i].habitat == child.habitat
                     and self.actors[i].stage in ('adult','elder')]
        if not guardians:
            metrics['no_colocated_caregiver'] += 1
            return False
        donor = max(guardians, key=lambda p: self.book.energy[self.physical.reserve(p)])
        donor_account = self.physical.reserve(donor)
        if self.book.energy[donor_account] < ASSIST_GUARDIAN_FLOOR + ASSIST_GUARDIAN_WORK:
            metrics['caregiver_insufficient_energy'] += 1
            return False
        if child.species == 'ridge_hound':
            source = self.carrion(child.habitat)
            kind = 'assisted_carrion'
            minimum = .0004
        elif child.species == 'carrion_bird' and self.book.mass[self.carrion(child.habitat)] >= .0004:
            source = self.carrion(child.habitat)
            kind = 'assisted_carrion'
            minimum = .0004
        else:
            source = self.physical.plant(child)
            kind = 'assisted_plant'
            minimum = .04
        if self.book.mass[source] <= minimum:
            metrics['no_compatible_local_food'] += 1
            return False
        before_reserve = self.book.energy[self.physical.reserve(child)]
        before_mass = self.book.mass[source]
        if not self._feed_stock(child, source, kind):
            metrics['no_digestible_energy'] += 1
            return False
        self.book.move(energy=[(donor_account, 'environment:heat', ASSIST_GUARDIAN_WORK)])
        metrics['successful_meals'] += 1
        metrics['food_mass_debited'] += before_mass-self.book.mass[source]
        metrics['caregiver_work_energy_debited'] += ASSIST_GUARDIAN_WORK
        self._log('assisted_dependent_meal',actor=child.id,caregiver=donor.id,
                  species=child.species,habitat=child.habitat,
                  food_source=kind,material_debit=before_mass-self.book.mass[source],
                  caregiver_work_energy=ASSIST_GUARDIAN_WORK,
                  child_reserve_gain=self.book.energy[self.physical.reserve(child)]-before_reserve)
        return True


def enable_assisted_feeding(sim):
    if type(sim.bridge) is not KnowledgeFamilyBridge242:
        raise TypeError('cycle136 candidate requires exact, unmodified Cycle135 bridge')
    sim.bridge.__class__ = JuvenileSupportBridge136
    sim.bridge.juvenile_support_metrics = Counter()
    return sim
