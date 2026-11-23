# Founders-CIV WORLD-024 — 100-scenario World Tree Commons integration report

**Status:** reproducible experimental engineering report, not an empirically validated ecology or society.  
**Source:** WORLD-023 integrated living-tree pilot, preserving the original v0.18 `Book` ledger and SOCIAL-021 autonomous 100-Founder scheduler.  
**Run record:** `/results/world024/100_stress/preregistered_plan.json` and `raw_100_runs.jsonl` in the release.

## Why this update exists

The user-defined World Trees are not merely decorative environments: they are ecological resources that Founders can harvest, use for energy and ongoing development, and lose through neglect, overextraction, or environmental shocks. The new loop models one public World Tree surrounded by 100 autonomous Founders (50 starting support pairs), allowing voluntary stewardship and, in a separate condition, additional privately researched trees. **No creation is made invulnerable.** A tree collapsing is a successful stress test when the ledger, identity, causal history, and dependency rules still hold.

## What changed in executable code

1. **Shared tree economy:** tree vegetation -> portable Founder food inventory through a funded material transformation. Food consumption -> detritus and usable Founder energy debited from the tree's finite chemical account. No phantom mass or energy. Harvesting competes with mortal grazers and plant regeneration.
2. **Voluntary cooperative stewardship:** Founders independently observe the world and may join a council depending on ambition, goals, perceived trust and energy. A three-person rotating watch is allowed to maintain either the World Tree or its parent Realm. Maintenance requires sufficiently recent observation and is funded from the acting Founder's energy. It competes with personal activities; duty does not guarantee action.
3. **Alternatives:** owner-only stewardship, faction-restricted cooperation, no-upkeep negative control, and intensive harvesting.
4. **Environmental interventions:** temporary low rainfall, disease risk, doubled-upkeep pressure, and energy drain on active Founders. All energetic costs go through the shared `Book`.
5. **Independent creations:** Founders may initiate up to two additional World Tree projects and separate Species Seeds. The original two-distinct-cycle research requirement, independent peer review, parent Realm requirement and funded planting remain in force.
6. **Long-run learning bug repair:** skill increments are capped to prevent a saturated coordination/practice skill from generating a negative learning increment that aborts late runs. Original `FounderRegistry.learn` still rejects invalid nonpositive progress.
7. **Interactive interface:** `launch_world024.py` and `founder_world_024.html` show council membership, energy contribution, harvested biomass, food energy, tree lifecycle, private creations, and actor-level actions.

## Test design

- **100 controlled scenario executions**: 10 profiles × 10 matched seeds (820–829). The runs use durations `[80,100,120,140,160,180,200,220,260,300]`, shared for every profile at a given seed.
- **17,600 post-bootstrap cycles**; each scenario uses 100 active Founder identities. Reported decision opportunities: **1,790,000** (including 3 setup cycles per scenario).
- The setup executes actual peer-reviewed Realm Island, World Tree and Species Seed blueprints; it nominates seed authors/reviewers for experimental control. Subsequent stewardship, exploration, research, sharing, harvesting, and private tree creation are agent-policy-selected.
- Passing means configured time steps execute and the Book audits balance with the expected persistent actor population, **not** that a tree survives.
- **100/100 scenario executions passed**, zero exceptions. Maximum absolute ledger residual across 100 scenario ends: approximately 4.46e-11 synthetic mass units and 7.96e-7 synthetic energy units.
- Separate automated Python suites passed **85 original/inherited tests + 53 top-level tests**, including 14 WORLD-024 unit/integration checks. Browser JavaScript syntax and live local HTTP scenario-start/state endpoints were also checked.

## Full results by condition

All mean outputs are per run, and every row contains 10 **synthetic** scenarios. Runs have unequal horizons but are matched across conditions.

| Condition | Active shared tree | Mean final mortals | Mean council members | Mean distinct contributors | Mean food mass harvested | Mean tree energy delivered |
|---|---:|---:|---:|---:|---:|---:|
| Shared cooperative stewardship | 10/10 | 20.8 | 55.8 | 39.6 | 19.84 | 4.67 |
| Owner-only stewardship | 0/10 | 0.0 | 0.0 | 0.9 | 7.67 | 2.72 |
| Faction-restricted stewardship | 0/10 | 0.0 | 0.6 | 0.6 | 6.68 | 2.61 |
| No upkeep control | 0/10 | 0.0 | 0.0 | 0.0 | 4.03 | 2.16 |
| Intensive harvesting | 5/10 | 8.6 | 50.9 | 28.0 | 33.40 | 4.34 |
| Extended low precipitation | 9/10 | 11.3 | 56.0 | 39.2 | 19.06 | 4.15 |
| Disease exposure | 10/10 | 21.2 | 56.4 | 38.4 | 19.80 | 4.68 |
| 2.1× maintenance demand | 7/10 | 12.5 | 56.2 | 44.6 | 18.21 | 4.27 |
| Founder energy pressure | 10/10 | 19.6 | 55.9 | 38.2 | 19.57 | 4.46 |
| Independent seed creation allowed | 10/10 | 20.7 | 55.9 | 38.3 | 19.61 | 4.60 |

The unrestricted cooperative condition retained **10/10** shared trees through the assigned 80–300-cycle horizons, with a mean of 55.8 volunteer members and 39.6 distinct energy contributors. Owner-only, faction-restricted and unmaintained controls each ended **0/10** active; their average collapse times were 26.8, 20.9 and 11.0 cycles. The policy itself creates some of this advantage by staffing a redundant watch: this is a test of the modeled mechanism, not independent proof of a universal social law.

Intensive harvesting produced a mean of 33.40 units of harvested food material, versus 19.85 in the cooperative careful-harvest condition; **usable energy delivered was actually lower** (4.34 versus 4.67). Five of the extractive trees collapsed. This could reflect a mixture of harvest intensity, regeneration limits, reduced chemical stocks and Founders devoting attention to collecting instead of repairing. The current ablations do not separate those pathways.

Extended low rainfall left 9/10 trees active but lowered mean surviving mortals to 11.3, from 20.8 in the normal collective condition. The disease intervention left 10/10 trees active and had a small average effect, indicating that its current mortality pressure may be too mild or poorly calibrated. High upkeep left 7/10 trees active. Founder energy drain left 10/10 active in this sweep.

Private creation produced **two extra World Tree constructs per run (20 in total)**, but **zero were active at their run's end**. Across these experiments, 11 of the private-tree projects also received their own Species Seeds. Seed design and planting pathways work, but private stewardship, maintenance agreements and creation succession are deficient.

## Fixed-seed 500-cycle follow-up (5 additional runs, not counted above)

All runs used seed 829 to examine late failure after the initial 300-cycle study.

| Policy | Shared-tree status at cycle 500 | Living mortals | Shared-tree collapse cycle | Parent Realm collapse cycle |
|---|---|---:|---:|---:|
| Shared cooperative stewardship | archived | 0 | 440 | 451 |
| Owner-only stewardship | archived | 0 | 21 | 21 |
| Intensive harvesting | active | 16 | — | — |
| Independent seed creation allowed | active | 20 | — | — |
| 2.1× maintenance demand | active | 17 | — | — |

**Critical exception:** the cooperative tree that survived to 300 cycles eventually collapsed at cycle **440**, and its parent Realm collapsed at **451**. Thus cooperation **does not make trees immortal**. The intensive-harvest tree happened to survive to cycle 500 with 16 residents, while the private-option common tree survived with 20; those paths are not proof that extraction or privatization is inherently beneficial. All five runs passed accounting checks.

## Interpretation and design implications

- **Ecology and social structure are causally coupled in the *programmed* model**: decision opportunities, trust-gated membership, observation, funded repair, collection and world biomass are connected through event and resource accounts. However, the social utility rules are hand-designed and require testing against simpler alternatives and empirical constraints.
- **World Trees can now yield food and energy**, creating competition between Founder consumption, ecological inhabitants and preservation. This is a first economic feedback loop, not a complete production system.
- **Institutions outlive individual intentions only if their stewardship obligations are modeled.** Private World Trees demonstrate a creation/maintenance mismatch. Adding explicit funded budgets, rotating watch contracts, backup stewards and belief-based early-warning systems is the logical next step.
- **Failure is not a programming defect by itself**. The 500-cycle cooperative loss is an important output; errors and malformed ledger transfers are programming defects, and none remained in the completed 100-run study.

## Scientific and engineering limitations

1. **Synthetic environmental rates:** the ecology tracks one grazer type and bulk resources across four graph habitats. The model is not fitted to observed ecosystems. Snow, disease, dry season and crop failure magnitudes are simulation assumptions.
2. **A real food-energy accounting gap remains:** consumption currently draws chemical energy from the *live tree* rather than from a portable, energy-tagged food resource established during harvest. Food can be stranded after a world collapses; future code must move embodied energy together with food and release it at consumption.
3. **Construction material gap:** World Seed construction still draws mass from Solara's source accounts. The tree can supply some energy used by Founders, but it cannot yet supply a provenance-tagged export of timber, minerals or soil directly into new creations.
4. **Weak economic incentives:** the House and river have substantial alternative energy supplies; tree-produced energy is relatively small. More realistic valuation, resource scarcity and Founder demand must be introduced before testing theories of tree-driven civilization growth.
5. **No complete institutions:** a deterministic three-person rotating watch is an experimental coordination policy. Actual elections, contracts, assignment failures, liability, taxation, and generational continuity are absent. The number of volunteers is partly determined by handcrafted goal and trust thresholds.
6. **Limited inference:** only 10 paired seeds per condition; duration is tied to seed index, so variation in seed and horizon cannot be separated statistically. Results are internal model behaviors, **not scientific confirmation about consciousness, human societies, or actual ecosystem survival rates**.
7. **Unresolved integration details:** private trees with mortal populations lack autonomous ecology-management institutions, and knowledge/trust/memory are not yet fully integrated with calibrated forgetting and prerequisites.

## Prioritized WORLD-025 work

1. Implement **persistent steward contracts** with voluntary acceptance, payment/energy budget, recorded promises, missed duties, backup stewards, institutional audits, and no guaranteed rescue.
2. Add portable **food embodied-energy accounts** and `tree -> Founder -> creation` provenance, including harvestable building material and optional communal storage.
3. Make maintenance decisions sensitive to multi-source observational evidence, learned technical competence and institutional decision latency; keep misleading information and contested authority possible.
4. Rework private trees so their owners can recruit staff, form coalitions, insure maintenance, or deliberately abandon them; study whether public and private trees can both persist.
5. Expand ecology beyond one grazer species to plant succession, decomposers, pollinators, predators, parasitism and variable habitat area, then measure carrying capacity and resilience across longer 500–2,000-step sweeps.
6. Add targeted ablations separating biomass overharvest from time/attention competition, and calibrate knowledge/trust and ecology with outside observations when available.

## Reproduction

```bash
cd Founders_CIV_v020_Soul_Ecology_Pilot
python -m unittest discover -s tests -q
python -m unittest discover -s . -p 'test*.py' -q
python run_world024_stress.py --seed 829 --cycles 300 --profile commons --history --out results/sample.json
python run_world024_batch.py --out results/world024/100_stress --workers 4
python run_world024_long.py
python launch_world024.py --seed 820 --port 8766
```

Running `run_world024_batch.py` reruns the 100-scenario plan; on a multicore system it may be computationally substantial. The provided CSV, JSONL and scenario manifest are results of the completed run.
