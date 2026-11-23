from diagnose_replay_021124 import compare

def test_short_exact_replay():
 r=compare(days=31)
 assert r['events_match'] and r['book_mass_match'] and r['book_energy_match']
 assert r['first_difference'] is None

def test_invalid_window():
 try:compare(days=30)
 except ValueError:pass
 else:raise AssertionError('invalid checkpoint accepted')
