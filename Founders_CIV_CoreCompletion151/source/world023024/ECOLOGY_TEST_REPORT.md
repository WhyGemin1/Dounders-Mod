# Founders-CIV — v0.20 Soul Network Ecology: Executed A/B Tests

**Date:** 2026-11-06  
**Status:** tested experimental patch; no claimed proof of ecological sustainability.

## The question

Can carefully selected Soul Network learning rules improve individual animals' behavior under environmental changes **without changing their inherited biological traits, artificial population caps, conservation ledger, or canonical Soul hierarchy**?

## Study implementation

The experiment imports the original v0.20 `Population`, `Book` and `SoulNetwork` modules. We left their metabolic costs, birth/death mechanics, state-transition tolls, aging and mutation code unchanged. We introduced an independent **seasonal hazard fixture** because both existing v0.20 patches otherwise offer nearly identical survival conditions; the fixture is held identical across cognitive arms. Each iteration is a demographic generation-like step, **not a measured day**.

Forty matched seeds (200–239) per condition, 12 steps, 30 initial grazers, two patches, alternating season every six steps, and invented patch-specific hazard probabilities of 0.17 exposed versus 0.018 sheltered. All arms get the same initial two experienced route teachers. Each real migration uses `Population.migrate` and consumes existing energy in the authoritative ledger. Cognition changes **decisions**, not reproduction rates or physical resources.

## Results: seasonal hazard comparison

| Outcome, mean across 40 seeds | Baseline | Episodic | Social learning | Full selective patch |
|---|---:|---:|---:|---:|
| Final survivors | 6.100 | 6.075 | 6.125 | **7.725** |
| Births | 29.975 | 30.550 | 31.275 | 33.725 |
| Habitat event deaths | 27.750 | 27.875 | 27.575 | 26.675 |
| Unsafe habitat exposures | 139.200 | 134.850 | 129.625 | **124.675** |
| Explicit action-driven migrations | 0 | 4.050 | 8.825 | **15.400** |
| Traced route-learning practices | 0 | 4.050 | 8.825 | **15.400** |
| Animals with trained route flag at end | 2.825 | 1.600 | 2.375 | 4.225 |
| Remaining food mass | 427.737 | 426.584 | 425.001 | 421.047 |

The **full treatment** averaged **+1.625 survivors** per seeded simulation versus baseline, or +26.6% relative to the baseline's small surviving population. The 95% *paired nonparametric bootstrap* interval for that mean difference was approximately **+0.575 to +2.650** animals. The difference was positive for 25 seeds, negative for 9, and tied for 6. Unsafe habitat exposure was **14.525 lower** on average; paired bootstrap interval approximately **−20.750 to −8.425** exposures.

Importantly, the episodic and social treatments without the complete fear-guided decision policy did **not** show a clear survival benefit. This implies that stored information matters only insofar as the actor can use it to select effective behavior. The full treatment also increased births, so the +1.625 survivors should **not** be attributed solely to directly avoided hazard deaths.

### What the paired interval means

The intervals describe variation across **these synthetic, matched-seed scenarios and fixed model parameters**. They are not confidence bounds on any real species, nor a general statistical guarantee. The optional threat fixture and its numeric rates have not been empirically calibrated. This is a *proof-of-mechanism* result; it is not evidence that this precise Soul architecture is optimal.

## No-hazard negative control

Forty matched seeds per arm, same world and actors, with the artificial habitat hazard disabled. **All four arms had an identical mean of 21.775 animals after 12 steps, identical births, and no Soul-directed migrations.** That supports the claim that knowledge by itself did not directly grant biological advantage or energy.

## Long-run demographic stress

Thirty matched seeds per arm, 30 steps. **Every arm went extinct.** Average remaining food was still ~419–427 abstract material units. Thus v0.20's age-dependent mortality and insufficient demographic replacement remain the primary barrier to persistent ecology. The current model turns each step into a whole unit of biological aging; all animals die after age 9, so this fixture is **not** a realistic 30-day animal-survival model.

## Memory-decay sensitivity check

Forty matched seeds, full-treatment arm, 12 steps. We varied retrieval decay, keeping all other conditions unchanged.

| Memory decay | Final surviving animals | Unsafe habitat exposures | Migrations |
|---|---:|---:|---:|
| 0.02 | 7.725 | 123.150 | 15.575 |
| 0.13 | 7.725 | 124.675 | 15.400 |
| 0.40 | 8.050 | 125.900 | 14.675 |

The short-run survival ranking was not especially sensitive to this particular range, although route retrieval and movement changed. A longer viable ecology and varied-quality information would be needed to calibrate memory decay meaningfully.

## Integrity results

- **15/15** targeted and original continuity tests passed in the extracted pilot harness, including knowledge/procedure separation, forgetting without deletion, source confidence revision, newborn noninheritance, reproduction, deterministic execution, no-hazard null test, and ledger conservation.
- Maximum observed absolute material imbalance: < 8×10⁻¹² abstract mass units.
- Maximum observed absolute energy imbalance: < 2.4×10⁻¹⁰ synthetic energy units.
- All observed migrations use the unchanged v0.20 energy-transfer action. No cognitive event creates resources.
- No Soul State was granted automatically through a lesson or one migration experience.

## Critical implementation checks

During development I caught a **world-knowledge leak** where the decision code temporarily selected the objectively safe patch rather than using local perception. I removed it **before finalizing the numbers reported above**, replacing it with selection of a merely adjacent patch and local noisy hazard sensing. That error is now explicitly documented so future testing does not recreate it. World state and actor belief must remain separate.

## Interpretation and deployment

**Supported:** Source-tagged experience, context-sensitive retrieval, real practice and fear-sensitive action selection can interact with the existing v0.20 ecology and produce a measurable short-term response under a constructed seasonal hazard without breaking conservation.

**Not supported:** The Soul extension alone makes ecology stable; memory-only or social-learning-only is sufficient; animal reproduction and survival are scientifically calibrated; Souls develop advanced States/Kingdoms/Nations automatically; this proves a scientific claim about real animals.

**Next test:** Repair the demographic timeline and implement seasonally renewable producer stocks, then run 5–20 simulated years with repeated ecological cycles and ≥3 patches; rerun the same learning ablations and estimate whether cultural routes alter population persistence, not merely 12-step survival.
