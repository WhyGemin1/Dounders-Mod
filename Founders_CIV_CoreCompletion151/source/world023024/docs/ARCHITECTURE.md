# Founders-CIV v0.18 — Code architecture and extension contracts

## 1. Delivery structure

```
Founders_CIV_v018_Canon_Observatory/
├── START_DASHBOARD.bat                 # double-click on Windows
├── RUN_TESTS.bat                        # Windows test launch
├── launch.py                            # localhost Python server
├── run_simulation.py                    # Python command-line runner
├── founders_civ/
│   ├── canon.py                         # authoritative canon + readiness register
│   ├── core/
│   │   ├── ledger.py                    # authoritative atomic material/energy balances
│   │   └── engine.py                    # v0.17 integrated simulation core
│   ├── observatory.py                   # read-only simulation snapshots, event exports
│   ├── runner.py                        # CLI/JSON/CSV writer
│   └── server.py                        # localhost-only API, Python stdlib
├── web/
│   ├── index.html
│   ├── styles.css
│   ├── app.js                            # animated 2D Canvas viewer, data inspection
│   └── sample_run.json                   # real executed 30-day seed-42 trace
├── docs/
│   ├── CANONICAL_SYSTEMS.md / .docx
│   ├── ARCHITECTURE.md
│   └── V016_INTEGRATION_BLUEPRINT.md
├── tests/                                # release regression and conservation checks
├── results/                              # generated simulation traces, can be removed
└── archive/                              # reference code only; not imported by release
```

## 2. Trusted authoritative state

- Material and energy: `core.ledger.Book.mass` and `Book.energy`. No visualization or belief system creates material/energy.
- Actors: `core.engine.Simulation.actors`; `Agent` holds identity, species, needs, memories, skills, goals, learned nodes, current patch.
- Relationships: directed `Simulation.edges`, indexed by learner/target ID.
- Institutions: `Simulation.institutions` and `Simulation.pending`, created by pledged resource transfers.
- Events: `Simulation._record`; each physical event carries a ledger transaction ID.
- Read-only view: `ObservatorySimulation.capture` after each day. Browser may interpolate dots but does not update physical state.

## 3. Time update pipeline

1. `Simulation.step` advances clock; Wellspring adds energy, Underworld propagates return, sunlight is charged against House.
2. Growth occurs as an abstract soil->plant state transition, paying one transformation toll.
3. Actors expend food/energy in metabolism, with material and energy transaction details.
4. Actors assess feasible actions; ecological creatures forage/migrate/hunt/scavenge, creations consider needs, Fear Logic, teaching and institutions.
5. Transactions commit atomically; events record the action and any observer links.
6. Experiences change memory, expectations, skills, and preliminary Soul Network Nodes.
7. Institutions store members, pooled food, rules, monitoring and shared norms.
8. Observatory samples authoritative state once per day; records snapshots, institutions, and selected event metadata.

## 4. Observable vs unimplemented

The UI draws an animated **diagrammatic** 2D map. Underlying simulation positions are one of four named patches in each world, not a continuous x/y coordinate. All actor dot offsets are stable hashes used only for display. Animated ray and river decoration does not create in-world energy or water. The dashboard's actor 'final skills' and belief records are end-of-run values, not day-specific histories; energy/needs are day-specific. Only 2 Founders are represented; 100-Founder checkpoint rules, reproduction, elemental chemistry, full social roles, advanced Soul Arts, and independent institutions are not implemented. See `canon.py` for rule-by-rule status.

## 5. Configuration

`S F B I` arm flags: e.g. `1111` all active, `0000` all inactive.

```
py run_simulation.py --days 30 --seed 42 --arm 1111 --output results/my_run
py launch.py
```

Dashboard opens at `http://127.0.0.1:8765` and can start another simulation of 1–180 days. CLI can run 1–720 days. Dashboard uses a standard-library HTTP service bound to local loopback only; no cloud/API costs. For experiment-grade results, run specific matched seeds and retain raw files; the 480-run registered study is **not** triggered by opening the dashboard.

## 6. Canon vs parameters

`founders_civ.canon.SYSTEMS` stores canon rules and implementation status. `core.engine.SPECIES` stores **provisional numeric experiment parameters**, not locked world law. The demonstration toll of 10% work and allocation of 20% world, 10% Underworld, 70% House are illustrative. Updating one of these must create a new code version and explicit sensitivity tests. Do not silently change an implemented mechanic to make a hypothetical outcome look good.

## 7. Adding a new system safely

1. Add a canon register entry with explicit status, rule, code path and gap.
2. Write independently testable transaction/decision rules; avoid direct changes to another subsystem's stock.
3. Add event types and source IDs; claims about learning require remembered sources and qualifying practice.
4. Add a unittest for both valid and invalid transactions, same-seed reproducibility and counterfactual behavior.
5. Update Observatory serialization and UI indicators. UI is read-only, not authoritative.
6. Test 1-day, 30-day, and 120-day scenarios; freeze parameters before confirmatory matched-seed studies.

## 8. Integration gates and failure criteria

- Material total constant in closed systems; energy total grows only through explicitly accounted Wellspring input.
- Transformations pay toll exactly once; moves of a location or ownership do not pay toll.
- Not allowed: skill acquisition from claim exposure alone; bonus crop yields directly from belief; institutions without identified members and pooled resources.
- Findings must be expressed as properties of **this synthetic implementation**, not as direct sociological or ecological truth.
- Do not interpret 120-day adult predator persistence as a viable food web until births, juvenile survival, and multi-generation stocks are implemented.

## 9. Data format

`results/<run>/simulation.json` holds `configuration`, `actors`, `edges`, `frames`, `events`, `daily`, `audit`, and `systems`. `frame.actors` uses compact arrays: `[id, patch, alive, health, physiological_need_deficit, conviction, energy_reserve, developed_node_count, safety_need_deficit, belonging_need_deficit, esteem_need_deficit, purpose_need_deficit, fear]`. `frame.patches` stores authoritative stocks, not fabricated coordinates. See `README.md` for command usage.
