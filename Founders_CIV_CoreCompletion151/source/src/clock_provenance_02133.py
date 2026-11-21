"""Read-only WORLD-023 bootstrap-relative clock audit. No new clock or ledger."""

def clock_provenance(sim):
    host=sim.host
    absolute=host.sim.tick
    bootstrap=host.bootstrap_tick
    bridge_day=sim.bridge.day
    elapsed=sim.days
    return {
        'absolute_tick': absolute,
        'bootstrap_tick': bootstrap,
        'host_elapsed': absolute-bootstrap,
        'bridge_day': bridge_day,
        'unified_days': elapsed,
        'ecology_day': host.sim.ecology.day,
        'clock_consistent': (absolute==host.sim.ecology.day and
                             absolute-bootstrap==elapsed==bridge_day),
        'book_shared': host.book is host.sim.book is sim.bridge.book,
    }

def assert_clock_provenance(sim):
    result=clock_provenance(sim)
    if not result['clock_consistent'] or not result['book_shared']:
        raise AssertionError(f'world clock/book divergence: {result}')
    return result
