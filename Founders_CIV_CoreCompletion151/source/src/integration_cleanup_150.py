"""Core150: local food-lot consistency and physiological decision cleanup.

Changes are opt-in for matched comparisons. Book alone owns mass/energy;
cell records are access metadata, never minted resource inventories.
"""
from __future__ import annotations
from collections import Counter
from five_phase_core_142 import EdibleLot
from trophic_integration_149 import UnifiedTrophicIntegration149, TrophicIntegrationBridge149
from trophic_roles_146 import CARNIVORE_ROLES


class CleanBridge150(TrophicIntegrationBridge149):
    def activate_cleanup(self, enabled=True):
        self.cleanup150_enabled = bool(enabled)
        self.cleanup150_metrics = Counter()
        # Pair exactly the mass already localized in _carcass_patches149 with
        # its embodied chemical energy. Neither mapping owns Book stock.
        self._carcass_energy_patches150 = {}

    def _refresh_quota(self):
        if not self.cleanup150_enabled:
            return super()._refresh_quota()
        old_mass = dict(self._carcass_patches149)
        super()._refresh_quota()
        # Parent may proportionally reconcile localized mass to real stock.
        for cell, old in old_mass.items():
            now = self._carcass_patches149.get(cell, 0.)
            if old > 0. and now < old:
                self._carcass_energy_patches150[cell] = (
                    self._carcass_energy_patches150.get(cell, 0.) * now / old)
        # Existing habitat-global processes can alter carcass energy. Keep
        # location estimates below Book totals without altering Book itself.
        for habitat in self.tree.habitats:
            keys = [k for k in self._carcass_energy_patches150 if k[0] == habitat]
            claimed = sum(self._carcass_energy_patches150[k] for k in keys)
            actual = max(0., self.book.energy[self.physical.carrion_energy(habitat)])
            if claimed > actual + 1e-12 and claimed > 0:
                factor = actual / claimed
                for k in keys:
                    self._carcass_energy_patches150[k] *= factor
                self.cleanup150_metrics['patch_energy_reconciliations'] += 1

    def _carcass_energy_offer(self, animal, requested_mass):
        """Energy in the accessible *local* portion of a mixed carcass pool."""
        source = self.carrion(animal.habitat)
        keys = self._forage_cells(animal, source)
        all_patches = [(k, m) for k, m in self._carcass_patches149.items()
                       if k[0] == animal.habitat]
        pmass = sum(max(0., m) for _, m in all_patches)
        penergy = sum(max(0., self._carcass_energy_patches150.get(k, 0.))
                      for k, _ in all_patches)
        total_mass = max(0., self.book.mass[source])
        total_energy = max(0., self.book.energy[self.physical.carrion_energy(animal.habitat)])
        background_mass = max(0., total_mass - pmass)
        background_energy = max(0., total_energy - penergy)
        bg_density = background_energy / background_mass if background_mass > 1e-12 else 0.
        remaining = max(0., requested_mass)
        energy = 0.
        for cell in keys:
            if remaining <= 1e-12:break
            quota = max(0., self._cell_quota.get((source, *cell), 0.))
            take = min(remaining, quota)
            localized = min(take, max(0., self._carcass_patches149.get(tuple(cell), 0.)))
            mass = max(0., self._carcass_patches149.get(tuple(cell), 0.))
            embedded = max(0., self._carcass_energy_patches150.get(tuple(cell), 0.))
            energy += localized * (embedded / mass if mass > 1e-12 else 0.)
            energy += (take - localized) * bg_density
            remaining -= take
        return max(0., min(total_energy, energy))

    def _spend_forage_quota(self, animal, source, amount):
        if not (self.cleanup150_enabled and self.integration149_flags['carcass_locality']
                and source == self.carrion(animal.habitat)):
            return super()._spend_forage_quota(animal, source, amount)
        remaining = amount
        for cell in self._forage_cells(animal, source):
            quota_key = (source, *cell)
            quota = max(0., self._cell_quota.get(quota_key, 0.))
            used = min(quota, remaining)
            if used <= 0:continue
            patch_key = tuple(cell)
            before_mass = max(0., self._carcass_patches149.get(patch_key, 0.))
            before_energy = max(0., self._carcass_energy_patches150.get(patch_key, 0.))
            consumed_patch_mass = min(used, before_mass)
            consumed_patch_energy = before_energy * consumed_patch_mass / before_mass if before_mass > 1e-12 else 0.
            self._carcass_patches149[patch_key] = max(0., before_mass - consumed_patch_mass)
            self._carcass_energy_patches150[patch_key] = max(0., before_energy - consumed_patch_energy)
            self._cell_quota[quota_key] = quota - used
            remaining -= used
            if remaining <= 1e-9:break
        if remaining > 1e-7:
            raise AssertionError('carcass local quota exceeded')
        self.cleanup150_metrics['paired_carcass_access_events'] += 1

    def _feed_stock(self, animal, source, kind, dt=None):
        if not (self.cleanup150_enabled and self.integration149_flags['carcass_locality']
                and source == self.carrion(animal.habitat) and animal.species in CARNIVORE_ROLES):
            return super()._feed_stock(animal, source, kind, dt=dt)
        if not animal.alive:return False
        dt = getattr(self, '_current_dt', 1.) if dt is None else dt
        role = CARNIVORE_ROLES[animal.species]
        body = self._bodymass(animal)
        daily = max(.007, body*.24)*self._trait(animal).intake
        if animal.stage in ('dependent', 'juvenile'):daily *= .7
        available = self._local_access(animal, source)
        q = min(daily*dt, available,
                max(0., role.stomach_fraction*body-self.book.mass[self.physical.gut(animal)]))
        if q < 1e-6:return False
        e = self._carcass_energy_offer(animal, q)
        if e < 1e-12:return False
        lot = self.lots.carrion(animal.habitat)
        # Give the existing Book ingest API the energy density of the ACTUAL
        # accessible portion; do not use habitat-wide density for a local meal.
        local_lot = EdibleLot(lot.mass_account, lot.energy_account, lot.habitat,
                              lot.material, e/q)
        fed = self.lots.ingest(animal, local_lot, q, role.meat_digestibility, kind)
        if fed:
            self.cleanup150_metrics['localized_calorie_meals'] += 1
        return fed

    def _hunt(self, predator):
        if not self.cleanup150_enabled:
            return super()._hunt(predator)
        account = self.physical.carrion_energy(predator.habitat)
        before = self.book.energy[account]
        source = self.carrion(predator.habitat)
        before_mass = self.book.mass[source]
        result = super()._hunt(predator)
        # The older method transfers a portion of reserve/rapid fuel into the
        # killer's gut AFTER localizing the remaining carcass mass.
        if self.integration149_flags['carcass_locality']:
            remaining = max(0., self.book.mass[source]-before_mass)
            new_energy = max(0., self.book.energy[account]-before)
            if remaining > 1e-12 and new_energy > 1e-12:
                death = next((x for x in reversed(self.events[-15:])
                              if x.get('event')=='predation' and x.get('predator')==predator.id), None)
                if death is not None:
                    victim = self.actors.get(death['prey'])
                    if victim is not None:
                        location = tuple(self._pos(victim))
                        self._carcass_energy_patches150[location] = (
                            self._carcass_energy_patches150.get(location, 0.) + new_energy)
                        self.cleanup150_metrics['localized_kill_energy'] += new_energy
        return result

    def _choose(self, actor):
        action, hunger, danger = super()._choose(actor)
        if (self.cleanup150_enabled and not danger and action in ('feed', 'search')
            and actor.species in CARNIVORE_ROLES):
            role = CARNIVORE_ROLES[actor.species]
            capacity = role.stomach_fraction * self._bodymass(actor)
            gut = self.book.mass[self.physical.gut(actor)]
            if capacity > 0 and gut >= .72 * capacity:
                self.cleanup150_metrics['full_gut_rest_decisions'] += 1
                return 'rest', 0., False
        return action, hunger, danger


class UnifiedCleanup150(UnifiedTrophicIntegration149):
    def __init__(self, *args, cleanup150=True, **kwargs):
        super().__init__(*args, **kwargs)
        if type(self.bridge) is not TrophicIntegrationBridge149:
            raise TypeError('Cycle150 requires unmodified Core149 bridge')
        self.bridge.__class__ = CleanBridge150
        self.bridge.activate_cleanup(cleanup150)
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        r = super().report()
        r['cleanup_150'] = {
            'enabled': self.bridge.cleanup150_enabled,
            'metrics': dict(self.bridge.cleanup150_metrics),
            'status': 'experimental_not_canonical',
        }
        return r
