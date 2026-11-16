"""U026-C019: opt-in autonomy, subjective value and evidence-based learning.

The engine may offer care, creation, trade, food and exploration as genuine
alternatives. It must never automatically *mandate* care for a Tree or Realm.
Founder valuations are private, bounded, heterogeneous and updated only from
personal experience; world collapse and refusing upkeep remain legal outcomes.
No Book account, energy, matter, CE, time currency or WorldBox actor is created.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import blake2b
from math import isfinite


CARE = frozenset(('parent_steward', 'tree_tend', 'creation_steward', 'seed_tend'))
INSPECT = frozenset(('parent_inspect', 'tree_observe', 'food_scan'))
MAKE = frozenset(('seed_design', 'seed_research', 'seed_request_review', 'seed_fund', 'seed_plant'))


@dataclass
class FounderValuation:
    """A personal, checkpointable *estimate*, never universal utility."""
    care_preference: float
    resource_preference: float
    creation_preference: float
    learning_preference: float
    believed_tree_value: float = 0.
    believed_care_value: float = 0.
    believed_creation_value: float = 0.
    experience_count: int = 0
    event_cursor: int = 0
    recent_experiences: list[str] = field(default_factory=list)


def _bound(value):
    if not isfinite(value):
        raise ValueError('nonfinite private Founder value')
    return max(-1., min(1., value))


def _variation(seed, founder):
    digest = blake2b(f'{seed}|{founder}|valuation'.encode(), digest_size=8).digest()
    return (int.from_bytes(digest, 'big') / (2**64 - 1) - .5) * .44


def personal_values(sim, founder):
    """Seed individual predispositions from *existing* social traits and goals."""
    if not hasattr(sim, 'founder_valuations'):
        sim.founder_valuations = {}
    if founder not in sim.founder_valuations:
        s = sim.states[founder]
        variation = _variation(sim.seed, founder)
        sim.founder_valuations[founder] = FounderValuation(
            care_preference=_bound(.50*s.empathy + .35*s.caution - .44 + variation),
            resource_preference=_bound(.50*s.caution + .2*s.ambition - .33 - variation*.5),
            creation_preference=_bound(.48*s.ambition + .32*s.curiosity - .40 + variation),
            learning_preference=_bound(.53*s.curiosity - .28 - variation*.4),
        )
    return sim.founder_valuations[founder]


def observe_personal_outcomes(sim, founder):
    """Learn only from events *experienced by this Founder*.

    In particular, a global `creation_collapsed` event does not teach an
    absent Founder what happened. They may later discover it themselves.
    """
    memory = personal_values(sim, founder)
    for event in sim.events[memory.event_cursor:]:
        if event.get('actor') != founder:
            continue
        name = event['action']
        tree_delta = care_delta = creation_delta = 0.
        if name == 'tree_observed':
            # These quantities were measured at a physical observatory.
            tree_delta = .14 if event.get('measured_biomass', 0) > 0 else -.10
        elif name == 'founder_food_scan':
            tree_delta = .20 if event.get('visible_lots', 0) > 0 else -.07
        elif name == 'tree_founder_harvest':
            tree_delta = .35 if event.get('resource_kind') == 'food' else .27
            creation_delta = .17 if event.get('resource_kind') == 'fruit' else 0.
        elif name in ('founder_food_ingested', 'founder_food_digested'):
            tree_delta = .18
        elif name == 'seed_planted':
            creation_delta = .42
        elif name in ('founder_parent_realm_tended', 'creation_autonomous_stewardship',
                      'tree_autonomous_maintenance'):
            # Choosing to spend fuel is not proof that spending was worthwhile.
            care_delta = -.07
        elif name == 'world_action_rejected':
            attempted = event.get('attempted')
            if attempted in CARE:
                care_delta = -.19
            elif attempted in MAKE:
                creation_delta = -.16
            elif attempted in ('tree_harvest', 'food_ingest', 'food_digest'):
                tree_delta = -.11
        if not (tree_delta or care_delta or creation_delta):
            continue
        memory.believed_tree_value = _bound(memory.believed_tree_value + tree_delta)
        memory.believed_care_value = _bound(memory.believed_care_value + care_delta)
        memory.believed_creation_value = _bound(memory.believed_creation_value + creation_delta)
        memory.experience_count += 1
        memory.recent_experiences.append(name)
        if len(memory.recent_experiences) > 12:
            del memory.recent_experiences[:-12]
    memory.event_cursor = len(sim.events)
    return memory


def value_proposals(sim, founder, proposals):
    """Adjust *relative* scores; never remove permission or override choice.

    High urgency in the existing stewardship policy is information about a
    possible proposal, not a command. Re-center those scores so any Founder
    may decline, explore, make a Tree, or attempt something else instead.
    """
    if not getattr(sim, 'founder_autonomy_learning_enabled', False):
        return proposals
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        return []
    m = observe_personal_outcomes(sim, founder)
    scored = []
    for raw, action, target, meta in proposals:
        if action in CARE:
            # Preserve real urgency as a *small* influence, not the 6+ hard
            # priority that previously made stewardship near-mandatory.
            urgency = min(1., max(0., (raw - 3.0) / 4.5))
            score = .95 + 1.25*urgency + 1.3*m.care_preference + \
                1.25*m.believed_care_value + .42*m.believed_tree_value
        elif action == 'parent_inspect':
            score = 1.75 + .75*m.learning_preference + .30*m.believed_tree_value
        elif action in ('tree_observe', 'tree_research', 'food_scan'):
            score = 1.30 + .72*m.learning_preference + .42*m.believed_tree_value
        elif action in MAKE:
            score = max(-.6, min(2.1, raw*.36 + .80*m.creation_preference +
                                 1.1*m.believed_creation_value + .25*m.believed_tree_value))
        elif action in ('tree_harvest', 'food_ingest', 'food_digest'):
            score = max(-.6, min(2.5, raw*.53 + .75*m.resource_preference +
                                 .65*m.believed_tree_value))
        else:
            score = raw  # preserve unrelated voluntary social and survival work
        scored.append((score, action, target, meta))
    # No energy, action points, time tokens, reserve transfer or forced upkeep.
    # A Founder can decline even when the Tree has virtually no reserve.
    scored.append((.62 + .23*(1-m.care_preference), 'decline_investment', None, None))
    return scored
