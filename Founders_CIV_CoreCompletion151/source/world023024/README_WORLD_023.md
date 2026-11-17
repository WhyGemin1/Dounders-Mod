# Founders-CIV WORLD-023 — First Living World Tree

**Status:** executable experimental vertical slice, not a full society or validated biological ecosystem.
**Source:** extends WORLD-022, SOCIAL-021, and the v0.18 physical `Book` with the WORLD-023 design specification.

## Run the interactive Sea

On Windows, extract the release ZIP, enter `Founders_CIV_v020_Soul_Ecology_Pilot`, and double-click `START_FOUNDER_WORLD.bat`. On Linux/macOS, run `python launch_founder_world.py --seed 400 --port 8765`; visit http://127.0.0.1:8765/.

In the interface click **Start reviewed living world** to reset to a reproducible pilot scenario. The launcher *actually executes* the three seed workflows: a Realm Island blueprint, a World Tree blueprint, and a Species Seed blueprint each receive research on two distinct simulation cycles, review by another colocated Founder, and funded planting. Initial creation is a **scripted test setup**, not emergent autonomy. Subsequent Founder observation, research and stewardship actions are selected by the autonomous agent policy.

Alternatively, use the right-side workshop to create these three blueprints manually. A World Tree remains an unpopulated (germinating) environment until a validated Species Seed is planted within it.

## Run reproducible tests

```sh
python -m unittest discover -s tests -q
python -m unittest discover -s . -p 'test*.py' -q
python run_world_tree_pilot.py --seed 400 --days 200 --out results/world023/my_200cycle_run.json
```

The inherited tests and new tests are separate discovery sets. The pilot script reports synthetic World Tree births, deaths, active Founder observations/research, stewardship, and ledger residuals.

## Implemented in WORLD-023

- `founders_civ/experimental/world_trees.py`: per-tree runtime, four habitat graphs, live individual resident identities, climate/rainfall and sunlight flow, plant growth, decomposition, consumption, reproductive birth, mortality, local migration, collapse and remnant material routing.
- `founders_civ/experimental/world_integration.py`: compile living runtime only from a *planted, reviewed* World Tree Seed; introduce organisms only after separately validated and planted Species Seed; tick world interiors in the original physical ecology → new World Tree → social Founders → construct upkeep pipeline.
- Founder autonomy: creator observes from House/riverbank, researches recent observations and funds creations according to an estimated remaining reserve, rather than omniscient account access. Social founder attention competes with other goals.
- RSW-K: observed world dynamics produce an actor-specific knowledge encounter; exposure changes cognitive records without granting instant mastery.
- `founder_world.html` and `launch_founder_world.py`: actual localhost-backed habitat inspector, population and biomass history, living resident summaries, World Tree observation and research controls and starter world scenario.

## Major limitations

- One starter herbivore type; one approved Species Seed per World Tree in the pilot. No separately modeled predator, pollinator, parasite or decomposer agents. Decomposition is a material-flow process.
- Resources are conserved synthetic bulk matter and energy, not realistic stoichiometric chemistry. Plant growth receives **funded House sunlight**; water redistribution is bookkeeping, not full evaporation/condensation thermodynamics.
- A World Tree's initial material comes from existing Solara patch accounts; a dedicated Sea/Wellspring matter-conversion policy remains unresolved in canon.
- Reef/island geography, seasons and food webs are simplified; present mortality/fertility coefficients have not been empirically calibrated.
- Stewardship is initially owner-based. There are no shared maintenance contracts, supply routes, local mortal institutions, or interworld travel by mortals.
- The House already runs the legacy Solara/Vespara ecology; World Tree interiors are new modules and do not inherit its entire population/animal ecology.
- Pilot `bootstrap()` is a reproducible **scenario creator**, not a claim that independent Founders discovered all three blueprints unaided. After planting, autonomous Founder decisions govern their subsequent observations and maintenance.
- 100+ cycles surviving in some simulations does not establish stability in all seeds, ecological realism, or consciousness.

## Current experiment evidence

Four 120-cycle trial seeds 400–403: three active worlds with living residents at the end, one collapsed from unfunded upkeep. A 200-cycle seed-400 trial remained active with descendants. See `results/world023/` and `docs/WORLD_023_IMPLEMENTATION_AND_TESTS.md`.

The raw project contains historical documentation and prototype tests. A module existing in the ZIP does **not** mean it is wired into the main decision policy; WORLD-023 integration explicitly covers only the mechanisms described above.
