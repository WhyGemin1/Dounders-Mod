# WORLD-024 — World Tree Commons, Stewardship, and Resource Economy

Experimental extension of the WORLD-023 living tree vertical slice. All Founder decisions remain on a single 100-actor SOCIAL-021 scheduler. Physical changes and energy budgets use the original v0.18 `Book`, not a parallel material model. This is **not** an empirically calibrated ecological or psychological model.

## What's new

- **Tree economics:** Founders at the House or river gateway can observe the shared tree, harvest a measured fraction of plant mass into their portable food stock, and subsequently consume it. Harvest is a funded state change; consumption converts food into detritus and transfers *existing* local chemical energy to the Founder. Conservation is audited after every simulation tick. Tree harvests compete with mortal grazers and plant regeneration.
- **Voluntary stewardship:** Founders may observe the shared tree, choose to join a stewardship watch according to their goals, ambition, perceived trust and energy, and choose to maintain the tree or its parent realm during rotating duty. They use previously observed maintenance reserves and decay forecasts; access to the actual ledger is restricted to physical resolution and observation.
- **Governance alternatives:** `collective`, `owner`, `fragmented`, and `none`. Collapses are allowed and retained in the results; no survival bonuses are conferred by governance labels.
- **Private-tree option:** Founders may autonomously propose up to two additional World Tree blueprints and later Species Seed blueprints, still subject to research on separate cycles, independent peer review, physical funding, and a valid parent Realm Island. These compete for attention and Solara/House resources. The common World Tree remains the focal world in all treatments.
- **Exogenous conditions:** transient rainfall reduction, disease risk, higher construct upkeep, and Founder energy drain are explicit experimental interventions, not changes to the world's original blueprint and not free-energy creation.
- **Learning saturation repair:** social-agent practice and coordination no longer attempt negative skill increments after skills approach 1.0; the core registry still rejects invalid progress.

## Run the experiment

From the project folder:

```bash
python -m unittest discover -s tests -q
python -m unittest discover -s . -p 'test*.py' -q
python run_world024_stress.py --seed 820 --cycles 120 --profile commons --history --out results/example.json
python run_world024_batch.py --out results/world024/100_stress --workers 4
```

The batch preregisters 10 governance/environment conditions × 10 matched seeds (820–829), for exactly **100 independent scenarios**. Cycle durations per seed are `[80,100,120,140,160,180,200,220,260,300]`; all profiles use the same duration for a given seed. Counts are simulation cycles after a three-seed research-and-planting bootstrap. Each active run has 100 Founders and starts with one common Realm Island, one World Tree, and one separately approved mortal Species Seed. Private trees, if created, require their own subsequent seed workflow.

Success means the run completed with exactly 100 Founder identities and a balanced physical ledger. A world that collapses **still counts as a valid stress run** if the model records and accounts for the collapse without violating invariants.

## Interpreting the data

- `100_stress_results.csv`: one row per run, with survival/archival state, birth/death, harvest, participation, blueprint activity, and energy-accounting metrics.
- `100_stress_summary.json`: aggregated condition-level results.
- `raw_100_runs.jsonl`: complete results, including selected 300-cycle trajectories and diagnostic decisions.
- `preregistered_plan.json`: seeds, durations, and scenario definitions.
- `run_world024_stress.py`: reproducible individual-run driver.
- `test_world024.py`: targeted invariants and regression tests.

## Known limitations

The tree provides **food biomass** and **usable local chemical energy**, but there is no complete export chain for ore, lumber, or soil into the construction supply system. Seed construction remains funded by the original Solara substrate and House reserve. The environment currently contains one grazer type and four graph habitats, not a detailed food web. All coefficients and humanlike decision rules are synthetic. The House/river remain alternative energy sources, potentially diminishing the economic incentive to maintain a tree. Council duties are a deterministic rotation among volunteers, not an elected institution with contracts, liability, or budgets. Private creations are possible, but the present scenario caps total independent trees for bounded workload. More extensive spatial, network, learning, and institutions realism remains planned.

## Interactive World Tree Commons

Use `START_WORLD_024.bat` on Windows or run `python launch_world024.py --seed 820 --port 8766`, then open `http://127.0.0.1:8766`.

Choose your social policy, harvest intensity and whether independent World Seeds are permitted, then select **Start reviewed World Tree commons**. That initializes one independently researched, reviewed and physically funded Realm, World Tree and Species Seed (the controlled research bootstrap). Afterwards, 100 Founders choose their own actions. The interface reports council size, material harvest, consumed energy, shared tree population and all private creations. Selected Founders can observe, volunteer, harvest, eat and use the existing workshop for their own seeds. Each UI action resolves through the same Python ledger and world scheduler.

## Specific remaining economic gap

In this version the energy for eating is drawn from the World Tree's *live chemical reservoir at consumption time*, rather than being packaged into a portable food-energy account at harvest. Therefore stored food is not yet a physically complete carryable calorie store, and a tree's collapse can strand previously harvested food. A future version should bind chemical energy to food items at harvest and then transfer that *stored food energy* to a consuming Founder, independent of the tree remaining alive. Tree-origin mineral and timber resources also need explicit harvesting, ownership and construction-input provenance. Do not extrapolate quantitative welfare or energy economics from these experimental coefficients.

On Windows, use `RUN_WORLD_024_TESTS.bat` for the two automated suites. Use `python run_world024_batch.py --workers 4` only when you want to repeat the computationally substantial full 100-run experiment.
