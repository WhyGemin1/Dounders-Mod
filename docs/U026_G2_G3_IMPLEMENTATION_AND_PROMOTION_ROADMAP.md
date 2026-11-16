# U026 — G2 and G3 implementation, experiment and promotion roadmap

**Record type:** Engineering implementation roadmap, not promotion.
**Base branch:** Development.
**Source of truth:** One existing Core151 Book and one existing WORLD-024 integration; never create a second engine, ledger, simulator or forced Founder controller.
**Decision at authoring:** G0 = PROMOTE (Development exact source f604b9d42b5c1547924d9c1346a4ea8668ded208); G1 = PROMOTE (Development exact source 35af1fa5e622d311e22835bfdec9a31c3f9509a5); G2 = NOT_PROMOTED; G3 = NOT_PROMOTED.
**Critical distinction:** G0 and G1 are accepted historical source revisions, not an all-Development merge into Core, Integration, Outer or main. The G1 source currently has two subsequent promotion-record-only documentation commits; new implementation changes will need their own exact-source acceptance. Preserve historical JSON attestations.

## 1. Verified baseline and evidence

| Gate | Accepted Development source | Independent Actions evidence | Scope |
| --- | --- | --- | --- |
| G0 | f604b9d42b5c1547924d9c1346a4ea8668ded208 | https://github.com/WhyGemin1/Dounders-Mod/actions/runs/43784994919; 497/497 hashes, 241/241 regressions, successful offline checks | Exact-source provenance at historical G0 revision |
| G1 | 35af1fa5e622d311e22835bfdec9a31c3f9509a5 | https://github.com/WhyGemin1/Dounders-Mod/actions/runs/43791096282; 515/515 hashes, 296/296 regressions, 17 focused G1, 10 focused stewardship, 20/20 matched runs; all three jobs green | Single Book, atomic/replay-safe physical funding, CE separation, Tree/Founder nutrition/creation, checkpoint/conservation |
| G1 follow-on | Same code revision, subsequent documentation records | https://github.com/WhyGemin1/Dounders-Mod/actions/runs/43791146755; all three jobs green | Further confirmation of focused and full tests, not a Core merge |

G1 20 matched runs = 10 seeds, control and opt-in arms, 30- and 180-day checkpoints. Neither G1 nor G0 demonstrates long-term ecological equilibrium, viability of every creation, second-generation reproduction, native WorldBox execution or arbitrary historical source acceptance.

**Working mechanics already present (extend rather than rewrite):**
- founders_civ/core/founder_autonomy.py — opt-in heterogeneous private valuation and experienced-outcome updates; explicit decline_investment.
- founders_civ/core/founder_tree_agency.py — opt-in Founder-authored independent WORLD-024 Tree research and physically fruit/CE-funded seeds.
- founders_civ/core/founder_parent_stewardship.py — local reserve inspection, voluntary Founder-to-parent Realm fuel transfers, exact Book replay.
- founders_civ/core/founder_exchange.py — opt-in, local, consensual Book-settled food/fruit gifts and whole-lot barter; no parallel market inventory.
- founders_civ/core/autonomous_provisioning.py — finite reserve-first Tree food and fruit production; actual plant/chemical/CE accounts.
- founders_civ/core/founder_nutrition.py and founder_recovery.py — verified ingestion/digestion distinction and chosen rest with energy mobilization/heat, not fuel minted by elapsed time.
- founders_civ/experimental/world_integration.py — one Book and scheduler, creation/Realm custody, opt-in flags, real action selection.
- founders_civ/experimental/world_trees.py and founders_civ/core/engine.py — physical Tree resident, feeding, ecological flux and death/recovery mechanics.

**Current limitations requiring implementation, not new dashboards:**
1. Self-Tree agency is still constrained by the blanket _has_active_stewardship check; an actor with an existing stable creation is not offered another self-Tree. The fixed blueprint-count cap and a single least-loaded parent Realm choice are imperfect proxies for capacity, access and incentive.
2. The exchange policy supports existing food/fruit lots but not independent non-Tree food production, cultivation, or physically meaningful local fallback supplies.
3. Care is still partly scored from synthetic urgency; proposals must remain optional, responsive to personal beliefs and observations, with refusal, trade, self-provision and collapse all valid paths.
4. The 8/12-day provisioning periods, 5-day fruit maturity, reserve threshold and many chemical-energy coefficients are synthetic defaults, not yet demonstrated across varied habitat carrying capacities.
5. Founders and Tree residents have limited resource-access/migration and ecological specialization. G1 conservation acceptance is not proof of sustainable trophic recruitment, predator reproduction or juvenile survival.
6. New source edits require reviewed full SHA-256 fingerprinting, complete regressions, matched simulation evidence and a separately decided G2 or G3 gate.

## 2. Gate contracts and dependency rules

**G2: Voluntary decentralized provisioning, agency and stewardship.** Prove that 100 autonomous Founders have physically attainable alternative strategies, can observe/learn private advantages of Trees and care, voluntarily create additional independent Trees, harvest or produce food, make and refuse consent-based resource agreements, and conserve all transferred matter and chemical/Creation Energy in the *existing Book*. G2 does not mandate that everyone plants or maintains a Tree. Scarcity, disinterest, trade refusal and collapse are legal outcomes.

**G3: Physical productivity, fuel and ecosystem access.** Prove that the G2 opportunities are supported by viable, spatially and temporally explicit food/chemical-energy throughput, competing users and residents, habitat constraints, metabolic recovery and migration/fallback pathways. Organisms should spend energy on actual physical work and use bodily stores/rest to change efficiency; time never becomes an energy/action currency. G3 must preserve mortality and ecological failure, not secretly repair populations. Long-run population persistence is assessed here but is a distinct G4 stability gate.

**Dependency:** G2 must pass a source-scoped acceptance before G3 may be promoted. G3 research can begin experimentally using G2 code, but a failing G2 contract blocks G3 promotion. G0/G1 historical attestations remain immutable throughout; no automatic Core merge.

## 3. G2 eight-phase implementation cycle

### G2.1 — Lock baseline and characterize real missing opportunities

- Capture Development head, Core/Integration/Outer/main ancestry, current 515-path candidate fingerprint and existing G1 promotion JSON.
- Run existing G1 focused, G2 parent stewardship, C017 self-Tree, C019 private autonomy, C020 resource-agreement and full Core151 tests at the same source SHA.
- Construct fixture cases: one fertile Tree/100 Founders; multiple Trees/partial shared resources; no tree fruit; single active owner Tree; non-owner with locally observed resources; no viable parent; private negative upkeep experience; parent reserve exhaustion.
- For each fixture, enumerate *actual executable* Founder choices and valid Book lots. Separate proposed options, chosen options and successfully settled physical transactions.
- Deliver exact-source baseline, failing characterization tests and one prioritized behavioral defect. Do not count this audit as implementation.

### G2.2 — Replace hard-coded Tree bottlenecks with physically available choices

- Modify founder_tree_agency.py so ownership of one stable Tree/Realm does not by itself forbid creating or collaborating on a second Tree; bound creation by finite fruit/CE, soil/water, reviewed seed, parent capacity and available labor, not by a target count of Trees.
- Replace a blanket least-loaded-parent choice with candidate parents grounded in known local location, observed reserve, remaining ecological capacity, agreement/consent and existing physical inputs; no omniscient Book reads exposed as Founder knowledge.
- Retain peer research/approval and transaction-funded seed/plant identity; a refused proposal is not a bug and an unfunded attempt must fail without partial changes.
- Tests: independently funded multiple Trees, owner with existing Tree, unreachable parent rejected, parent collapse mid-creation, asset ID replay, no forced plant, no new mass/CE.

### G2.3 — Implement independent finite food alternatives

- Add an opt-in Founder foraging/cultivation mechanism, using actual local ecology plant/soil/water/sun/chemical accounts and the same Book; no global free rations, new reserve ledger or time-as-work currency.
- Distinguish observation, gathering, cultivation, carrying, eating, digestion and resting. Ecological reserve must remain available to habitat residents, with failure when harvest would exceed supply.
- For cultivated crops, consume real seed/plant matter and suitable habitat inputs, allow growth and decay via accounted flux, and produce a stable lot only after an actual successful transition. Prefer existing TreeResourceOps/Book patterns and a small new physical adapter to a second simulated world.
- Add acceptance fixtures for non-Tree food with and without Tree access, seasonal depletion, spoiled lot and resource competition. Verify physical food cannot instantly turn into Founder usable energy.

### G2.4 — Make cooperation and resource agreements meaningful but consensual

- Extend founder_exchange.py only where needed for G2 resources and multi-actor contributions: optional gifts, whole-lot barter, shared cultivation access and voluntary Tree/Realm upkeep agreements. Both parties can decline or ignore.
- Resolve any partially fulfilled cooperation through a single Book transaction or explicit rollback; do not trust UI/agent-level receipts without Book ownership and idempotency checks.
- Use actual local contact/meeting requirements; keep unsolicited remote transfer, forged lot, withdrawn offer, replay with different payment and duplicate settlement negative tests.
- Resource agreements have opportunity cost and can be economically unattractive; no global utility override and no mandatory commune/market.

### G2.5 — Preserve private learning and genuine Founder self-direction

- Modify founder_autonomy.py and integrated action selection only where characterization tests show a systematic blockage. Learned Tree value comes from a Founder's own observations, consumption, trades, failures or shared human testimony with explicit provenance, not from omniscient world events.
- Keep multiple independent alternatives live when materially possible: rest, food, exchange, research, exploration, cultivation, Tree creation, selective stewardship, refusal.
- Retain personal heterogeneity across the 100 Founders; do not force a quota of caretakers, farms or Trees. Preserve meaningful stochastic choice and the real possibility of refusing needed upkeep.
- Tests: divergent choices with identical public state but distinct private history; no Book mutation by merely ranking/proposing; learning cannot mint food or access remote resources; checkpoint restores personal memory and choices.

### G2.6 — Lifecycle, replay, failure and rollback hardening

- Integrate Tree/Realm upkeep, fruit harvest, acquired lots, cooperative production, physical energy payments, decay, death and collapse with original Book operation IDs.
- Fault-inject at each boundary between physical transfer, world ownership/construct creation, event emission and checkpoint serialization. Prevalidate or atomically roll back multi-system commits; duplicate replay must not duplicate Book debits, resource ownership or social events.
- Preserve ownership of already-transferred food after a source Tree collapses; prevent claiming another Founder's holdings or reusing spent seed fruit.
- Require deterministic resume for at least two checkpoints (after receipt and after world transition) and re-run all G1 tests, not merely new G2 tests.

### G2.7 — Matched experimental tests and falsification

- First smoke: 8 treatment arms x 10 matched seeds x 30/180 days (same initial conditions and seed per arm).
- Full candidate: 8 arms x 30 matched seeds, reporting both 30- and 180-day checkpoints; extend selected pairs to 360 days only if initial acceptance tests are clean.
- Suggested 8 arms: factorial toggles of private-learning/agency, independent provisioning/Tree options, and consensual exchange, with the shared voluntary stewardship opportunity held constant and never mandatory. Define arm switches exactly in manifests before running.
- Record: independent Trees per owner, actual creation and collapse, non-Tree food lots produced/consumed, offers/accepts/declines, local access distance, individual food security, energy/fatigue, CE usage, real Book transfers, unique assets, parental upkeep and ecological resident cost.
- Main falsifiers: mechanics only work because of scripted Founder preference, impossible Tree supply, nonlocal knowledge, coerced consent, hidden stock minting or unexplained duplicate receipts. No minimum global Tree count is required for G2 passing.
- Compare outcomes to simple scarcity and opportunity-access explanations; do not claim behavioral improvement just because total actions increase.

### G2.8 — Independent acceptance and promotion decision

- Add focused tests in tests/test_u026_g2_voluntary_economy.py and an executable matched runner at tools/u026_g2_matched_acceptance.py (planned paths). Integrate focused, full and fail-closed provenance checks into existing CI.
- Pass conditions: no G1 regressions; all funded G2 fixture opportunities genuinely executable; explicit refusal/ownership/access enforced; zero unauthorized material/chemical/CE minting; checkpoint replay and rollback exact; full Core151 suite green; completed paired simulation manifest; independent exact-source SHA audit clean; CI passes at same commit.
- Document decisions as PROMOTE, REVISE or REVERT in a new docs/U026_G2_GATE_STATUS.json only after proof. An observed collapsed Tree or a Founder declining upkeep is not itself a gate failure.
- If accepted, freeze the source SHA and G2 receipt/choice contracts before enabling G3 candidate changes.

## 4. G3 eight-phase implementation cycle

### G3.1 — Quantify ecological and energy bottlenecks from G2

- Run source-matched G2 control/treatment cohorts and compile Book-funded flows: sunlight -> photosynthetic chemistry; plants -> residents/food; digestion -> body stores; resting -> usable store and heat; death -> carcass/detritus; Realm/Tree maintenance -> reserve heat and collapse.
- Distinguish starvation caused by no food production, unreachable food, too little time for development, unmatched partners, overcompetition, excessive metabolism, insufficient rest, reproduction gating and patch-specific bottlenecks.
- Use only already available histories/Book records and published ecological principles where needed; do not replace implementation with instrumentation.

### G3.2 — Close physically coherent primary productivity and reserves

- Extend core/engine.py, experimental/world_trees.py and core/autonomous_provisioning.py to account for per-patch soil nutrient, water, sunlight, temperature/season, plant maintenance, storage and finite growth.
- Eliminate arbitrary free food/regrowth or heat-to-food conversions. A World Tree's harvestable surplus must be after living residents and reserve-first maintenance. Neither one Tree nor a single parent Realm may produce unlimited sustenance for 100 Founders.
- Demand explicit source funding for each resource; distinguish amount produced, amount accessible, amount harvested and amount actually digested.
- Test drought, wetland, resource-rich coast, degraded ridge and forest conditions with no independent magic supply. Keep all coefficients configurable and empirically compared rather than claiming authentic biology.

### G3.3 — Replace simplistic animal energy gates with embodied metabolism

- Integrate core/founder_recovery.py, founder_nutrition.py, world-tree resident feeding and ecology engine work costs. Stored food does not instantly become usable fuel; digestion transfers actual chemicals, rest preserves/reallocates fuel and improves fatigue/efficiency.
- A Founder or animal does not purchase time with energy. Charge only modeled physical work such as travel, thermoregulation, active foraging, attack, seed processing or tissue repair; observation/social choice and mere existence are not uniformly debited.
- Energy deficiency can reduce output, alter preferences and increase risk; it must not universally forbid doing anything. Heat, waste and matter outputs remain Book-conserved.
- Test energy balance across active/rest/digest cycles; no rest-created fuel, CE-as-metabolism, negative stores, one-ULP overdrafts or unconditional survival rescue.

### G3.4 — Specialization, juvenile acquisition and reproduction pathways

- Give resident species explicit biologically meaningful trait ranges/phenotypes (body condition, feeding efficiency, movement range, defense, reproductive maturity and energy retention), with inheritance/variation where applicable.
- Juveniles need physically accessible food and safe shelter; predator viability depends on prey recruitment, hunting opportunity, reserves and losses, not a hard-coded prey count multiplier.
- Connect breeding eligibility to physical reserves, mate proximity, local conditions, dependent offspring costs and actual survival opportunities. Maintain death and failed breeding as possible.
- Implement trait mechanics behind opt-in flags and compare them against the simpler fixed-trait baseline before declaring improvement. G4, not G3, is the gate for verified long-horizon population stability.

### G3.5 — Local spatial alternatives, migration and fallback behavior

- Use the existing World Tree habitat patches and authoritative Core151 ecology rather than spawning a second map engine. Expand spatial resource reachability, travel costs and local observations to support multiple niches and independent food sources.
- Add feasible fallback: migrate to known nearby habitat, pursue alternative edible resources, retreat/rest, trade/gather with Founders, or fail if nothing is accessible. No teleportation, omniscient supply choice or scripted rescue.
- Test resident competition, crowding, predation, seasonal food depletion and isolated refuges; ensure expanding map size increases options only where physical connectivity/resources exist.

### G3.6 — Cross-scale integration, rollback and deterministic checkpoint

- Tie Tree production and ecological resident survival to actual Book balances without doubling resources in Tree-resident object fields. A Tree collapse returns/retains resources in traceable remnant accounts, not vanishing or reminting stock.
- Fault-inject birth, death, food consumption, migration, Tree growth, maintenance, world-seed funding and shared-resource agreements mid-transaction; verify failure leaves Book and world in a valid, replayable state.
- Verify canonical Founder, resident, Tree, Realm, lot, migration, event IDs and scheduler tick across replays and resumed trajectories.

### G3.7 — Ecology stress matrix and simple-explanation comparisons

- Pre-register 8 candidate arms x 30 seeds, all using identical initial Book stocks, species pools and world setup within each matched seed.
- Three mechanism axes: revised bodily energy/rest, habitat production/access, and species specialization/movement. Keep controls with all mechanisms disabled and single-factor arms; preserve real failure.
- Run 30/180-day checks first, then 360/720/1080-day continuations for matching successful and failing cohorts as capacity permits. Never hide truncated runs, cherry-pick seeds or claim 1080 days if only 180 ran.
- Report real biomass and chemical conservation, species/age counts and densities, births/deaths, juvenile-to-adult recruitment, second-generation reproduction, predator/prey ratios, forage availability, starvation vs predation causes, patch use, Founder access, collapsed vs living Trees, and Book-to-reported-state consistency.
- Explicit countertheories: space/density bottleneck, scarce physical energy, unreachable food, juvenile handling, overly expensive action costs, unrealistic reproductive gates, and actual predator-prey collapse. Test combinations and compare to simpler models; ecological stability is a separate G4 decision.

### G3.8 — Source review and promotion gate

- Implement focused executable tests in tests/test_u026_g3_energy_ecology.py, an 8-arm manifest runner in tools/u026_g3_ecology_matrix.py, and new candidate provenance and decision documents (planned paths).
- Pass conditions: all G0/G1/G2 behavioral contracts remain intact; one Book; no energy/CE/matter mint or negative stocks; every produced food/resource path has traceable physical inputs; rest/digestion/action work semantics match the contract; migration and species specialization function without hidden rescues; deterministic restart; full suite green; pre-registered stress controls executed; exact-source CI audit clean.
- No requirement that all ecosystems always survive. G3 must expose causal mechanisms and failure conditions, not guarantee stable multigeneration ecology (G4).
- PROMOTE only after source-scoped independent review and an exact commit Actions success. Otherwise REVISE with one concrete failure and targeted next implementation, or REVERT the candidate change without rewriting historical approvals.

## 5. Test matrix, safeguards and release order

**Invariant tests (every code change):** (a) one Book identity across ecology, Trees, Founders, constructs; (b) mass, chemical and CE conservation independently; (c) no double receipt/event; (d) correct owner/consent/proximity; (e) refusal never silently replaced with maintenance; (f) no time/action currency; (g) partial-failure rollback; (h) deterministic checkpoint; (i) no source drift accepted without review.

**Proposed first implementation targets, in dependency order:**
1. G2: reproduce and fix the _has_active_stewardship/one-Tree limitation while preserving scarce CE and source Book ownership.
2. G2: build one real Book-funded non-Tree food alternative and demonstrate voluntary choice against existing Tree harvest/trade, with no external stock.
3. G2: verify local, consensual cooperation and private value learning across realistic outcomes and retries; run matched scenarios and promote or revise.
4. G3: close photosynthesis/plant reserve and transfer-to-consumer supply, then physical rest/digestion for each relevant organism, then juvenile access and movement/specialization, in tested small changes.
5. G3: execute cross-scale stress cohorts and independent source acceptance. Hand ecological persistence hypotheses to G4.

**Execution commands from the repository root:**

    cd Founders_CIV_CoreCompletion151/source/world023024
    PYTHONPATH=. python -m pytest -q tests/test_u026_g1_exact_replay.py tests/test_u026_g2_parent_stewardship.py
    PYTHONPATH=. python -m pytest -q tests

    # From repository root after refreshing the candidate source snapshot:
    python tools/u026_g2_exact_source_audit.py
    python tools/u026_g1_matched_acceptance.py --seeds 10 --days 180

The planned G2 and G3 test runners must not be represented as existing scripts until implemented.

**Artifacts required per gate:** exact branch+commit; reviewed code diff; regression and negative-test logs; source manifest of exact SHA-256 bytes; matched seed/arm/horizon run manifests; checkpoint state digests; Book audits; ecological mechanisms and countertheories; explicit PASS/FAIL/NOT_RUN per acceptance; rollback instructions; independent reviewer; final PROMOTE/REVISE/REVERT decision. Store raw evidence links, not just summary claims.

**Branch policy:** Development implements one real, reviewable change at a time. Core accepts only scoped, regression-passing approved changes; the 121-commit Development lead is not permission to merge all history. Integration checks combined Core plus selected adapter. Outer/WorldBox remains offline-only until tested in the actual native runtime. main stays stable. Old G0/G1 attestation records must never be rewritten or interpreted as current-head approval after new source edits.

**Immediate next cycle:** G2.1 characterization followed by the minimal G2.2 behavioral correction and focused/full tests. Only a verified source diff and passing CI can count as implementation progress.
