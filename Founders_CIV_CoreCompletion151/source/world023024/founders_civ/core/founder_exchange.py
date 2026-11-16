"""U026-C020: genuinely voluntary Founder resource agreements.

Offers are information, not a new ledger or automatic transfers. Each settled
agreement is one Book.move transaction containing whole identified physical
food/fruit lots and their paired (distinct) chemical energy / Creation Energy.
No action points, minted food, trade currency, new fuel source, or native WorldBox
writes. The other Founder may accept, decline, or ignore the offer.
"""
from __future__ import annotations

from math import isfinite

KINDS = {"food": ("portable_food", "food_energy", .08, .02),
         "fruit": ("fruit", "ce:fruit", .10, 1.0)}


def holdings(book, kind, lot, founder):
    mass, energy, qty, charge = KINDS[kind]
    return (f"{mass}:lot:{lot}:founder:{founder}",
            f"{energy}:lot:{lot}:founder:{founder}", qty, charge)


def _data(sim):
    if not hasattr(sim, 'founder_exchange_offers'):
        sim.founder_exchange_offers = {}
    if not hasattr(sim, 'founder_exchange_counter'):
        sim.founder_exchange_counter = 0
    return sim.founder_exchange_offers


def _active(sim, actor):
    person = sim.founders.people.get(actor)
    return person is not None and person.alive


def _origin(sim, kind, lot):
    for tid, tree in sorted(sim.world_trees.worlds.items()):
        if tree.provisioning is not None and lot in tree.provisioning.lots:
            if tree.provisioning.lots[lot].kind == kind:
                return tid, tree
        # Some real Book-funded lots are made directly through TreeResourceOps
        # outside the C003 automatic provisioning loop. They remain authentic.
        provenance = (f'food:make:{tid}:{lot}' if kind=='food'
                      else f'fruit:grow:{tid}:{lot}')
        if provenance in sim.book.operations:
            return tid, tree
    return None, None


def owns_lot(sim, founder, kind, lot):
    """Book balance AND prior acquired identity, never an arbitrary claim."""
    if not _active(sim, founder) or kind not in KINDS or not isinstance(lot, str):
        return False
    if _origin(sim, kind, lot)[0] is None:
        return False
    source_m, source_e, qty, charge = holdings(sim.book, kind, lot, founder)
    if sim.book.mass.get(source_m, 0) < qty - 1e-8 or sim.book.energy.get(source_e, 0) < charge - 1e-8:
        return False
    if f'{kind}:harvest:{lot}:{founder}' in sim.book.operations:
        return True
    return any(o['status'] == 'accepted' and o['receiver'] == founder
               and o['lot'] == lot and o['kind'] == kind
               for o in _data(sim).values()) or any(
        o['status'] == 'accepted' and o['seller'] == founder
        and o.get('payment_lot') == lot and o.get('wanted_kind') == kind
        for o in _data(sim).values())


def owned_lots(sim, founder, kind):
    """Inspect only self-acquired holdings; never scan another owner's stock."""
    if not _active(sim, founder) or kind not in KINDS:
        return []
    suffix = ':' + founder
    prefix = f'{kind}:harvest:'
    lots = set()
    for key in sim.book.operations:
        if key.startswith(prefix) and key.endswith(suffix):
            lots.add(key[len(prefix):-len(suffix)])
    for offer in _data(sim).values():
        if offer['status'] != 'accepted':
            continue
        if offer['kind'] == kind and offer['receiver'] == founder:
            lots.add(offer['lot'])
        if offer['wanted_kind'] == kind and offer['seller'] == founder:
            lots.add(offer['payment_lot'])
    return sorted(lot for lot in lots if owns_lot(sim, founder, kind, lot))


def _contact(sim, a, b):
    return _active(sim, a) and _active(sim, b) and sim._contact(a, b)


def offer_resource(sim, seller, receiver, kind, lot, wanted_kind=None, decision_id=None):
    """Seller proposes an explicit gift or whole-lot barter. No Book mutation."""
    if not getattr(sim, 'founder_exchange_enabled', False):
        raise ValueError('resource agreements disabled')
    if not _contact(sim, seller, receiver):
        raise ValueError('Founders must meet to offer resources')
    if kind not in KINDS or wanted_kind not in (None, *KINDS):
        raise ValueError('unsupported resource kind')
    if wanted_kind == kind:
        raise ValueError('exchange must provide a distinct resource kind')
    if not isinstance(lot, str) or not owns_lot(sim, seller, kind, lot):
        raise ValueError('seller lacks identified Book-owned lot')
    if decision_id is None:
        decision_id = getattr(sim, '_current_parent', None)
    if not isinstance(decision_id, str) or not 1 <= len(decision_id) <= 72:
        raise ValueError('explicit offer decision identity required')
    offers = _data(sim)
    offer_id = f'X:{seller}:{decision_id}'
    if offer_id in offers:
        old = offers[offer_id]
        if (old['seller'], old['receiver'], old['kind'], old['lot'], old['wanted_kind']) != (
                seller, receiver, kind, lot, wanted_kind):
            raise ValueError('conflicting offer decision replay')
        return offer_id
    if any(o['status']=='open' and o['seller']==seller and o['kind']==kind and o['lot']==lot
           for o in offers.values()):
        raise ValueError('lot already offered by this Founder')
    offers[offer_id] = dict(id=offer_id, seller=seller, receiver=receiver, kind=kind,
                            lot=lot, wanted_kind=wanted_kind, payment_lot=None,
                            status='open', offered_at=sim.tick)
    sim.log('resource_agreement_offered', seller,
            parent=getattr(sim, '_current_parent', None),
            offer_id=offer_id, receiver=receiver, resource_kind=kind,
            wanted_kind=wanted_kind)
    return offer_id


def _legs(kind, lot, source, destination):
    source_m, source_e, qty, charge = holdings(None, kind, lot, source)
    dest_m, dest_e, _, _ = holdings(None, kind, lot, destination)
    return ((source_m, dest_m, qty), (source_e, dest_e, charge))


def decide_offer(sim, receiver, offer_id, accept, payment_lot=None):
    """The recipient may reject for free or accept atomic Book-funded barter.

    Replaying a settlement uses the same Book operation signature, and an
    altered payment lot cannot silently receive a cached successful receipt.
    """
    if not getattr(sim, 'founder_exchange_enabled', False):
        raise ValueError('resource agreements disabled')
    if not isinstance(offer_id, str) or not isinstance(accept, bool):
        raise ValueError('invalid agreement decision')
    offer = _data(sim).get(offer_id)
    if offer is None or offer['receiver'] != receiver or not _active(sim, receiver):
        raise ValueError('offer not addressed to active recipient')
    if offer['status'] == 'declined':
        if accept:
            raise ValueError('declined agreement cannot be accepted')
        return None
    if offer['status'] == 'accepted':
        if not accept or payment_lot != offer['payment_lot']:
            raise ValueError('conflicting agreement replay')
        mat1, energy1 = _legs(offer['kind'], offer['lot'], offer['seller'], receiver)
        mats, energies = [mat1], [energy1]
        if offer['wanted_kind'] is not None:
            mat2, energy2 = _legs(offer['wanted_kind'], payment_lot, receiver, offer['seller'])
            mats.append(mat2); energies.append(energy2)
        return sim.book.move(material=mats, energy=energies, operation_id=f'exchange:settle:{offer_id}')
    if offer['status'] != 'open':
        raise ValueError('offer is not open')
    if not accept:
        offer['status'] = 'declined'
        sim.log('resource_agreement_declined', receiver,
                parent=getattr(sim, '_current_parent', None), offer_id=offer_id,
                seller=offer['seller'])
        return None
    if not _contact(sim, offer['seller'], receiver):
        raise ValueError('both Founders must meet to settle resources')
    if not owns_lot(sim, offer['seller'], offer['kind'], offer['lot']):
        raise ValueError('seller no longer owns offered resource')
    if offer['wanted_kind'] is None:
        if payment_lot is not None:
            raise ValueError('gifts cannot demand a payment lot')
    elif not isinstance(payment_lot, str) or not owns_lot(sim, receiver, offer['wanted_kind'], payment_lot):
        raise ValueError('recipient lacks agreed physical barter resource')
    mat1, energy1 = _legs(offer['kind'], offer['lot'], offer['seller'], receiver)
    mats, energies = [mat1], [energy1]
    if offer['wanted_kind'] is not None:
        mat2, energy2 = _legs(offer['wanted_kind'], payment_lot, receiver, offer['seller'])
        mats.append(mat2); energies.append(energy2)
    txn = sim.book.move(material=mats, energy=energies, operation_id=f'exchange:settle:{offer_id}')
    offer['status'] = 'accepted'
    offer['payment_lot'] = payment_lot
    sim.log('resource_agreement_received', receiver,
            parent=getattr(sim, '_current_parent', None), txn=txn,
            seller=offer['seller'], offer_id=offer_id, resource_kind=offer['kind'],
            received_lot=offer['lot'])
    sim.log('resource_agreement_provided', offer['seller'], txn=txn,
            receiver=receiver, offer_id=offer_id, wanted_kind=offer['wanted_kind'])
    return txn


def propose_exchange(sim, founder, contacts):
    """Chance to offer, accept or refuse. Never force all Founders to cooperate."""
    if not getattr(sim, 'founder_exchange_enabled', False) or not _active(sim, founder):
        return []
    offers = _data(sim)
    s = sim.states[founder]
    proposals = []
    for offer_id, offer in sorted(offers.items()):
        if offer['status'] != 'open' or offer['receiver'] != founder:
            continue
        if not _contact(sim, offer['seller'], founder):
            continue
        payment = None
        if offer['wanted_kind'] is not None:
            payments = owned_lots(sim, founder, offer['wanted_kind'])
            if payments:
                payment = payments[0]
            else:
                # Unable to pay is still an informed opportunity to refuse,
                # not a command or a hidden automatic cancellation.
                proposals.append((1.0 + .25*s.caution, 'exchange_decline',
                                  offer['seller'], offer_id))
                continue
        score = 2.4 + (.7 if offer['kind']=='food' and sim.book.energy.get(f'founder:{founder}',0)<.5 else 0)
        score += .55 if offer['kind']=='fruit' and s.main_goal in ('research','exploration') else 0
        proposals.append((score, 'exchange_accept', offer['seller'], (offer_id, payment)))
        proposals.append((.8 + .25*s.caution, 'exchange_decline', offer['seller'], offer_id))
    if contacts and not any(o['status']=='open' and o['seller']==founder for o in offers.values()):
        # No centralized obligation to share; supply comes ONLY from owned lots.
        owned_food = owned_lots(sim, founder, 'food')
        owned_fruit = owned_lots(sim, founder, 'fruit')
        if owned_food or owned_fruit:
            gift = s.main_goal=='solidarity' or sim.founders.people[founder].partner_id in contacts
            # Choose what to part with; fruit retains real opportunity cost.
            kind, lot = ('food', owned_food[0]) if owned_food else ('fruit',owned_fruit[0])
            recipient = sorted(contacts)[0]
            request = None if gift else ('fruit' if kind=='food' else 'food')
            score = (1.8 if gift else 1.15) + .6*s.empathy
            proposals.append((score, 'exchange_offer', recipient, (kind,lot,request)))
    return proposals
