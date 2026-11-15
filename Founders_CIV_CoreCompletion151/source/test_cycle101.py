from pathlib import Path
import ast

def test_full_factorial_switches():
 t=Path(__file__).with_name('run_cycle101.py').read_text()
 for s in ('itertools.product','(4,8)','(0.0,0.5)','(False,True)','family_benefits=family','resource_aware_family=family','counts={k:density*2','capacity_scale=capacity'):
  assert s in t

def test_book_conservation_asserted():
 t=Path(__file__).with_name('run_cycle101.py').read_text()
 assert "row['mass_error']" in t and "row['energy_error']" in t and "row['rejections']==0" in t
