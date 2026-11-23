from pathlib import Path
import ast

def test_factorial_has_all_three_independent_switches():
 t=ast.parse(Path(__file__).with_name('run_cycle100.py').read_text())
 assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='product' for n in ast.walk(t))
 text=Path(__file__).with_name('run_cycle100.py').read_text()
 for name in ('maturation_feeding=nutrition','scheduled_funding=capacity','juvenile_refuge=refuge'):
  assert name in text
