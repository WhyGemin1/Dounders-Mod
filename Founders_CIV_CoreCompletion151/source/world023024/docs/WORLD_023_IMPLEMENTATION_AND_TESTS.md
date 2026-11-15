# WORLD-023A/B — Living World Tree implementation and experimental validation

**Release status:** experimental integrated vertical slice, not baseline promotion. 7 November 2026 project iteration.

## Objective and source alignment

The WORLD-023 specification calls for one real World Tree, four habitats, funded matter/energy, an enduring mortal population and autonomous Founder observation, research and maintenance. This implementation reuses the existing WORLD-022 seed lifecycle and the SOCIAL-021 agent scheduler with the original `Book`. It **does not** replace the v0.18 conservation engine.

## Architecture and changed files

| File | Change |
|---|---|
| `founders_civ/experimental/world_trees.py` | New `WorldTree`, `WorldTreeRegistry`, `TreeResident`, habitat graph, four biome accounts, mass/energy flows, aging, births/deaths, collapse archives, observation and study |
| `founders_civ/experimental/world_integration.py` | World Seed compile hook, Species Seed admission hook, shared tick integration, actor-relative reserve forecasts, competing autonomous stewardship/observation/research proposals, tree state in API |
| `launch_founder_world.py` | Manual world observe/study API; safe reset through reviewed-seed starter scenario |
| `founder_world.html` | Living biome inspector, population and biomass series, individual living-resident list, and Founder controls |
| `run_world_tree_pilot.py` | Reproducible scenario with physically funded, peer-reviewed Realm, Tree, and Species seed setup; no scripted maintenance after setup |
| `test_world_tree_023.py` | 15 regression/integration tests (new module) |

### Physical boundaries

Each World Tree uses four connected habitats, `forest`, `grassland`, `wetland`, `ridge`, represented by stable resource prefixes (`soil`, `plant`, `detritus`, `water`, `chem`, `sun`). Approved planting transfers material from existing `Solara` accounts and energy from approved donor accounts through `Book.move`; organisms are built from planted biomass through `Book.transform`, paying the canonical provisional toll. No post-freeze stock is incremented outside `Book`.

Every world tick: charge sunlight *from House energy*, relocate water into/from a shared atmospheric account, decompose detritus into soil, generate plant biomass using soil and funded sunlight, let individual herbivores select between local feeding and permitted migration, resolve metabolism, possible births and deaths, and then publish a world summary with transaction-range IDs. The world runs even when its creator is absent, unless upkeep failure causes collapse.

The original `Book` models abstract material and synthetic energy, not water thermodynamics or biochemical element conservation. In this prototype water's atmosphere account denotes transport, not a modeled phase transition. All rates are illustrative and open to sensitivity tests.

### Seed prerequisites

1. A Realm Island requires independently reviewed research and funded planting in the Sea.
2. A World Tree Seed requires a stable parent Realm, distinct-cycle research, independent review, and material/energy funding. This creates four *unpopulated* habitats.
3. A separate Species Seed requires the planted World Tree as parent and the same validation pipeline. It transforms existing plant material and energy into initial mortal inhabitants.
4. Any tree or species planted without these prerequisites is rejected. All failures must leave the resource ledger unmodified where preflight can detect them.

### Actor epistemics and autonomy

Founder perception is restricted to observation points (House or riverbank). Observations are recorded in the individual Founder's memory and in the RSW-K knowledge module, as *exposure* rather than perfect understanding. Research requires a recent observation and funds its time/energy expense. Stewards estimate future reserve from their last known creation budget and predictable upkeep; they do not read the true reserve to choose whether to intervene. Maintenance competes with other suggested actions and can be skipped or fail.

The scenario bootstrap nominates authors and independent reviewers explicitly. These three opening creations are an **experimental setup**; only ongoing observation, research, population dynamics and maintenance are tested as independent agent/world behavior.

### Tests actually executed

- Original `tests/` discovery: **85/85** passing.
- Top-level test discovery, including 15 WORLD-023-specific tests: **39/39** passing.
- JavaScript syntax: Node `--check` on the inline browser script passed.
- HTTP smoke: GET `/` and `/api/state`; POST `/api/action` with `starter_world` and `step` both succeeded. State returned one living World Tree with four habitat records and 16 starter individuals.
- Determinism: matched-seed replay matches world snapshots and ledger transaction counts in the new tests.
- Negative control: removing autonomous upkeep collapses the parent Realm and its dependent Tree; residents die, physical resources are moved to traceable remnant accounts, and conservation still audits.

### 120-cycle reproducible trials (post-bootstrap)

| Seed | Realm | Tree | Population | Births | Deaths | Observations | Tree studies | World-specific maintenance actions |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 400 | stable | stable | 11 | 25 | 30 | 9 | 14 | 10 |
| 401 | stable | stable | 16 | 25 | 25 | 10 | 13 | 9 |
| 402 | stable | stable | 14 | 28 | 30 | 14 | 15 | 10 |
| 403 | stable | **collapsed** | 0 | 15 | 31 | 1 | 2 | 2 |

Seed 403's World Tree was archived at global tick 45 because its construction reserve and upkeep were insufficient. Habitat matter moved to audited remnant accounts; founder failure has consequences. These synthetic trials are too few to estimate a true survival probability.

### 200-cycle pilot

Seed 400: Realm stable, Tree stable, 29 living individuals, 52 births and 39 deaths, resident generations 0–6 represented in history, 15 autonomous observations, 19 World Tree research actions, and 16 World Tree maintenance events. Maximum absolute ledger residuals approximately 3.0×10^-11 mass units and 5.6×10^-7 energy units. A population surviving 200 steps is evidence of functionality in this scenario, not a guarantee of an ecological equilibrium.

## Discovered weaknesses / not yet solved

1. Single-owner responsibility is brittle. The failed seed demonstrates the need for negotiated maintenance, backup stewards, institutions and promises; a low-attention Founder may abandon a world accidentally.
2. Life-course and carrying-capacity rates are synthetic and have not been fitted to biological observations. Long-run extinction remains possible.
3. The current tree's ecology has one mortal grazer type and non-agent decomposition; missing predator, scavenger, pollinator and parasite niches limit ecosystem dynamics.
4. The habitat graph has four discrete biomes with no true area, altitude, or continuous distance; no mortal may enter House or switch worlds.
5. External information, memory decay and partial understanding are only partially integrated through existing RSW-K encounters; calibration remains an open project.
6. World Trees currently draw initial physical substrate from Solara rather than a dedicated Sea matter boundary; precise energy-to-matter creation remains unspecified.
7. Cross-registry transactions are preflighted, but not yet a fully atomic distributed rollback across Book, blueprint registry, construct registry and world populations.
8. No complete cultural, institutional, humanlike or conscious agents exist inside new worlds.

## Honest release interpretation

This is the **first executable autonomous-ecology integration**, not a full evolutionary civilization simulator. Canonical world ontology and seed prerequisites are separate from tunable synthetic coefficients and from scientifically validated human behavior. The MASTER baseline remains the audited physical engine until wider factorial tests, atomicity, and ecological robustness improve.
