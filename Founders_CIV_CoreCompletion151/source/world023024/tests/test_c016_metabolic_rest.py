"""C016 regression: real Book-backed stored chemical fuel to useful work on rest."""
import pickle
import pytest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_recovery import perform_rest, paid_work
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest
from founders_civ.core.founder_nutrition import perform_nutrition


def prepared():
    sim, _realm, tid = bootstrap(seed=821)
    tree = sim.world_trees.worlds[tid]
    tree.enable_provisioning()
    for _ in range(17):
        sim.step()
    founder = 'F001'
    sim.founder_harvest_enabled = True
    sim.founder_nutrition_enabled = True
    sim.founder_recovery_enabled = True
    sim.founders.people[founder].location = 'riverbank'
    tree.observe(founder)
    tree.observations[founder]['known_lots'] = observed_lots(tree)
    lot = next(x['lot'] for x in tree.observations[founder]['known_lots'] if x['kind'] == 'food')
    perform_harvest(sim, founder, (tid, lot, 'food'))
    perform_nutrition(sim, founder, 'food_ingest', (tid, lot))
    perform_nutrition(sim, founder, 'food_digest', (tid, lot))
    return sim, founder


def audit(sim):
    checks = sim.book.audit()
    assert abs(checks['energy_error']) < 1e-7
    assert abs(checks['mass_error']) < 1e-7
    assert len(sim.founders.people) == len(set(sim.founders.people)) == 100


def test_rest_mobilizes_real_body_fuel_with_heat_and_no_energy_mint():
    sim, a = prepared()
    account = f'founder:{a}'
    body = f'body_chemical:founder:{a}'
    heat = f'body_heat:founder:{a}'
    assert sim.book.energy[body] == pytest.approx(.015)
    before = (sim.book.energy[account], sim.book.energy[body],sim.book.energy[heat],sim.book.seq)
    ev = perform_rest(sim,a)
    assert ev
    assert sim.book.energy[account] == pytest.approx(before[0] + .0114)
    assert sim.book.energy[body] == pytest.approx(before[1] - .012)
    assert sim.book.energy[heat] == pytest.approx(before[2] + .0006)
    assert sim.book.seq == before[3] + 1
    audit(sim)


def test_replay_same_tick_has_no_additional_fuel_or_fatigue_effect():
    sim, a = prepared()
    sim.recovery_states[a].fatigue = .78
    ev = perform_rest(sim,a,decision_id='decision-001')
    balances = (dict(sim.book.energy),sim.book.seq,sim.recovery_states[a].fatigue,len(sim.events))
    assert perform_rest(sim,a,decision_id='decision-001')==ev
    assert (dict(sim.book.energy),sim.book.seq,sim.recovery_states[a].fatigue,len(sim.events))==balances
    audit(sim)


def test_rest_without_food_reduces_fatigue_but_does_not_manufacture_fuel():
    sim, a = bootstrap(seed=820)[0], 'F001'
    sim.founder_recovery_enabled=True
    sim.recovery_states[a].fatigue=.65
    e_before=dict(sim.book.energy)
    event=sim._do(a,(2.,'rest',None,None),[],None,None)
    assert isinstance(event,str)
    assert sim.recovery_states[a].fatigue==pytest.approx(.45)
    assert dict(sim.book.energy)==e_before
    audit(sim)


def test_legacy_house_river_recharge_is_blocked_only_in_physiology_arm():
    sim, _ = bootstrap(seed=820)[:2]
    sim.founder_recovery_enabled=True
    f='F001'
    sim.founders.people[f].location='riverbank'
    before=dict(sim.book.energy)
    result=sim._do(f,(10.,'recharge',None,None),[],None,None)
    assert isinstance(result,str)
    assert dict(sim.book.energy)==before
    assert not any(v[1]=='recharge' for v in sim._proposals(f,[]))
    sim.founder_recovery_enabled=False
    assert sim._do(f,(10.,'recharge',None,None),[],None,None)
    assert sim.book.energy[f'founder:{f}'] > before[f'founder:{f}']
    audit(sim)


def test_fatigue_increases_paid_work_cost_rest_reduces_future_fuel_cost():
    sim, _=bootstrap(seed=820)[:2]
    sim.founder_recovery_enabled=True
    f='F001'; sim.recovery_states[f].fatigue=.80
    initial=sim.book.energy[f'founder:{f}']
    assert paid_work(sim,f,'practice',.13)
    used_tired=initial-sim.book.energy[f'founder:{f}']
    assert used_tired==pytest.approx(.13*(1+.6*.8))
    sim.recovery_states[f].fatigue=.8
    perform_rest(sim,f)
    initial2=sim.book.energy[f'founder:{f}']
    assert paid_work(sim,f,'practice',.13)
    used_rested=initial2-sim.book.energy[f'founder:{f}']
    assert used_rested < used_tired
    audit(sim)


def test_checkpoint_resume_and_rest_book_replay_are_deterministic():
    sim,a=prepared()
    sim.recovery_states[a].fatigue=.50
    clone=pickle.loads(pickle.dumps(sim))
    for item in (sim,clone):
        event=perform_rest(item,a)
        assert event
        item.book.audit()
    assert dict(sim.book.energy)==dict(clone.book.energy)
    assert sim.recovery_states[a]==clone.recovery_states[a]
    assert sim.book.operations==clone.book.operations
    audit(sim)


def test_no_spoofed_founder_and_disabled_rest_rejected():
    sim, a=prepared()
    with pytest.raises(ValueError,match='unknown|active'):
        perform_rest(sim,'NOT-A-FOUNDER')
    sim.founder_recovery_enabled=False
    with pytest.raises(ValueError,match='disabled'):
        perform_rest(sim,a)
    audit(sim)


def test_fueling_policy_supports_clean_factorial_controls_without_default_bypass():
    sim, _ = bootstrap(seed=820)[:2]
    a='F001'
    sim.founders.people[a].location='riverbank'
    sim.founder_recovery_enabled=True
    assert not sim._legacy_recharge_allowed()  # strict default, even with no fuel
    sim.founder_recharge_source_policy='legacy'  # intentionally nonphysical control
    assert sim._legacy_recharge_allowed()
    sim.founder_recovery_enabled=False
    sim.founder_recharge_source_policy='food_only'  # no-rest refueling ablation
    assert not sim._legacy_recharge_allowed()
    with pytest.raises(ValueError,match='source policy'):
        sim.founder_recharge_source_policy='invented'
        sim._legacy_recharge_allowed()
    sim.founder_recharge_source_policy=None
    assert sim._legacy_recharge_allowed()  # unmodified historical control


def test_distinct_rest_decisions_same_tick_do_not_treat_time_as_currency():
    sim, a=prepared()
    sim.recovery_states[a].fatigue=.65
    tick=sim.tick
    first=perform_rest(sim,a,decision_id='choice-a')
    second=perform_rest(sim,a,decision_id='choice-b')
    assert first != second
    assert sim.tick==tick  # no time was gained or spent
    assert sim.recovery_states[a].rest_decisions==2
    assert sim.recovery_states[a].fatigue==pytest.approx(.25)
    # .015 stored fuel, first rest mobilized .012 and second .003.
    assert sim.book.energy[f'body_chemical:founder:{a}']==pytest.approx(0.)
    before=sim.book.seq
    assert perform_rest(sim,a,decision_id='choice-a')==first
    assert perform_rest(sim,a,decision_id='choice-b')==second
    assert sim.book.seq==before
    audit(sim)


def test_rest_rejects_ambiguous_decision_ids_without_book_or_fatigue_changes():
    sim, founder = prepared()
    before = (dict(sim.book.energy), sim.book.seq,
              sim.recovery_states[founder].fatigue,
              sim.recovery_states[founder].rest_decisions, len(sim.events))
    for decision_id in ('alias:other', ' leading', 'trailing ', ''):
        with pytest.raises(ValueError, match='invalid recovery decision ID'):
            perform_rest(sim, founder, decision_id=decision_id)
    assert (dict(sim.book.energy), sim.book.seq,
            sim.recovery_states[founder].fatigue,
            sim.recovery_states[founder].rest_decisions, len(sim.events)) == before
    audit(sim)


def test_rest_rejects_orphan_book_operation_without_recovering_twice():
    sim, founder = prepared()
    decision_id = 'checkpoint-rest-001'
    operation = f'founder:rest:{founder}:{decision_id}'
    assert perform_rest(sim, founder, decision_id=decision_id)
    sim.recovery_receipts.pop(operation)
    before = (dict(sim.book.energy), sim.book.seq,
              sim.recovery_states[founder].fatigue,
              sim.recovery_states[founder].rest_decisions, len(sim.events))
    with pytest.raises(ValueError, match='missing recovery replay receipt'):
        perform_rest(sim, founder, decision_id=decision_id)
    assert (dict(sim.book.energy), sim.book.seq,
            sim.recovery_states[founder].fatigue,
            sim.recovery_states[founder].rest_decisions, len(sim.events)) == before
    audit(sim)


def test_default_rest_identity_remains_valid_under_strict_separator_guard():
    sim, founder = prepared()
    sim.recovery_states[founder].fatigue = .55
    before = sim.book.seq
    event = perform_rest(sim, founder)
    operation = f'founder:rest:{founder}:manual-{sim.next_event}'
    # The fallback is generated from the next event before logging increments it.
    assert event
    assert operation in sim.recovery_receipts
    assert sim.book.seq == before + 1
    assert perform_rest(sim, founder, decision_id=f'manual-{sim.next_event}') == event
    audit(sim)


def test_corrupt_fatigue_rejects_rest_before_book_or_event_mutation():
    sim, founder = prepared()
    before = (dict(sim.book.energy), sim.book.seq,
              dict(sim.book.operations), len(sim.events),
              sim.recovery_states[founder].rest_decisions)
    for fatigue in (-0.01, 1.01, float('nan'), float('inf')):
        sim.recovery_states[founder].fatigue = fatigue
        with pytest.raises(ValueError, match='invalid Founder fatigue'):
            perform_rest(sim, founder, decision_id='corrupt-rest')
        assert (dict(sim.book.energy), sim.book.seq,
                dict(sim.book.operations), len(sim.events),
                sim.recovery_states[founder].rest_decisions) == before
    assert 'founder:rest:F001:corrupt-rest' not in sim.recovery_receipts
    audit(sim)


def test_corrupt_fatigue_cannot_rank_rest_proposal_or_mutate_book():
    from founders_civ.core.founder_recovery import propose_rest
    sim, founder = prepared()
    before = (dict(sim.book.energy), sim.book.seq, dict(sim.book.operations),
              len(sim.events), sim.recovery_states[founder].rest_decisions)
    for fatigue in (-0.01, 1.01, float('nan'), float('inf')):
        sim.recovery_states[founder].fatigue = fatigue
        with pytest.raises(ValueError, match='invalid Founder fatigue'):
            propose_rest(sim, founder)
        assert (dict(sim.book.energy), sim.book.seq, dict(sim.book.operations),
                len(sim.events), sim.recovery_states[founder].rest_decisions) == before
    sim.recovery_states[founder].fatigue = .5
    assert propose_rest(sim, founder)
    audit(sim)


def test_funded_rest_receipt_rejects_missing_or_changed_book_checkpoint():
    sim, founder = prepared()
    operation = f'founder:rest:{founder}:funded-restore'
    event = perform_rest(sim, founder, decision_id='funded-restore')
    assert event
    assert operation in sim.recovery_book_receipts
    original = sim.book.operations[operation]
    before = (dict(sim.book.energy), sim.book.seq,
              sim.recovery_states[founder].fatigue,
              sim.recovery_states[founder].rest_decisions, len(sim.events))
    sim.book.operations.pop(operation)
    with pytest.raises(ValueError, match='recovery receipt/Book checkpoint mismatch'):
        perform_rest(sim, founder, decision_id='funded-restore')
    assert (dict(sim.book.energy), sim.book.seq,
            sim.recovery_states[founder].fatigue,
            sim.recovery_states[founder].rest_decisions, len(sim.events)) == before
    sim.book.operations[operation] = original
    assert perform_rest(sim, founder, decision_id='funded-restore') == event
    audit(sim)
