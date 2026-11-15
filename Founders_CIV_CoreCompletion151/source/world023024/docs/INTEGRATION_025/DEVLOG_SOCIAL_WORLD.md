# Founders-CIV | Social & World Systems Development Log

**Edition:** INTEGRATION-025 documentation and compatibility handoff  
**Chronology covered:** CORE-018 through WORLD-024 and the present optional SDK  
**Date of compilation:** 7 November 2026  
**Evidence policy:** "Canon" is an accepted fictional rule; "implemented" is a code pathway; "tested" is a documented/reproducible software check; "validated" does **not** mean empirically representative of humans or ecosystems.

## Executive synthesis

The Founders-CIV project evolved from a physical/ecological core into an experimental system in which 100 individual Founders make social decisions, research and review creation Seeds, plant Realm Islands and World Trees, and interact with a four-habitat environment. The latest WORLD-024 branch couples voluntary stewardship and food/energy harvesting to the canonical resource ledger. Cooperation improves persistence in programmed scenarios, but World Trees can collapse, private creations often lack lasting maintenance, and synthetic parameters remain uncalibrated. The INTEGRATION-025 deliverable adds **optional, versioned scenario-and-extension compatibility** while leaving the underlying physical engine unchanged.

## Canonical design contributions from project discussions and notes

1. **Individuality and relationships.** Exactly 100 Founders; 50 reciprocal close partnerships; eight squads of twelve with four officers. Every Founder has an identity and can acquire skills outside its title or starting specialty. Historical roster, powers and officers are a separate lore layer; provisional F001–F100 numerical assignments must not silently overwrite the original names and hierarchy.
2. **Six-component relational software.** Actions, Capabilities, Memory, Thoughts/Ideas, Attitudes and Goals jointly produce identity in context; knowledge and trust are interacting mechanisms rather than new primary components. Simulation actors have fallible memories and information access.
3. **The House and Sea.** The House, energy river, waterfall, Fields, Ridge, and Sea geography provide the initial spatial framework. The map is schematic until actual navigation and collision are implemented.
4. **Creation through seeds.** Realm Islands, World Trees, Species Sprouts, Underworld Flowers and Dimensions begin with a blueprint describing their operating rules. Research, independent peer review and funded planting precede existence; creation is not a free action.
5. **World Trees are productive ecologies, not immortal decorations.** They sustain mortal life, food and energy; Founders can cultivate, harvest, care for, neglect, compete over or lose them. A real world must age, reproduce, decompose and die under funded physics. Independent private creation is permitted but carries upkeep cost.
6. **Checkpoint continuity.** When a Founder dies, its saved internal development is restored. External archives, others' memories and physical world histories do not rewind.
7. **Research integrity.** Keep fictional canon, test coefficients, implementation coverage and external scientific evidence separate. Physical conservation does not by itself guarantee ecological viability.

## Development record

### CORE-018 — Canonical physical and observability baseline (5 Nov 2026)

- **Original implementation:** `founders_civ/core/ledger.py` holds authoritative material and energy accounts; `core/engine.py` owns the ecological world, actors and physical events; `observatory.py` offers read-only day snapshots. The House and Wellspring fund energy; material transformations pay an explicit toll rather than spontaneously producing mass.
- **Test record:** release `docs/VALIDATION_REPORT.md` records 46/46 tests, 30- and 120-day samples, conservation checks and a local browser dashboard. The long-running master 100-Founder creation economy was not yet operational.
- **Constraint introduced:** later branches must reuse the same `Book`, never construct parallel uncoupled resource economies; UI coordinates cannot be presented as physical geometry.

### KTC-019 and CONT-020 — Knowledge/continuity experiments (5–6 Nov 2026)

- **Knowledge design:** physical artifacts, personal memory, speech, ideas, culture, potential/unknown knowledge; exposure, belief, understanding, memory and applied capability are distinct. Directional trust estimates perceived ability, benevolence and integrity. Source provenance and event-linked learning are central design objectives.
- **K-01/TR-01 status:** experimental learning and trust scripts ran independently. Direct observation and written/spoken instruction caused rapid saturation toward perfect understanding; uncalibrated learning rates and missing forgetting, prerequisites, partial understanding, interference and metacognition remain important gaps.
- **Continuity experiment:** a shared-ledger scripted loop joined Founder checkpoint restoration, Soul State availability, ecological generations, teaching and construct refueling. Its documentation records 66 legacy tests and 6-seed 8-/30-iteration comparisons. The 30-iteration population model went extinct. This was **not** an autonomous master engine; demographic steps and daily ticks still required reconciliation.
- **Integration principle:** later social/cognitive and Soul systems must share event identity and physical causality, while retaining distinct personal perceptions and world truth.

### SOCIAL-021 — Autonomous social Founders (6 Nov 2026)

- **User priority:** make Founders social agents before overexpanding geography. Preserve squads, close partners, ambition, competing goals, trust, specialization, shared knowledge and voluntary faction formation.
- **Code introduced:** `founders_civ/experimental/social_agents.py`; 100 seeded Founders with individual traits/goals and role flexibility; partner/squad contact bias; study, practice, teach, aid, coordinate, explore, rest, promises, goal reflection, factions and checkpoints.
- **Mechanisms:** three directed trust dimensions (ability, benevolence, integrity); testimony gives exposure without instant skill; factions require proposal plus two independent endorsements; real aid pays existing energy; promises can be fulfilled or expire; events link intentions with physical transactions.
- **Testing:** `docs/SOCIAL_25_SEED_REPORT.md` records 25 matched seeds x 6 variants x 30 cycles (150 runs; 450,000 Founder decision opportunities), with passing energy/mass audits. Means in the full arm: 8.12 factions; 35.56 faction members; 99.72 Founders with information encounters; 753.36 encounters; aggregate skill 1.14670.
- **Findings and limits:** no-teaching reduced information encounters; isolation increased personal practice time; faction-building consumed attention without institutional production benefits; neutral trust barely changed aggregate outcomes because few costly reliance decisions existed. These are behavior of synthetic utility policies, not empirical psychological validation. Squads/officers in code are provisional assignments; initial agents all begin near House.

### WORLD-022 — Seed-built Sea and integrated Founder/World clock (7 Nov 2026)

- **User direction:** allow Founders to create Worlds (Trees), Realms (Islands), Underworlds (Flowers), Species Sprouts and Dimensions, each via designed, researched, reviewed and planted Seeds.
- **Code introduced:** `founders_civ/experimental/world_integration.py`; `SeedRegistry` and `IntegratedWorld`; a combined ecological tick, Social Founder tick, creation upkeep and shared `Book.audit()`; House/Riverbank/Fields/Ridge interaction graph and local Python-backed Sea UI.
- **Rules:** two distinct research cycles, independent colocated reviewer, blueprint preflight, physical work/material/House energy for planting, maintenance reserve and child collapse when parent realm fails. World Seeding initially created constructs, **not** self-sustaining interior ecologies.
- **Tests:** 96/96 documented stress interventions, including invalid seeds, physical shortages, collapse, checkpoint restoration and conservation. These are internal fixture results, not human/social calibration.
- **Missing:** tree resident populations, complete Underworld functionality, material creation policy, exact Sea navigation, institutions and knowledge calibration.

### WORLD-023 — Living four-habitat World Tree (7 Nov 2026)

- **User milestone:** one tree with four functioning habitats; real resource cycles; a reproducing mortal population; an autonomous observing/researching/stewarding Founder.
- **Code introduced:** `founders_civ/experimental/world_trees.py` with tree/resident/habitat registries; `forest`, `grassland`, `wetland`, `ridge`; plant/soil/water/detritus/chemical/sun accounts; migration, births/deaths, decomposition, resident history, collapse and remnants. The tree cannot populate itself: a separate peer-reviewed Species Seed is necessary.
- **Environmental coupling:** `IntegratedWorld.step()` advances legacy ecology -> internal tree habitats -> 100 Founder social actions -> seed upkeep -> ledger audit. The initial Realm, Tree and Species Seeds are established through a **scripted test bootstrap that executes their actual validation process**, after which the agents choose their own stewardship actions.
- **Results:** source report `docs/WORLD_023_IMPLEMENTATION_AND_TESTS.md` records four 120-cycle trials: three active populated trees, one upkeep collapse. Another 200-cycle seed-400 run retained descendants and a populated tree; the then-current suite reported 124 passing tests.
- **Limits:** one grazer type; synthetic biomass and climate; no full food web, institutional maintenance, distinct physical coordinate geometry or empirical ecosystem parameterization.

### WORLD-024 — Tree commons, productive resources and 100-Founders cooperation (7 Nov 2026)

- **User direction:** world trees should produce food/energy/resources that reward growth and make care worthwhile; preserve failure. Organize as many Founders as possible around one common tree but permit their independent worlds.
- **Code introduced:** `founders_civ/experimental/world024.py` and `run_world024_stress.py`; 100 autonomous Founders may observe, voluntarily join stewardship watch, fund repair from Founder energy, harvest food and eat. Policies `collective`, `owner`, `fragmented`, `none`; extraction `careful`, `intensive`, `none`; optional private Seeds; exogenous rainfall, disease, upkeep and founder-energy stress windows. Existing physical ledger remains authority.
- **Tests:** `docs/WORLD_024_100_RUN_REPORT.md` records ten conditions x ten matched seeds, 80–300 cycles per seed, 100 completed scenarios and 17,600 post-bootstrap cycles. The test matrix includes physical conservation checks; the project also reports 85 inherited + 53 top-level tests.
- **Observed within-model results:** cooperative tree active in 10/10 runs; owner-only 0/10; fragmented 0/10; no upkeep 0/10; intensive harvest 5/10; drought 9/10; high upkeep 7/10. Private options created two additional trees per run but none survived the run horizon. Five 500-cycle follow-ups included a cooperative tree collapsing at cycle 440, demonstrating that cooperation does not guarantee immortality.
- **Interpretation:** redundant watch systems alter maintenance probability and survival; intensive extraction can deplete stocks and compete for steward attention; private creation lacks durable obligations. Survival fractions are consequences of programmed decision rules, not proven sociology.
- **Open physical/economic issues:** food is not yet a portable embodied-energy item; consumption can draw live tree energy; there is no realistic tree-origin timber/mineral construction material chain. House/river energy can reduce tree dependence. Institution contracts are absent; watch rotation is deliberately simplified. The ten seed horizons are linked to seed IDs, limiting clean duration/seed inference.

### INTEGRATION-025 — Compatibility and developer handoff (current build)

- **User request:** support future source code and variations without destabilizing the latest Social/World engine; preserve a development log that distinguishes canon, experimental code and validation.
- **Implementation:** additive `founders_civ/integration/` with a versioned scenario schema, frozen observational DTOs, source-scoped event IDs, shared WORLD-024 bootstrap, experimental hooks, read-only cross-branch normalization and critical-file SHA-256 checks. No changes were made to `core/ledger.py`, `core/engine.py`, Social/World runtime mechanics or existing world policies.
- **Extensions:** built-in event tally + World-Tree history monitor; reviewed user-defined local Python extensions may be enabled explicitly. They receive immutable event/snapshot objects but are *not sandboxed*; only load trusted code. The SDK intentionally does not yet expose unrestricted physical actor actions.
- **New test record:** original suite 100/100 (85 inherited + 15 compatibility tests), top-level 53/53; additionally 16 short matched-seed configurations across eight existing policy/learning variants completed with correct Founder counts and ledger audits. Separate 12-cycle scenario smoke runs completed. Do not compare these short runs as long-term survival outcomes.
- **Status:** release candidate for **opt-in compatibility**, **not** WORLD-025 ecology/governance implementation or promotion to master canon.

## Current status by system

| System | Canon/design | Executable at WORLD-024 | Remaining gap |
|---|---|---|---|
| Founder identities, pairs, squads | established | 100 social actors; 50 pairs; provisional squad indices | verify original roster/officers |
| Goals, ambition, skill learning | established mechanism | yes, synthetic policy | realistic learning calibration, causal identification |
| Directional trust and promises | established mechanism | yes | contingent risk, evidence quality and contracts |
| Knowledge transmission | established | partial | forgetting, prerequisites, partial understanding, false claims |
| Factions and councils | intended | coalition endorsements / voluntary watch | budgets, election, enforcement, long-term obligations |
| Seeds and Realm/World/Species | established creation rule | research, review, plant, tend, collapse | independent thriving world institutions |
| Four-habitat ecology | intended | yes, simplified grazer ecosystem | multispecies trophic and seasonal realism |
| Tree economy | intended | partial food/energy exchange | portable food-energy and construction exports |
| Autonomous stewardship | intended | yes, finite action budgets | backup obligations and conflict resolution |
| Underworld Flowers | source design | construct only | death/soul routing, remnant physics |
| Exact Sea map | source design | schematic interactions | real spatial routes / barriers |
| Core ledger | foundational | authoritative `Book` | multielement matter chemistry |
| Observatory | intended | working local view | cross-tree and institution causal replay |
| Integrations/plugin interfaces | current dev work | 025 read-only hooks + scenario variants | live action plugins, state migration, replay continuation |

## Known technical debt, prioritized

1. **Institutional stewardship:** persistent budgets, accepted responsibilities, backup stewards, late notices, sanctions and successions. Preserve the possibility of collapse.
2. **Embodied food and construction economy:** food carries its own energy after harvest; item/resource provenance tracks tree-to-Founder-to-creation paths without duplication.
3. **Knowledge mechanics:** forgetting, partial/prerequisite mastery, trustworthy teacher evidence, source disagreements and empirical learning-rate calibration.
4. **Ecology:** multiple trophic levels, pollinators, parasites, decomposers, rain/water balance and meaningful carrying capacity.
5. **Temporal semantics:** reconcile days, iterations, generations and reproduction; eliminate seed-duration confounding in long trials.
6. **Creation autonomy and governance:** privately owned trees can recruit stewards, fund upkeep, request council help or be abandoned; institutions endure across individual deaths.
7. **Global event provenance and reliable saves:** one cross-subsystem causal ID graph, rollback boundaries, stable schema migrations and deterministic replay of physical effects.
8. **Map and UI:** real routes and accessibility, ecological maps, multiworld history/research and institution dashboards.
9. **Scientific discipline:** compare against simpler models with matched opportunity budgets and multiple independent seeds; never describe test outputs as consciousness or human realism proof.

## Development workflow going forward

- Write a versioned change proposal naming the parent branch and changed public contracts.
- Mark each change **source canon**, **design inference**, **implemented**, **tested** or **empirically supported**—these labels are not interchangeable.
- Add regression tests and forced failure/invalid-input tests before tuning survival outcomes.
- Use the INTEGRATION-025 scenario schema for governance/harvest/social variations; always record seed and duration separately.
- All physical changes must be source-funded by `Book` transactions; all observations must preserve the actor's limited access.
- Update this log with files, test commands, observed failures, migrations and any unresolved canon conflicts before calling a branch the master release.

## Source register (bundled with project)

- `docs/CANONICAL_SYSTEMS.md`, `docs/VALIDATION_REPORT.md`, `docs/ARCHITECTURE.md` — CORE-018 authority and test claims.
- `docs/RSW_KNOWLEDGE_TRUST_COGNITION_CANON_v019.md` — knowledge/trust design status.
- `CONTINUITY_REPORT.md` and `MASTER_INTEGRATION_AUDIT.md` — continuity baseline, Soul ecology and test limitations.
- `docs/SOCIAL_AGENT_SPEC_v021.md`, `docs/SOCIAL_25_SEED_REPORT.md` — Social architecture and 25-seed trial.
- `README_WORLD_022.md`, `docs/WORLD_022_Implementation_and_Stress_Test_Report.docx` — seed-driven world and 96 stressors.
- `README_WORLD_023.md`, `docs/WORLD_023_IMPLEMENTATION_AND_TESTS.md` — four-habitat tree and earlier 120/200-cycle checks.
- `README_WORLD_024.md`, `docs/WORLD_024_100_RUN_REPORT.md` — 100-run economics/stewardship stress study.
- `docs/INTEGRATION_025/README.md`, `COMPATIBILITY_MATRIX.md` and `BASELINE_HASHES.json` — present SDK code contracts.
- User-authored *Note Oct 11, 2026 2.pdf*, especially pp. 18–27 — original roster, Founder powers, organization and Sea maps (not automatically embedded into this code ZIP).
