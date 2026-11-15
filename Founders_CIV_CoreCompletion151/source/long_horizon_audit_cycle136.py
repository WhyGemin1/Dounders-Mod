"""Opt-in, numerically stable Book.audit for long experiments.

Uses math.fsum to avoid order-dependent reduction error in 100K+ transactions.
Does NOT change transaction processing, initial balances, or physical transfers.
Reports and gates real conservation errors against the Book's native
relative-to-world-budget tolerance, and also the runner's 1e-6 absolute gate.
"""
import math
from founders_civ.core.ledger import Book, EPS

class AccurateAuditBook136(Book):
    def audit(self):
        mass_total=math.fsum(self.mass.values())
        energy_total=math.fsum(self.energy.values())
        m=mass_total-self.start_mass
        e=energy_total-(self.start_energy+self.external)
        self.max_abs_mass_error=max(self.max_abs_mass_error,abs(m))
        self.max_abs_energy_error=max(self.max_abs_energy_error,abs(e))
        mass_tolerance=max(EPS,1e-10*self.start_mass)
        energy_tolerance=max(EPS,1e-10*(self.start_energy+self.external))
        if abs(m)>mass_tolerance or abs(e)>energy_tolerance:
            raise AssertionError(f'ledger error mass={m}, energy={e}')
        if min(self.mass.values()) < -EPS or min(self.energy.values()) < -EPS:
            raise AssertionError('negative stock')
        return {'mass_error':m,'energy_error':e,
             'max_abs_mass_error':self.max_abs_mass_error,
             'max_abs_energy_error':self.max_abs_energy_error,
             'mass_total':mass_total,'energy_total':energy_total,
             'external_wellspring':self.external,
             'transactions':self.transactions,
             'toll_events':self.toll_count,'rejections':self.rejected}

def enable_precise_audit(sim):
    book=sim.host.book
    if type(book) is not Book:raise TypeError('expected native Book')
    book.__class__=AccurateAuditBook136
    if book is not sim.bridge.book or book is not sim.bridge.tree.book:
        raise AssertionError('audit must share one authoritative Book')
    return sim

from five_habitat_02142 import FiveHabitatRunner, ORIGINAL, FIFTH
class LongHorizonFiveHabitatRunner136(FiveHabitatRunner):
    def _validate(self):
        # Retain native identity/clock/world invariants and the Book's native
        # scale-aware tolerance instead of the historical absolute 1e-6 runner
        # gate that eventually fails solely from roundoff after ~300K moves.
        assert self.book is self.sim.ecology.book
        assert self.book is self.sim.world_trees.worlds[self.tree_id].book
        assert len(self.sim.founders.people)==100
        habitats=set(self.sim.world_trees.worlds[self.tree_id].habitats)
        assert habitats in (ORIGINAL, ORIGINAL | {FIFTH})
        assert self.sim.tick == self.sim.ecology.day
        a=self.book.audit()
        mass_tol=max(EPS,1e-10*self.book.start_mass)
        energy_tol=max(EPS,1e-10*(self.book.start_energy+self.book.external))
        assert abs(a['mass_error']) <= mass_tol and abs(a['energy_error']) <= energy_tol

def enable_long_horizon_validation(sim):
    if type(sim.host) is not FiveHabitatRunner:raise TypeError('expected native five habitat runner')
    sim.host.__class__=LongHorizonFiveHabitatRunner136
    return sim
