"""Read-only provenance cross-check for bridge reproductive events and live pregnancy state.

A missing event is an observability discrepancy, never evidence of a miscarriage.
"""
from collections import Counter
from live_reproductive_audit_02131 import live_reproductive_audit


def audit_bridge_provenance(bridge, species='ridge_hound'):
    """Inspect the existing bridge Book-linked actors and append-only events; no step()."""
    day = bridge.day
    events = bridge.events
    actors = bridge.actors
    if not isinstance(day, int) or day < 0:
        raise ValueError('invalid bridge day')
    if not isinstance(events, list):
        raise TypeError('bridge events must be an event list')
    event_ids = [e.get('event_id') for e in events if isinstance(e, dict)]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError('duplicate event identifiers')
    summary = live_reproductive_audit(events, actors, day, species)
    pregnant = []
    for animal in actors.values():
        if (animal.species == species and animal.alive
                and getattr(animal, 'pregnant_until', None) is not None):
            pregnant.append({'mother': animal.id, 'due': animal.pregnant_until,
                             'father': getattr(animal, 'pregnancy_father', None)})
    conceptions = {e.get('mother') for e in events if isinstance(e, dict)
                   and e.get('species') == species and e.get('event', e.get('kind')) == 'conception'
                   and isinstance(e.get('day'), (int, float)) and e['day'] <= day}
    summary['provenance'] = {
        'event_store': 'bridge.events', 'actor_store': 'bridge.actors',
        'observation_clock': 'bridge.day', 'event_rows_total': len(events),
        'pregnant_live': sorted(pregnant, key=lambda x: x['mother']),
        'pregnant_without_recorded_conception': sorted(p['mother'] for p in pregnant if p['mother'] not in conceptions),
        'bridge_conception_events': sum(e.get('species') == species and e.get('event', e.get('kind')) == 'conception'
                                         for e in events if isinstance(e, dict)),
        'bridge_birth_events': sum(e.get('species') == species and e.get('event', e.get('kind')) == 'birth'
                                    for e in events if isinstance(e, dict)),
    }
    return summary
