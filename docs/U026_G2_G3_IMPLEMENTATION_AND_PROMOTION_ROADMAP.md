# U026 — G2 and G3 implementation, experiment and promotion roadmap

**Record type:** Engineering implementation roadmap, not promotion.
**Base branch:** Development.
**Source of truth:** One existing Core151 Book and one existing WORLD-024 integration; never create a second engine, ledger, simulator or forced Founder controller.
**Decision at authoring:** G0 = PROMOTE (Development exact source f604b9d42b5c1547924d9c1346a4ea8668ded208); G1 = PROMOTE (Development exact source 35af1fa5e622d311e22835bfdec9a31c3f9509a5); G2 = NOT_PROMOTED; G3 = NOT_PROMOTED.
**Critical distinction:** G0 and G1 are accepted historical source revisions, not an all-Development merge into Core, Integration, Outer or main. After G1 acceptance, Development acquired further G2 candidate source/test changes. The old acceptance remains valid for its exact SHA, but the new head is **not** automatically attested. Inspect the latest Development ref before each implementation or gate decision. Preserve historical JSON attestations.

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

**G2: Physically real autonomous WORLD-024 Trees and voluntary Founder provisioning.** Prove that Tree habitat and reserve stocks actually fund food/fruit production, maturation, accessible harvest, trade, collapse/remnants and limited CE across multiple Trees, while 100 autonomous Founders can create their *own* Tree when eligible, decline care, and choose real alternatives. One Tree does not feed everyone; no fake rations, mandatory work, omniscient inventories or global planting quota. Independent local food production and agreements are deliberate G2 extensions, not replacements for the existing Book-backed Tree.

**G3: One scheduler and embodied Founder fuel, digestion and recovery.** Prove that the integrated world uses one deterministic tick and Book, with observed Founder food access, body stores, digestion, work actually funded by chemical energy, rest mobilizing existing fuel and reducing fatigue, and no cost for merely choosing or experiencing elapsed time. G3 assesses the effect on survival/food security and keeps refusal legal; second-generation ecological viability, inherited species traits, migration ecosystem-scale tuning and long-term persistence belong to G4.

**Dependency:** G2 must pass a source-scoped acceptance before G3 may be promoted. G3 research can begin experimentally using G2 code, but a failing G2 contract blocks G3 promotion. G0/G1 historical attestations remain immutable throughout; no automatic Core merge.

## 3. G2 eight-phase implementation cycle

### G2.1 — Lock baseline and characterize real missing opportunities

- Capture Development head, Core/Integration/Outer/main ancestry, current 515-path candidate fingerprint and existing G1 promotion JSON.
- Run existing G1 focused, G2 parent stewardship, C017 self-Tree, C019 private autonomy, C020 resource-agreement and full Core151 tests at the same source SHA.
- Construct fixture cases: one fertile Tree/100 Founders; multiple Trees/partial shared resources; no tree fruit; single active owner Tree; non-owner with locally observed resources; no viable parent; private negative upkeep experience; parent reserve exhaustion.
- For each fixture, enumerate *actual executable* Founder choices and valid Book lots. Separate proposed options, chosen options and successfully settled physical transactions.
- Deliver exact-source baseline, failing characterization tests and one prioritized behavioral defect. Do not count this audit as implementation.

### G2.2 — Finish physically funded Tree availability and fix real Founder eligibility

- Validate the newly committed G2 correction in founder_tree_agency.py: owning a stable **parent Realm** must not count as already having a personal WORLD-024 food Tree. The added C017 fixture is a candidate until new exact-source CI passes.
- Preserve the existing policy of **one stable personal World Tree per Founder** unless a separate reviewed requirement changes it; do not force everybody to plant one. The observed fruit/CE plus peer review, habitat material, existing parent Realm and chemical work must all be funded through the same Book.
- Improve parent selection and creation capacity only when tests show a real bottleneck: use observed viable parents, local access, physical reserve and material/CE constraints rather than a global quota or omniscient convenience. Treat the current blueprint-count limit as an explicit experimental guard to evaluate, not proof of food capacity.
- Cover source Tree production and remnant/lot continuity: reserve-first provisioning, food/fruit maturation, decay, exact ID, two Trees contesting finite river CE, collapse after observation, no invisible stock top-ups.
- Tests: Realm-owner may propose/plant a correctly funded Tree; duplicate stable personal Tree remains blocked by policy; missing/mature/depleted fruit; stolen fruit; failed planting and rollback; shared CE exhaustion; deterministic checkpoint; voluntary refusal never coerced.

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

### G3.1 — Lock G2 source, trace the single scheduler and reproduce work/fuel failures

- Freeze a G2-reviewed Development source SHA and rerun the G1/G2 acceptance suite. Read world_integration.step, _proposals and _do, ecological engine.step, WorldTree.step, social_agents, founder_nutrition, founder_recovery and checkpoint serializers.
- Characterize any duplicate ticks, unconditional upkeep, arbitrary per-action fuel fees, out-of-order digestion, mismatched observable holdings or owner-reserve preflight. Keep a failing regression before each behavioral correction.
- Trace actual Book pathways from Tree food and agreements to gut, body chemical store, usable work store and heat; do not equate energy with time.

### G3.2 — Enforce one deterministic scheduling contract

- In experimental/world_integration.py, make the single integrated tick order explicit: physical ecosystem flux, Tree growth and resident feeding, construct upkeep/parent collapse, Founder observation and candidate choices, physical actions, digestion/recovery, event reconciliation and Book audit at safe boundaries.
- Avoid advancing a standalone Founder or Tree clock separately inside the combined world. Do not create another resource inventory or duplicate an existing ecology engine.
- Preserve event/decision IDs and RNG replay across multiple Worlds; no scripted override that forces stewardship or Tree creation. Tests assert clock parity, restart determinism and exactly-once effects.

### G3.3 — Couple ingestion, chemical stores, digestion and real work

- Extend founder_nutrition.py and living_assets.py where tests prove missing behavior: only real owned or consent-received food lots enter gut; digestion transfers physical nutrients/chemical potential to body stores, with waste/heat losses, and does not instantly refill work fuel.
- Physical work such as gathering, traveling, processing seeds, production, repairs and active maintenance draws appropriately from existing chemical fuel through the Book. A cost is paid only if the work is executed; an unsuccessful or declined choice does not spend energy by fiat.
- Strictly separate finite river CE from bodily chemical fuels. No WorldBox-native body-state writes.

### G3.4 — Make voluntary recovery and self-maintenance useful, not compulsory

- In founder_recovery.py, treat rest as a chosen activity that reduces fatigue and can reallocate existing embodied chemical stores into usable work while directing losses to heat; it never manufactures energy or purchases elapsed time.
- Let Founder preferences compare food, rest, local search, trade, study, Tree creation, exploration, Realm care and refusal using personal valuations, locally perceived opportunities and actual body condition. Preserve private learning and heterogeneity.
- Test low-fuel and high-fatigue trajectories, predation/accident fallback where present, no energy-per-decision, incomplete digestion, failed work preserving Book plus fatigue, repeated rest receipt idempotency and decline.

### G3.5 — Repair cross-scale physical funding and resource competition

- Ensure Tree growth and stored fruit/food remain grounded in real source plant/sun/chemical stock, with reserve-first and resident-competition boundaries. Founder resources cannot be replenished merely by observing a tree or receiving an offer.
- Explicitly handle food scarcity and physical inability to perform actions: try actually reachable alternatives or fail; do not force replenishment, freeze time as a substitute, or rely on universal action energy gates.
- Juvenile food access, inherited species specialization, spatial refuge and migration mechanisms may be profiled but are **G4 candidates** unless needed to repair a demonstrated G3 integration bug.

### G3.6 — Checkpoint, replay and failure-injection enforcement

- Checkpoint Book operations and stock, unique lot and Founder IDs, actor bodies, fatigue, private values, accepted/withdrawn offers, observations, scheduler cursor, RNG, Tree/Realm status and one authoritative tick.
- Inject failure between paired food/chemical transfers, digestion, rest work mobilization, voluntary upkeep, planting and event emission; require exact rollback and no duplicate social effects.
- Verify exact retry and conflicting-payload rejection, deterministic state hash after checkpoint resume and conservation with all resource types.

### G3.7 — Matched viability and physical opportunity trials

- Pre-register an 8-arm x 30-seed matrix after passing focused tests: three binary axes are (a) embodied work/rest revision, (b) scarcity-aware food/consumption prioritization and (c) local trade/food alternative access. G2 Tree ownership and provenance contracts remain constant.
- Run 10 seeds x 30/180-day smoke tests first; expand to 30 matched seeds and 360/720/1080-day continuations for feasible paired subsets. Every run reports an actual horizon or NOT_RUN.
- Record Founder fuel/body stocks, fatigue and action work success, rest decisions, survival, starvation, physically acquired/ingested/digested food, Tree supply, parent reserve, resident competition, voluntary stewardship/refusal and mass/energy/CE audits. Compare with simpler scarcity-only and fixed-preference baselines.
- This experiment can identify causes of survival differences, but **G4** alone will decide multigeneration stability, predator recruitment and ecological equilibrium.

### G3.8 — Independent exact-source promotion decision

- Add real, focused tests (planned: tests/test_u026_g3_scheduler_metabolism.py) and a matched runner (planned: tools/u026_g3_matched_acceptance.py); only label them implemented after GitHub contains executable code.
- Promotion requires all G0/G1/G2 invariants, one Book and clock, energy charged only for actual physical work, fully conserved digestion/recovery/heat, unforced Founder choices, deterministic checkpoint and rollback, complete Core151 regressions, matched control evidence, exact-source SHA validation, all CI jobs green and independent review.
- Do not require every Founder or ecosystem to survive; explicit starvation or collapse under real scarcity remains a valid outcome. If any correctness condition fails, REVISE or REVERT on Development. Preserve G0/G1 source approval records, and never claim native WorldBox success from an offline sidecar.

## 5. Test matrix, safeguards and release order

**Invariant tests (every code change):** (a) one Book identity across ecology, Trees, Founders, constructs; (b) mass, chemical and CE conservation independently; (c) no double receipt/event; (d) correct owner/consent/proximity; (e) refusal never silently replaced with maintenance; (f) no time/action currency; (g) partial-failure rollback; (h) deterministic checkpoint; (i) no source drift accepted without review.

**Proposed first implementation targets, in dependency order:**
1. G2: verify the already committed parent-Realm-versus-personal-Tree eligibility correction, then correct the next proven bottleneck in real Tree supply, local access or shared finite CE; preserve the one-personal-Tree policy until separately reviewed.
2. G2: build one real Book-funded non-Tree food alternative and demonstrate voluntary choice against existing Tree harvest/trade, with no external stock.
3. G2: verify local, consensual cooperation and private value learning across realistic outcomes and retries; run matched scenarios and promote or revise.
4. G3: integrate one scheduler, physically paid work, no instant digestion fuel, and voluntary rest/fatigue recovery in reviewed small changes. Assign broader juvenile prey, inherited specialization and migration to G4.
5. G3: execute one-Book/one-clock physical-energy controls and independent source acceptance; hand ecological persistence, juvenile recruitment and trophic-stability hypotheses to G4.

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

**Immediate next cycle:** Reconcile the concurrent G2 parent-Realm eligibility correction and its C017 tests against the current Development SHA, refresh exact-source audit, rerun focused/full CI, then implement the next falsified G2 physical-food/Tree supply limitation. A documentation-only roadmap is not a promoted gate. Only a verified source diff and passing CI can count as implementation progress.
