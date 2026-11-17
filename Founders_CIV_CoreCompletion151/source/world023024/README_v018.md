# Founders-CIV v0.18 — Canon & Observatory

A **local, offline Python simulation and interactive 2D observatory** for the Founders-CIV fictional universe and its RSW/CIV-OS research model. The core is the tested v0.17 first integration, organized and instrumented for inspection. **v0.18 is an observability and canon consolidation release, not a claim that all proposed subsystems are finished.**

## Getting started on Windows

1. Download and extract `Founders_CIV_v018_Canon_Observatory.zip` completely. Do **not** run from inside the ZIP preview.
2. Double-click **`START_DASHBOARD.bat`**. A Command Prompt window runs the local server; the dashboard opens in your browser at `http://127.0.0.1:8765`.
3. Press **Play** to watch the included seeded 30-day sample. Adjust the day slider, choose a world, and click animals, creations or habitat patches to inspect information.
4. Set a seed, choose a duration and toggle **S / F / B / I**; click **Run New Simulation**. The new run is computed on your PC. It does **not** send simulation data to any external server.
5. Open **Canon register** to see each rule's implementation status and its supporting code path. Open **Test & methodology** for research boundaries.
6. Close the `Founders-CIV Server` Command Prompt to stop the local service.

If `py` isn't recognized, open Command Prompt in the extracted folder and run `python launch.py` (or `python3 launch.py` on macOS/Linux). Then manually open `http://127.0.0.1:8765`. Python 3.10+ is recommended; no third-party packages are needed to run.

**If the window says “Only one usage of each socket address”**, an old copy of the server is still running. Close the old Command Prompt or run `python launch.py --port 8770` and open `http://127.0.0.1:8770`.

## Dashboard features

- **2D animated world panel:** Solara and Vespara, each with forest, grassland, wetland and ridge habitats, living actor dots colored by species, moving sunlight motif, and vegetation-based habitat shading.
- **Time travel:** play/pause, adjust playback speed, scrub to any simulated day, advance/rewind one day.
- **Actor inspector:** see species, age-independent health, reserve energy, need deficits, fear/conviction, goals, skills, developed Nodes, remembered claims and directed social relationships.
- **Habitat inspector:** see the actual simulated plant, soil, water, detritus and carcass material accounts for the selected patch.
- **Trend graphs:** see herbivores by world, plant stocks by world, House energy, institution count and elementary Soul Network Node count.
- **Event stream:** inspect selected significant actor actions with search and filters for ecology, decisions, social learning and institutions.
- **Institutions:** inspect real member counts, pooled resource stocks, norms, monitoring events and revisions.
- **Canon register:** browse **25** canonical systems with exact operational/partial/specified labels.
- **Export:** download the active simulation's JSON for further investigation. Each run is also saved in `results/<job-id>/` as JSON and CSV.

**Spatial honesty:** the engine tracks actors' **habitat patches**, not continuous x/y positions. Within-patch dot positions and gentle motion in the animation are **diagrammatic**. Do not interpret them as collision, exact tracking or pathfinding data.

## Command-line operation

Open Command Prompt or Terminal in the extracted folder.

```powershell
py -m unittest discover -s tests -v
py run_simulation.py --days 30 --seed 42 --arm 1111 --output results/my_trial
py run_simulation.py --days 120 --seed 1729 --arm 1010 --output results/second_trial
```

On Unix/macOS use `python` instead of `py`. `run_simulation.py` accepts **1 to 720 days**, while the interactive dashboard limits runs to **180 days** to avoid unbounded browser exports. The four binary factor digits are **Social relationships / Fear Logic / Collective belief / Institutional feedback**, in that order. `1111` enables all; `0000` disables all four interventions (the shared physiology/physics remains on).

**Important:** the registered **16 configurations × 30 seeds × 720 days** study remains **unexecuted**. The CLI can run the configured days, but it is not a validated batch manager, and the existing ecology cannot yet establish long-term generational stability.

## Directory guide

```text
Founders_CIV_v018_Canon_Observatory/
├── START_DASHBOARD.bat                 # Windows double-click launcher
├── RUN_TESTS.bat                       # Windows test launcher
├── launch.py                           # Dashboard entry point
├── run_simulation.py                   # CLI entry point
├── Founders_CIV_v018_Canonical_Systems.docx
├── README.md
├── founders_civ/
│   ├── canon.py                        # 25-rule machine-readable register
│   ├── core/
│   │   ├── engine.py                   # v0.17 integrated world/actor core
│   │   └── ledger.py                   # funded atomic mass/energy transfers
│   ├── observatory.py                  # read-only snapshots and event exports
│   ├── runner.py                       # CLI runner, JSON/CSV writeout
│   └── server.py                       # local HTTP dashboard server
├── web/
│   ├── index.html, styles.css, app.js  # dashboard and 2D animation
│   └── sample_run.json                 # bundled 30-day seeded data
├── docs/
│   ├── CANONICAL_SIMULATION_SPEC.md    # full markdown version of DOCX
│   ├── SYSTEM_TRACEABILITY.csv         # status and code audit
│   ├── RESEARCH_AND_TEST_PROTOCOL.md
│   ├── RELEASE_NOTES.md
│   ├── V016_INTEGRATION_BLUEPRINT.md
│   └── OBSERVATORY_PREVIEW.png         # optional preview image
├── archive/                             # prior research engines, not live
├── tests/                               # ledger, engine, system, UI contract tests
└── results/sample/                      # full reproducible sample run
```

## Canon versus implementation

The authoritative specification is the Word file / `docs/CANONICAL_SIMULATION_SPEC.md`, with detailed coverage in `founders_civ/canon.py`. At release time **4 of 25** systems are classified operational, **17 partial**, and **4 specified-only**. This is a transparent accounting of the current model, not a grading of how important each rule is.

Examples of **not yet operational**: all 100 autonomous Founders, checkpoint rollback and resurrection, every Spirit role, biological reproduction and genetic inheritance, element-level chemistry, full time dilation, dimensions and realms, advanced Soul Network Kingdoms/Nations/Realms, independent constitutional government, and genuine engine-coordinate 2D pathfinding.

## No extra installation required

The application uses Python's standard library plus ordinary browser Canvas and JavaScript. No hosted AI API, internet connection, npm installation, JavaScript framework or game engine is needed to inspect and run the bundled simulation. `python-docx` is required only if you want to **regenerate the Word specification** with `python tools/build_canon_doc.py`; the finished Word document is already included.

## Validation and known limitations

Tests check double-entry material/energy conservation, tolls only on registered transformations, rollback on failed transfers, same-seed reproducibility, source-tagged learning with separate practice, materialized institutions and snapshot schemas. The 30-day sample is a synthetic test scenario, not scientific evidence that real religions, ecologies or societies work a certain way. Energy is measured in **experimental energy units**, material in **abstract mass units**, time in synthetic daily steps. Conservation does **not** imply realistic chemistry or ecological sustainability.

UI outputs include **selected significant events** rather than every low-level movement and physical ledger entry. This keeps the dashboard usable on ordinary PCs; deeper transaction-level history would require expanding the persistence layer.
