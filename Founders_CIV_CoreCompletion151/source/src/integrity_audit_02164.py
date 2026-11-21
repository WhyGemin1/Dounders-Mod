"""Read-only audit of release fingerprint and missing source-test dependencies."""
from pathlib import Path
import hashlib,json,ast

def audit(root):
    root=Path(root)
    wt=root/'world023024'
    expected=json.loads((wt/'docs/INTEGRATION_025/BASELINE_HASHES.json').read_text())['hashes']
    observed={p:hashlib.sha256((wt/p).read_bytes()).hexdigest() if (wt/p).exists() else None for p in expected}
    changed={p:{'expected':expected[p],'actual':observed[p]} for p in expected if expected[p]!=observed[p]}
    modules={'experiments.realm_counterfactual_02119':'src/experiments/realm_counterfactual_02119.py',
             'scripts.source_edit_lease':'src/scripts/source_edit_lease.py',
             'cycle024_daily_eligibility':'src/experiments/cycle024_daily_eligibility.py',
             'cycle026_continuity':'src/experiments/cycle026_continuity.py',
             'cycle028_bottleneck':'src/experiments/cycle028_bottleneck.py'}
    missing=[name for name,p in modules.items() if not (root/p).is_file()]
    return {'fingerprint_changed':changed,'missing_source_dependencies':missing,'tracked_files':len(expected)}
