"""Run any validated WORLD-024 scenario + optional trusted extension hooks.

Examples:
 python run_integration_025.py examples/scenarios/commons.json --out results/integration_025.json
 python run_integration_025.py examples/scenarios/harvest_pressure.json
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from founders_civ.integration import ScenarioSpec,IntegrationHost
from founders_civ.integration.compat import check, reviewed_check
from founders_civ.integration.extensions import resolve_extensions

def main():
 p=argparse.ArgumentParser()
 p.add_argument('scenario',type=Path)
 p.add_argument('--out',type=Path)
 p.add_argument('--check-hashes',action='store_true')
 p.add_argument('--allow-local-code',action='store_true',help='Load reviewed local Python modules from scenario extensions')
 a=p.parse_args()
 root=Path(__file__).parent
 if a.check_hashes:
  baseline=root/'docs/INTEGRATION_025/BASELINE_HASHES.json'
  review=next((p for p in (root/'docs/INTEGRATION_025/APPROVED_DRIFT_C004.json',
                           root/'docs/INTEGRATION_025/APPROVED_DRIFT_C003.json',
                           root/'docs/INTEGRATION_025/APPROVED_DRIFT_C002.json',
                           root/'docs/INTEGRATION_025/APPROVED_DRIFT_C001.json')
               if p.is_file()),root/'docs/INTEGRATION_025/APPROVED_DRIFT_C001.json')
  state=reviewed_check(root,baseline,review) if review.is_file() else check(root,baseline)
  if state['status'] not in ('compatible_fingerprint','approved_drift'):
   raise SystemExit('Source drift not approved: '+','.join(state.get('unapproved_files',state['changed_files'])))
 spec=ScenarioSpec.from_file(a.scenario)
 extensions=resolve_extensions(spec.extensions,allow_local_code=a.allow_local_code)
 result=IntegrationHost(spec,extensions=extensions).run()
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2),encoding='utf8')
 print(json.dumps({'seed':spec.seed,'cycles':spec.cycles,'tree_state':result['final_observation']['shared_tree_state'],
  'population':result['final_observation']['shared_tree_population'],'events':result['events_forwarded'],
  'ledger':result['summary']['conservation']},indent=2))

if __name__=='__main__':main()
