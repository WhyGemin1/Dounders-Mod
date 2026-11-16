"""C020: consent, physically backed exchange, optional cooperation, independence."""
from copy import deepcopy
import pickle
from random import Random

import pytest

from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest
from founders_civ.core.founder_exchange import (offer_resource,decide_offer,owns_lot,
    owned_lots,propose_exchange,withdraw_offer)
from founders_civ.core.founder_nutrition import propose_nutrition, perform_nutrition
from founders_civ.core.founder_tree_agency import _own_fruit, fund_own_tree


def setup(kind='food', seed=821):
    sim, realm, tid = bootstrap(seed=seed)
    tree=sim.world_trees.worlds[tid]
    tree.enable_provisioning()
    for _ in range(17):sim.step()
    sim.founder_harvest_enabled=True
    sim.founder_exchange_enabled=True
    sim.founder_nutrition_enabled=True
    sim.founder_tree_independence_enabled=True
    seller,buyer='F001','F002'
    sim.founders.people[seller].location='riverbank'
    sim.founders.people[buyer].location='riverbank'
    tree.observe(seller)
    tree.observations[seller]['known_lots']=observed_lots(tree)
    lot=next(x['lot'] for x in tree.observations[seller]['known_lots'] if x['kind']==kind)
    perform_harvest(sim,seller,(tid,lot,kind))
    return sim,realm,tid,seller,buyer,lot


def audit(sim):
    a=sim.book.audit()
    assert abs(a['mass_error'])<1e-7
    assert abs(a['energy_error'])<1e-6
    assert len(sim.founders.people)==100


def test_explicit_consent_and_gift_moves_real_food_no_fuel_mint():
    s,_,tid,a,b,lot=setup()
    prev=dict(s.book.energy); before=s.book.transactions
    offer=offer_resource(s,a,b,'food',lot,decision_id='choice-1')
    assert s.book.transactions==before
    assert owns_lot(s,a,'food',lot) and not owns_lot(s,b,'food',lot)
    txn=decide_offer(s,b,offer,True)
    assert txn and txn.seq>before
    assert not owns_lot(s,a,'food',lot)
    assert owns_lot(s,b,'food',lot)
    assert s.book.mass[f'portable_food:lot:{lot}:founder:{b}']==pytest.approx(.08)
    assert s.book.energy[f'food_energy:lot:{lot}:founder:{b}']==pytest.approx(.02)
    assert s.book.energy[f'founder:{a}']==prev[f'founder:{a}']
    assert s.book.energy[f'founder:{b}']==prev[f'founder:{b}']
    assert decide_offer(s,b,offer,True)==txn
    assert s.book.transactions==before+1
    audit(s)


def test_recipient_can_refuse_without_resources_moving():
    s,_,_,a,b,lot=setup()
    offer=offer_resource(s,a,b,'food',lot,decision_id='refused')
    balances=(dict(s.book.mass),dict(s.book.energy),s.book.seq)
    assert decide_offer(s,b,offer,False) is None
    assert (dict(s.book.mass),dict(s.book.energy),s.book.seq)==balances
    assert owns_lot(s,a,'food',lot)
    with pytest.raises(ValueError,match='declined'):decide_offer(s,b,offer,True)


def test_no_remote_claim_no_wrong_recipient_or_forged_lot():
    s,_,_,a,b,lot=setup()
    offer=offer_resource(s,a,b,'food',lot,decision_id='meet')
    before=s.book.seq
    with pytest.raises(ValueError,match='recipient'):
        decide_offer(s,'F003',offer,True)
    s.founders.people[b].location='ridge'
    with pytest.raises(ValueError,match='meet'):
        decide_offer(s,b,offer,True)
    s.founders.people[b].location='riverbank'
    with pytest.raises(ValueError,match='lacks'):
        offer_resource(s,b,a,'food',lot,decision_id='forgery')
    assert s.book.seq==before


def test_no_double_pledge_or_second_owner_claim():
    s,_,_,a,b,lot=setup()
    oid=offer_resource(s,a,b,'food',lot,decision_id='once')
    assert oid==offer_resource(s,a,b,'food',lot,decision_id='once')
    s.founders.people['F003'].location='riverbank'
    with pytest.raises(ValueError,match='conflicting'):
        offer_resource(s,a,'F003','food',lot,decision_id='once')
    with pytest.raises(ValueError,match='already offered'):
        offer_resource(s,a,b,'food',lot,decision_id='twice')
    decide_offer(s,b,oid,True)
    with pytest.raises(ValueError,match='lacks'):
        offer_resource(s,a,b,'food',lot,decision_id='after-spent')
    audit(s)


def test_traded_food_is_ingestible_and_digestible():
    s,_,tid,a,b,lot=setup()
    oid=offer_resource(s,a,b,'food',lot,decision_id='eat')
    decide_offer(s,b,oid,True)
    proposals=propose_nutrition(s,b)
    assert any(p[1]=='food_ingest' and p[3]==(tid,lot) for p in proposals)
    perform_nutrition(s,b,'food_ingest',(tid,lot))
    assert s.book.mass[f'gut:founder:{b}:lot:{lot}']==pytest.approx(.08)
    perform_nutrition(s,b,'food_digest',(tid,lot))
    assert s.book.energy[f'body_chemical:founder:{b}']>=.015-1e-8
    audit(s)


def test_creation_fruit_gift_supports_independent_world_seed():
    s,realm,tid,a,b,lot=setup(kind='fruit')
    oid=offer_resource(s,a,b,'fruit',lot,decision_id='propagate')
    decide_offer(s,b,oid,True)
    assert (tid,lot) in list(_own_fruit(s,b))
    blueprint=s.seeds.draft(b,'world','Independent food Tree',realm,x=63,y=40)
    blueprint.stage='validated' # isolate physical funding from already-tested peer review
    txn=fund_own_tree(s,b,(blueprint.id,tid,lot))
    assert txn
    assert s.book.mass[f'world_seed:{blueprint.id}']==pytest.approx(.10)
    assert s.book.energy[f'ce:seed:{blueprint.id}']==pytest.approx(1.)
    assert f'seed:fund:{blueprint.id}' in s.book.operations
    audit(s)


def test_real_food_for_real_fruit_atomic_barter_and_replay():
    s,realm,tid,a,b,food=setup()
    tree=s.world_trees.worlds[tid]
    tree.observe(b)
    tree.observations[b]['known_lots']=observed_lots(tree)
    fruit=next(x['lot'] for x in tree.observations[b]['known_lots'] if x['kind']=='fruit')
    perform_harvest(s,b,(tid,fruit,'fruit'))
    oid=offer_resource(s,a,b,'food',food,'fruit',decision_id='barter')
    checkpoint=pickle.loads(pickle.dumps(s))
    first=decide_offer(s,b,oid,True,fruit)
    again=decide_offer(checkpoint,b,oid,True,fruit)
    assert dict(s.book.mass)==dict(checkpoint.book.mass)
    assert dict(s.book.energy)==dict(checkpoint.book.energy)
    assert first.seq==again.seq
    assert owns_lot(s,a,'fruit',fruit) and owns_lot(s,b,'food',food)
    before=s.book.seq
    assert decide_offer(s,b,oid,True,fruit)==first
    assert s.book.seq==before
    with pytest.raises(ValueError,match='conflicting'):
        decide_offer(s,b,oid,True,'FAKE')
    audit(s)


def test_unaffordable_barter_rejected_without_partial_transfer():
    s,_,_,a,b,food=setup()
    oid=offer_resource(s,a,b,'food',food,'fruit',decision_id='cannot')
    snapshot=(dict(s.book.mass),dict(s.book.energy),s.book.seq)
    with pytest.raises(ValueError,match='lacks'):
        decide_offer(s,b,oid,True,'NONEXISTENT')
    assert (dict(s.book.mass),dict(s.book.energy),s.book.seq)==snapshot


def test_scheduler_offers_alternatives_and_book_unchanged_by_proposals():
    s,_,_,a,b,lot=setup()
    before=(s.book.seq,dict(s.book.mass),dict(s.book.energy))
    s.states[a].main_goal='solidarity'  # opt-in voluntary gift; recipient need not own barter fruit
    props=propose_exchange(s,a,[b])
    assert any(p[1]=='exchange_offer' for p in props)
    assert (s.book.seq,dict(s.book.mass),dict(s.book.energy))==before
    made=next(p for p in props if p[1]=='exchange_offer')
    # Existing actor routing, not a standalone fake market simulator.
    s._do(a,made,[b],Random(11),'decision-offer')
    offers=[p for p in s._proposals(b,[a]) if p[1] in ('exchange_accept','exchange_decline')]
    assert {p[1] for p in offers}=={'exchange_accept','exchange_decline'}
    s._do(b,next(p for p in offers if p[1]=='exchange_decline'),[a],Random(11),'decline')
    assert owns_lot(s,a,'food',lot)


def test_cannot_use_feature_when_disabled_and_no_mandatory_exchange():
    s,_,_,a,b,lot=setup()
    s.founder_exchange_enabled=False
    assert propose_exchange(s,a,[b])==[]
    with pytest.raises(ValueError,match='disabled'):
        offer_resource(s,a,b,'food',lot,decision_id='disabled')
    assert not any(p[1].startswith('exchange_') for p in s._proposals(a,[b]))


def test_scheduler_can_settle_consentful_gift_but_keeps_decline_option():
    s,_,tid,a,b,lot=setup()
    s.states[a].main_goal='solidarity'
    seller_option=next(x for x in s._proposals(a,[b]) if x[1]=='exchange_offer')
    s._do(a,seller_option,[b],Random(4),'decision-1')
    buyer_options=[x for x in s._proposals(b,[a])
                   if x[1] in ('exchange_accept','exchange_decline')]
    assert {x[1] for x in buyer_options}=={'exchange_accept','exchange_decline'}
    old=s.book.seq
    choice=next(x for x in buyer_options if x[1]=='exchange_accept')
    s._do(b,choice,[a],Random(9),'decision-2')
    assert s.counter['resource_agreement_received']==1
    assert owns_lot(s,b,'food',lot)
    assert s.book.seq==old+1
    audit(s)


def test_seller_can_voluntarily_withdraw_and_reoffer_unspent_food():
    s,_,_,a,b,lot=setup()
    s.founders.people['F003'].location='riverbank'
    old=s.book.seq
    original=offer_resource(s,a,b,'food',lot,decision_id='first')
    option=next(x for x in s._proposals(a,[b]) if x[1]=='exchange_withdraw')
    s._do(a,option,[b],Random(2),'withdraw-decision')
    assert s.founder_exchange_offers[original]['status']=='withdrawn'
    assert owns_lot(s,a,'food',lot)
    assert s.book.seq==old
    assert withdraw_offer(s,a,original) is None  # retry is free
    with pytest.raises(ValueError,match='not open'):
        decide_offer(s,b,original,True)
    revised=offer_resource(s,a,'F003','food',lot,decision_id='second')
    decide_offer(s,'F003',revised,True)
    assert owns_lot(s,'F003','food',lot)
    assert not owns_lot(s,a,'food',lot)
    assert s.book.seq==old+1
    audit(s)


def test_two_worlds_cannot_claim_same_ambiguous_physical_lot():
    """A portable lot ID without a World namespace must never choose a World."""
    from types import SimpleNamespace
    from founders_civ.core.founder_exchange import _origin
    from founders_civ.core.founder_nutrition import _tree_for_lot
    tree_a = SimpleNamespace(provisioning=None)
    tree_b = SimpleNamespace(provisioning=None)
    sim = SimpleNamespace(
        world_trees=SimpleNamespace(worlds={'W1': tree_a, 'W2': tree_b}),
        book=SimpleNamespace(operations={
            'food:make:W1:shared': object(),
            'food:make:W2:shared': object(),
            'fruit:grow:W1:shared': object(),
        }),
    )
    assert _origin(sim, 'food', 'shared') == (None, None)
    assert _tree_for_lot(sim, 'shared') == (None, None)
    assert _origin(sim, 'fruit', 'shared') == ('W1', tree_a)
    del sim.book.operations['food:make:W2:shared']
    assert _origin(sim, 'food', 'shared') == ('W1', tree_a)


def test_detached_tree_cannot_authenticate_shared_book_resource_origin():
    """A foreign Book must not authorize a World lot for exchange or ingestion."""
    from types import SimpleNamespace
    from founders_civ.core.founder_exchange import _origin
    shared = object()
    foreign = object()
    tree = SimpleNamespace(book=foreign, provisioning=None)
    sim = SimpleNamespace(book=shared, world_trees=SimpleNamespace(worlds={'W1': tree}))
    # An old provenance receipt in the authoritative Book is insufficient
    # when the currently registered World writes to a different Book.
    sim.book = SimpleNamespace(operations={'food:make:W1:lot': object()})
    tree.book = foreign
    assert _origin(sim, 'food', 'lot') == (None, None)
    tree.book = sim.book
    assert _origin(sim, 'food', 'lot') == ('W1', tree)

def test_offer_identity_replay_after_settlement_and_separation_is_side_effect_free():
    s, _, _, seller, buyer, lot = setup()
    oid = offer_resource(s, seller, buyer, 'food', lot, decision_id='stable-offer')
    decide_offer(s, buyer, oid, True)
    s.founders.people[buyer].location = 'ridge'
    before = (s.book.seq, dict(s.book.mass), dict(s.book.energy),
              len(s.events), len(s.founder_exchange_offers))
    assert offer_resource(s, seller, buyer, 'food', lot,
                          decision_id='stable-offer') == oid
    assert (s.book.seq, dict(s.book.mass), dict(s.book.energy),
            len(s.events), len(s.founder_exchange_offers)) == before
    with pytest.raises(ValueError, match='conflicting'):
        offer_resource(s, seller, buyer, 'fruit', lot,
                       decision_id='stable-offer')
    with pytest.raises(ValueError, match='meet'):
        offer_resource(s, seller, buyer, 'food', lot,
                       decision_id='new-offer')
    audit(s)


def test_settlement_and_decline_replay_after_recipient_death_without_new_transfer():
    """Past Book receipts survive later actor death; new acceptance does not."""
    s, _, _, seller, buyer, lot = setup()
    oid = offer_resource(s, seller, buyer, 'food', lot, decision_id='death-replay')
    receipt = decide_offer(s, buyer, oid, True)
    before = (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events))
    s.founders.people[buyer].alive = False
    assert decide_offer(s, buyer, oid, True) == receipt
    assert (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events)) == before
    with pytest.raises(ValueError, match='conflicting'):
        decide_offer(s, buyer, oid, False)
    audit(s)

    t, _, _, seller, buyer, lot = setup(seed=822)
    oid = offer_resource(t, seller, buyer, 'food', lot, decision_id='decline-replay')
    assert decide_offer(t, buyer, oid, False) is None
    t.founders.people[buyer].alive = False
    assert decide_offer(t, buyer, oid, False) is None
    with pytest.raises(ValueError, match='declined'):
        decide_offer(t, buyer, oid, True)
    audit(t)

    u, _, _, seller, buyer, lot = setup(seed=823)
    oid = offer_resource(u, seller, buyer, 'food', lot, decision_id='unsettled')
    u.founders.people[buyer].alive = False
    with pytest.raises(ValueError, match='active recipient'):
        decide_offer(u, buyer, oid, True)
    audit(u)


def test_withdrawn_offer_replay_after_seller_death_is_historical_not_new_action():
    """A prior voluntary withdrawal stays withdrawn after its author dies."""
    s, _, _, seller, buyer, lot = setup(seed=824)
    oid = offer_resource(s, seller, buyer, 'food', lot, decision_id='withdraw-death')
    assert withdraw_offer(s, seller, oid) is None
    before = (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events))
    s.founders.people[seller].alive = False
    assert withdraw_offer(s, seller, oid) is None
    assert s.founder_exchange_offers[oid]['status'] == 'withdrawn'
    assert (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events)) == before
    with pytest.raises(ValueError, match='not open'):
        decide_offer(s, buyer, oid, True)
    audit(s)

    t, _, _, seller, buyer, lot = setup(seed=825)
    oid = offer_resource(t, seller, buyer, 'food', lot, decision_id='still-open')
    t.founders.people[seller].alive = False
    with pytest.raises(ValueError, match='active seller'):
        withdraw_offer(t, seller, oid)
    assert t.founder_exchange_offers[oid]['status'] == 'open'
    audit(t)


def test_decline_cannot_carry_payment_or_change_historical_replay():
    """A refusal never carries physical payment, including on replay."""
    s, _, _, seller, buyer, lot = setup(seed=826)
    oid = offer_resource(s, seller, buyer, 'food', lot, 'fruit', decision_id='refuse-no-payment')
    before = (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events))
    with pytest.raises(ValueError, match='cannot transfer payment'):
        decide_offer(s, buyer, oid, False, 'fabricated-fruit')
    assert s.founder_exchange_offers[oid]['status'] == 'open'
    assert (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events)) == before
    assert decide_offer(s, buyer, oid, False) is None
    declined = (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events))
    s.founders.people[buyer].alive = False
    with pytest.raises(ValueError, match='cannot supply payment'):
        decide_offer(s, buyer, oid, False, 'fabricated-fruit')
    assert decide_offer(s, buyer, oid, False) is None
    assert (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events)) == declined
    audit(s)


def test_resource_agreement_cannot_self_deal_even_if_contact_layer_allows_it():
    """A Founder cannot manufacture a social exchange by transferring to self."""
    s, _, _, seller, buyer, lot = setup(seed=827)
    before = (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events))
    with pytest.raises(ValueError, match='distinct Founders'):
        offer_resource(s, seller, seller, 'food', lot, decision_id='self-deal')
    assert (s.book.seq, dict(s.book.mass), dict(s.book.energy), len(s.events)) == before
    assert not getattr(s, 'founder_exchange_offers', {})
    audit(s)
