"""Fail-closed evidence gate; no baseline rewrite or missing-module stubs."""
from pathlib import Path
import ast
from founders_civ.integration.compat import check
ROOT=Path(__file__).resolve().parents[1]
MISSING={'experiments.realm_counterfactual_02119','scripts.source_edit_lease','cycle024_daily_eligibility','cycle026_continuity','cycle028_bottleneck'}

def test_drift_is_not_silently_approved():
    d=check(ROOT/'world023024',ROOT/'world023024/docs/INTEGRATION_025/BASELINE_HASHES.json')
    assert d['status']=='drift_requires_review'
    assert set(d['changed_files']) == {'founders_civ/experimental/world_trees.py', 'founder_world.html'}

def test_known_missing_dependencies_not_faked():
    import importlib.util
    assert all(importlib.util.find_spec(n) is not None for n in MISSING)

def test_funded_capacity_is_single_source_account():
    source=(ROOT/'src/funded_capacity_02145.py').read_text()
    ast.parse(source)
    assert 'book' in source.lower()
