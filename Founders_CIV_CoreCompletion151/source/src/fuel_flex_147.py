"""Core147: physically funded, adaptive energy mobilization for Founders animals.

Research prototype, not empirical calibration. Existing short substrate models rapid
circulating/glycogen availability; the Book reserve models endogenous longer-term
fuel. Structural tissue is an expensive, bounded, LAST-RESORT substrate. This
module does not create energy or time, bypass the Book, or guarantee survival.

One Book, world clock, 100 Founders, and two demographic schedulers are retained.
"""
from __future__ import annotations
from collections import Counter
from core_completion_146 import UnifiedCoreCompletion146, CoreCompletionBridge146
from core_physiology_v2 import MAX_FATIGUE, PROFILES


LOW_INTENSITY = frozenset({
    'cell_movement', 'habitat_movement', 'prey_tracking', 'scavenge_movement',
    'caregiving', 'avoid_large_predator',
})


class FuelFlexBridge147(CoreCompletionBridge146):
    def activate_fuel_flex(self, enabled=True):
        self.fuel_flex_enabled = bool(enabled)
        self.fuel_flex_metrics = Counter()

    def _maintenance_demand(self, a):
        basal = super()._maintenance_demand(a)
        if not self.fuel_flex_enabled:
            return basal
        # Reversible modest fasting adaptation is a state response, not a
        # permanent 25% reduction for every animal. Zero fuel never means zero
        # metabolism. Fatigue/sleep alone do not refund physical energy.
        s = self._state(a)
        reserve = self.book.energy[self.physical.reserve(a)]
        rapid = self.book.energy[self._short(a)]
        coverage = (rapid + reserve) / max(basal, 1e-12)
        debt = min(1.0, max(0.0, s.starvation_debt))
        adaptation = min(0.15, 0.04 * debt + (0.11 if coverage < 1.0 else 0.06 if coverage < 3.0 else 0.0))
        return basal * (1.0 - adaptation)

    def _mobilization_capacity(self, a):
        # Power (how fast stored reserves can be mobilized) and energy stock
        # (total chemical energy) are DIFFERENT. This is a rate per resolution
        # step; step duration is a world-clock fraction, not a time wallet.
        dt = max(0.0, min(1.0, float(getattr(self, '_current_dt', 1.0))))
        basal = self._maintenance_demand(a)
        endurance = self._trait(a).endurance
        return max(1e-8, basal * (3.0 + 12.0 * dt) * max(.7, min(1.4, endurance)))

    def _mobilize(self, a, wanted):
        if not self.fuel_flex_enabled:
            return super()._mobilize(a, wanted)
        requested = max(0.0, wanted)
        if requested <= 1e-12:
            return 0.0
        b = self.book; reserve = self.physical.reserve(a)
        amount = min(requested, b.energy[reserve], self._mobilization_capacity(a))
        if amount > 1e-12:
            b.move(energy=[(reserve, self._short(a), amount)])
            self.fuel_flex_metrics['reserve_mobilized'] += amount
            self.fuel_flex_metrics['reserve_mobilization_events'] += 1
        return amount

    def _emergency_tissue_to_fuel(self, a, requested):
        """Costly limited fasting metabolism, not a second free reserve.

        Called ONLY to fund low-intensity movement/care that is otherwise
        impossible. It burns body tissue and deteriorates condition. It cannot
        finance high-intensity strikes and will stop at structural minimum.
        """
        if requested <= 1e-12 or not a.alive:
            return 0.0
        b = self.book; ph = self.physical
        body = b.mass[ph.live(a)]; tissue = ph.tissue(a)
        energy = b.energy[tissue]
        p = PROFILES[a.species]
        minimum = max(p.newborn_mass() * .80, p.adult_mass() * .35)
        excess = max(0., body-minimum)
        if excess <= 1e-12 or energy <= 1e-12:
            return 0.0
        density = energy/max(body,1e-12)
        useful_fraction = .75 * .90
        gross = min(requested / useful_fraction, energy*.012,
                    excess*density*.06)
        potential = (gross*.90)*.75
        # Do not strip tissue on a partial failed action: the requested
        # physical movement must be completely funded before conversion.
        if gross <= 1e-12 or potential + 1e-11 < requested:
            return 0.0
        loss = min(excess,gross/max(density,1e-12))
        toll = gross*.10
        b.transform([(ph.live(a),ph.detritus(a),loss)],
                    source=tissue,work=toll,
                    energy_outputs=[(tissue,'environment:heat',toll*.90)])
        useful=(gross-toll)*.75
        lost=(gross-toll)-useful
        b.move(energy=[(tissue,self._short(a),useful),
                       (tissue,'environment:heat',lost)])
        a.condition=max(0.,a.condition-.002*loss/max(body,1e-12))
        self.fuel_flex_metrics['emergency_tissue_energy'] += useful
        self.fuel_flex_metrics['emergency_tissue_mass'] += loss
        return useful

    def _work(self,a,activity,effort=1.0):
        if not self.fuel_flex_enabled:
            return super()._work(a,activity,effort)
        # Physical work only; deciding to move/forage has no independent tax.
        s=self._state(a);trait=self._trait(a)
        scale=(self._bodymass(a)/.05)**.64
        learned=1.+min(.5,s.experience*.20)
        readiness=max(.20,s.readiness)
        efficiency=max(.35,(1.-.34*s.fatigue)*readiness*learned)
        actual_effort=effort/max(0.1,trait.locomotion)
        # Economical locomotion at low speed; an attack remains exertive.
        gait = .78 if activity in LOW_INTENSITY else 1.0
        demand=.000055*scale*actual_effort*gait/max(efficiency,.1)
        short=self._short(a)
        if self.book.energy[short] < demand:
            self._mobilize(a,demand-self.book.energy[short])
        if self.book.energy[short]+1e-12<demand and activity in LOW_INTENSITY:
            self._emergency_tissue_to_fuel(a,demand-self.book.energy[short])
        # No partial charge for a cancelled activity. Work is actually settled
        # only if it resolves, with exactly one Book debit to environmental heat.
        if self.book.energy[short]+1e-12<demand:
            self.physiology_metrics['work_unfunded']+=1
            self.fuel_flex_metrics['work_power_limited']+=1
            return False
        self.book.move(energy=[(short,'environment:heat',demand)])
        self.physiology_metrics['resolved_work_energy']+=demand
        s.fatigue=min(MAX_FATIGUE,s.fatigue+.018*actual_effort/(readiness*learned*trait.endurance))
        s.experience=min(2.,s.experience+.0006)
        self.physiology_metrics[f'activity:{activity}']+=1
        self.fuel_flex_metrics['physical_work_events']+=1
        if activity in LOW_INTENSITY:self.fuel_flex_metrics['low_intensity_work_events']+=1
        return True


class UnifiedFuelFlex147(UnifiedCoreCompletion146):
    def __init__(self,*args,fuel_flex=True,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not CoreCompletionBridge146:
            raise TypeError('Unexpected bridge before FuelFlex147 integration')
        self.bridge.__class__=FuelFlexBridge147
        self.bridge.activate_fuel_flex(enabled=fuel_flex)
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        result=super().report()
        result['fuel_flex_147']={
            'status':'experimental_not_canonical',
            'enabled':self.bridge.fuel_flex_enabled,
            'metrics':dict(self.bridge.fuel_flex_metrics),
        }
        return result
