# INTEGRATION-025 — Extensibility & Compatibility SDK

Status: **working experimental adapter over WORLD-024**, not a v0.25 replacement engine or full physical API.

The SDK is deliberately additive. It uses the actual `CommonsWorld` and the existing `run_world_tree_pilot.bootstrap` (including reviewed Realm, World and Species Seeds), the original `Book`, the 100-actor social scheduler, and the four-habitat World Tree. No separate world simulator or ledger is created.

## What is shipped

| Component | Path | Purpose |
|---|---|---|
| Versioned configuration | `founders_civ/integration/contracts.py` | `ScenarioSpec`, `StressWindow`, strict schema v1.0 |
| Extension host | `founders_civ/integration/host.py` | Builds real WORLD-024 scenario, calls observational hooks; stable event IDs |
| Cross-branch inspection | `founders_civ/integration/branches.py` | Read-only normalized views of SOCIAL-021, WORLD-022/023 and WORLD-024 instances |
| Trusted local plugin loading | `founders_civ/integration/extensions.py` | Built-ins by default; optional explicitly approved `module:Class` |
| Source fingerprinting | `founders_civ/integration/compat.py` | Hashes critical files, warns when source drifts |
| Scenario CLI | `run_integration_025.py` | Run variant with plugins and export provenance-rich JSON |
| Comparison CLI | `run_compat_matrix_025.py` | Matched seeds/durations across 8 established variants |
| Tests | `tests/test_integration_025.py` | Config constraints, physical integrity, replay, extension contract |
| Examples | `examples/scenarios/` and `examples/extensions/` | Composable scenario files; review-before-loading example |

## Quick start

```powershell
python -m unittest tests.test_integration_025 -v
python run_integration_025.py examples/scenarios/commons.json --check-hashes --out results/integration_025/commons.json
python run_integration_025.py examples/scenarios/harvest_pressure.json --out results/integration_025/harvest.json
python run_compat_matrix_025.py --seeds 820 821 --cycles 6 --out results/integration_025/matrix.csv
```

Run the old suites unchanged:

```powershell
python -m unittest discover -s tests -q
python -m unittest discover -s . -p 'test*.py' -q
```

## Extension contract

Import `Extension` and subclass it. Override only the hook(s) you need:

```python
from founders_civ.integration import Extension
class MyReport(Extension):
    id = 'my_report'
    api_version = '1.0'
    def __init__(self): self.total = 0
    def on_event(self, event):
        if event.action == 'creation_collapsed': self.total += 1
    def report(self): return {'collapses_seen': self.total}
```

Hooks: `on_start(observation)`, `on_event(event)`, `on_cycle(observation)`, `on_finish(observation)`, `report()`. Observations are frozen value objects, not the `Book` or live mutable agents. Events have *source-scoped IDs*: `founder:SOC-…`, `ecology:…`; event identity does not assume all clocks are globally ordered within one tick. `transaction_id` may be `None` for informational events. `payload_json` preserves the original source event details as a serialized string. Hooks receive only **post-bootstrap** events; the setup records remain available in the underlying engine but are not re-emitted as new decisions. Missing parent IDs remain missing rather than fabricated.

To load reviewed custom Python from `examples/extensions/archival_monitor.py`, add `"examples.extensions.archival_monitor:ArchiveMonitor"` to the `extensions` array in a scenario file and run the scenario with `--allow-local-code`. **Never load untrusted extension modules**: they execute ordinary Python in your operating system. This is not a security sandbox.

## Scenario variation contract

The following are compatible today: `governance` (`collective`, `owner`, `fragmented`, `none`), `extraction` (`careful`, `intensive`, `none`), `social_mode` (`full`, `no_partner`, `no_teach`, `no_faction`, `neutral_trust`, `isolated`), `allow_private` (Boolean), and time-limited `StressWindow` entries (`upkeeps`, `rainfall`, `disease`, `founder_drain`). All are passed to the real WORLD-024 policy. Matched seeds/durations permit comparisons but do not isolate every causal mechanism; calibrate before inferring social science.

## Compatibility guarantee — and limits

- CORE-018 (`Book`) is the only material/energy authority. Do not modify `Book` balances from plugin hooks.
- WORLD-024 is runnable through this SDK. Other branches support **read-only normalized inspection**, not behavioral hot-swapping.
- The starter population is initialized through a *scripted but real* reviewed seed workflow. Autonomous Founders act after bootstrap.
- `export_snapshot()` is a **read-only export**, not a resume/rollback checkpoint. Existing Founder checkpoint logic remains in the actual engine.
- Unknown schema fields, API versions, social modes, governance types and invalid stress settings are rejected before simulation.
- Fingerprints help catch accidental code drift. They are not substitutes for behavioral tests or human code review.
- World-Tree collapse is an expected ecological outcome, not a test failure. A failed ledger, broken event identity, unhandled exception or duplicate Founders is an engineering failure.
- Physical geography remains a graph and schematic UI. Portable food embodied-energy, timber exports, functional Underworld Flowers, mature institutions and calibrated cognition remain open work.

## Integration process for new code

1. Branch from WORLD-024 + INTEGRATION-025; preserve original `founders_civ/core/ledger.py` unless conservation migration is separately reviewed.
2. Create a change proposal with `docs/INTEGRATION_025/CHANGE_PROPOSAL_TEMPLATE.md` and name the touched system, version, events and ledger accounts.
3. Add an optional module with a stable `id`, explicit schema version and dependencies. Start observational; add physical actions only through reviewed engine methods with `Book` transactions and acceptance tests.
4. Create new deterministic scenario files and matched-seed controls; preserve collapse and deliberate failure trajectories.
5. Compare hash manifest, run inherited and new test suites, reproduce experiment CSV, then update `DEVLOG_SOCIAL_WORLD.md` and any canonical specifications.
6. Promote to master only after explicit review of state migration, clock consistency, source/actor IDs, and rollback behavior.

## Practical next integrations

**High priority:** transferable food with embodied energy; tree-origin building materials; stewardship contracts and budgets; multiactor task delegation with trust-weighted risk. **Next:** realistic knowledge prerequisites and forgetting; independently verified historical Founder roster; multispecies ecology and calibrated slow population dynamics. **Later:** true spatial Sea navigation, alternative Soul systems, dimensions, Underworld Flowers, and multi-realm governance.
