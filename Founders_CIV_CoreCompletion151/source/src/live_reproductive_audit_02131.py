"""Read-only snapshot of reproductive opportunity and observed outcomes.

No state mutation, new Book, energy transfers, or inferred births.
"""
from collections import Counter
from reproductive_cohort_outcomes_02129 import cohort_outcomes


def live_reproductive_audit(events, actors, observation_day, species='ridge_hound', ledger_rejections=0):
    if observation_day < 0:
        raise ValueError('observation_day must be nonnegative')
    if ledger_rejections < 0:
        raise ValueError('ledger_rejections must be nonnegative')
    relevant = [e for e in events if isinstance(e, dict)
                and e.get('species') == species
                and isinstance(e.get('day'), (int, float))
                and e['day'] <= observation_day]
    kinds = Counter(e.get('kind', e.get('type', e.get('event', 'unknown'))) for e in relevant)
    causes = Counter((e.get('cause') or 'unknown') for e in relevant
                     if e.get('kind', e.get('type')) == 'death')
    # Snapshot counts are descriptive only: no assertion that these actors are native WORLD residents.
    sex = Counter()
    for actor in actors.values() if isinstance(actors, dict) else actors:
        if getattr(actor, 'species', None) == species and getattr(actor, 'alive', True):
            sex[getattr(actor, 'sex', 'unknown')] += 1
    return {'species': species, 'day': observation_day, 'event_counts': dict(kinds),
            'death_causes': dict(causes), 'living_by_sex': dict(sex),
            'pregnancies': cohort_outcomes(relevant, observation_day, species),
            'ledger_rejections': ledger_rejections}
