"""C019: Founder values and experience guide choices but never require upkeep."""
import pickle
from random import Random

import pytest

from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_autonomy import personal_values, value_proposals


def sim_on(seed=820):
    sim, realm, tree = bootstrap(seed=seed)
    sim.founder_autonomy_learning_enabled = True
    sim.founder_parent_stewardship_enabled = True
    return sim, realm, tree


def test_default_feature_off_preserves_legacy_choice_contract():
    s, realm, _ = bootstrap(seed=820)
    assert not s.founder_autonomy_learning_enabled
    proposals=[(6.9,'parent_steward',None,(realm,.3)),(.4,'study',None,None)]
    assert value_proposals(s,'F001',proposals)==proposals
    assert not hasattr(s,'founder_valuations')


def test_100_founders_have_private_heterogeneous_starting_values():
    s, _, _=sim_on()
    vals=[personal_values(s,f) for f in s.founders.people]
    assert len(vals)==100
    assert len({round(v.care_preference,6) for v in vals}) >= 50
    assert all(-1<=v.care_preference<=1 for v in vals)
    assert all(v.experience_count==0 for v in vals)


def test_all_maintenance_candidates_can_be_declined_without_spending_fuel():
    s, realm, _=sim_on()
    f='F002'
    choices=value_proposals(s,f,[(7.6,'parent_steward',None,(realm,.3))])
    assert any(p[1]=='parent_steward' for p in choices)
    assert any(p[1]=='decline_investment' for p in choices)
    # The existing stochastic chooser, not a forced steward command, picks.
    decisions={s._choose(f,choices,Random(j))[1] for j in range(150)}
    assert 'parent_steward' in decisions
    assert 'decline_investment' in decisions
    before=s.book.seq
    event=s._do(f,next(p for p in choices if p[1]=='decline_investment'),[],Random(2),'test-choice')
    assert event
    assert s.events[-1]['action']=='founder_declined_investment'
    assert s.book.seq==before


def test_event_based_learning_is_private_not_omniscient():
    s, _, _=sim_on()
    alice='F001'; bob='F002'
    a=personal_values(s,alice)
    b=personal_values(s,bob)
    before_a=a.believed_tree_value
    before_b=b.believed_tree_value
    # An actually perceived resource raises the perceiver's valuation.
    s.log('founder_food_scan',alice,visible_lots=3)
    value_proposals(s,alice,[])
    value_proposals(s,bob,[])
    assert a.believed_tree_value > before_a
    assert b.believed_tree_value == before_b
    # Global collapse is not private knowledge, even if record actor=owner.
    old=a.believed_tree_value
    s.log('creation_collapsed',alice,creation='CRE-99999')
    value_proposals(s,alice,[])
    assert a.believed_tree_value==old


def test_one_bad_experience_can_reduce_care_value_not_enforce_it():
    s, realm, _=sim_on()
    f='F002'
    m=personal_values(s,f)
    before=m.believed_care_value
    s.log('world_action_rejected',f,attempted='parent_steward',reason='no observed reserve')
    value_proposals(s,f,[])
    assert m.believed_care_value < before
    assert m.experience_count==1


def test_no_book_changes_from_personal_valuer_or_new_opt_out():
    s, realm, _=sim_on()
    f='F002'; seq=s.book.seq; balances=dict(s.book.energy)
    for _ in range(5):value_proposals(s,f,[(7.5,'parent_steward',None,(realm,.3))])
    assert s.book.seq==seq
    assert dict(s.book.energy)==balances
    s.book.audit()


def test_pickle_checkpoint_replay_preserves_individual_learning_and_choices():
    s, realm, _=sim_on()
    f='F002'; s.log('tree_founder_harvest',f,resource_kind='food')
    value_proposals(s,f,[])
    copy=pickle.loads(pickle.dumps(s))
    before=[(7.0,'parent_steward',None,(realm,.3)),(.6,'practice',None,None)]
    assert value_proposals(s,f,before)==value_proposals(copy,f,before)
    assert s._choose(f,value_proposals(s,f,before),Random(120))==copy._choose(f,value_proposals(copy,f,before),Random(120))
    assert s.book.seq==copy.book.seq


def test_maintenance_is_not_unconditionally_top_ranked():
    s, realm, _=sim_on()
    f='F002'
    proposals=[(7.5,'parent_steward',None,(realm,.4)),(1.45,'study',None,None),
               (1.75,'explore',None,None)]
    adjusted=value_proposals(s,f,proposals)
    assert max(x[0] for x in adjusted if x[1]=='parent_steward') < 7.5
    assert any(x[1]=='explore' and x[0]==1.75 for x in adjusted)
    assert any(x[1]=='decline_investment' for x in adjusted)


def test_integration_step_identity_conservation_and_optional_refusal():
    s, realm, _=sim_on(seed=822)
    s.founder_tree_independence_enabled = True
    s.founder_harvest_enabled = True
    s.founder_community_foraging_enabled = True
    for _ in range(3):s.step()
    assert len(s.founders.people)==100
    assert len({x.id for x in s.founders.people.values()})==100
    assert s.counter['founder_declined_investment']>=1
    assert s.book.audit()['mass_error']<1e-6
    assert s.book.audit()['energy_error']<1e-6
