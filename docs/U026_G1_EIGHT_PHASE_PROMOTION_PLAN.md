# U026-G1 — Eight-phase promotion cycle (Core151)

Status: **PLAN / NOT PROMOTED**. Prepared against live `Development` source after G0 promotion. No G1 code change or acceptance result is implied by this plan.

## Target and constraints

Promote **G1: one authoritative Book and physical resource integration** for mass, biological/chemical fuel, heat, and separately typed Creation Energy (CE). Every real lot, fruit, seed, Founder transfer, digestion, construct upkeep and collapse must reconcile to a single Book, with replay-safe identities and conservation. G1 is not G2 Tree physiological value, G3 autonomous-choice success, G4 ecosystem stability, nor live WorldBox runtime support.

G0 evidence: accepted exact source SHA `f604b9d42b5c1547924d9c1346a4ea8668ded208`; promotion record `docs/U026_G0_GATE_STATUS.json` committed as `6a62ab21a4c641a30b6168b20af2e5c0c4c31f1a`; successful follow-up GitHub Actions run `43785239624`: 497/497 source hashes, no missing/changed/forbidden paths, 241 Core151 tests passing, offline WorldBox job passing.

Nonnegotiable: existing Core151 engine and Book only; Development implementation first; no blind merges to Core, Integration, Outer, or main; do not re-approve older C018/C036 attestations by changing them. No automatic Founder Tree feeding or scripted rescue resources. Decisions are not an energy currency; biological work is charged only for physical processes. Provisional CE reservation from finite `river_pool` is not new chemical fuel.

## Eight phases

### 1. Pin G0 and enumerate G1 baseline
- Capture current Development HEAD, immutable G0 source/attestation SHA, workflow results and existing G1 feature-flag defaults.
- Identify entrypoints: `founders_civ/core/ledger.py`, `living_assets.py`, `autonomous_provisioning.py`, `founder_harvesting.py`, `founder_nutrition.py`, `founder_tree_agency.py`, `experimental/world_trees.py`, `experimental/world_integration.py`.
- Deliver a source-and-action matrix and explicitly list any known discrepancies. Do not infer G1 acceptance from the G0 result.

### 2. Trace physical ownership and find actual P0 failures
- Map resource lifecycle: local plants/chemical energy → Tree-owned portable food or Creation fruit → observed Founder harvest → ingestion and later digestion, or fruit + CE → seed funding → physical planting → upkeep/collapse.
- Compare every staged side effect to Book operations, asset IDs, transaction IDs, event references, physical balances and actor/Tree state. Mark derived read-only caches vs competing authoritative stores.
- Primary review candidates: `SeedRegistry.plant()` performs sequential Book work funding, construction and (when enabled) seed germination; `TreeProvisioningPolicy._allocate()` may reserve CE before fruit growth. Inject failures after each possible boundary to determine whether partial commitment is possible.
- Output reproduced failure cases, or negative tests proving the suspected paths safe. Hypotheses are not defects until reproduced.

### 3. Implement atomic cross-step physical operations (P0)
- Fix each reproduced partial-commit path in the **existing** Book-backed engine. Prefer comprehensive preflight and a Book-owned transaction/batch boundary; if state mutations cannot be committed together, use explicit rollback/compensation with test-proven invariants.
- Ensure no irreversible material, CE, energy, lot ownership, transaction journal or creation state changes survive a rejected operation. Do not paper over a physical failure with logs or shadow balances.
- Require deterministic operation IDs, replay returning the same transaction, conflicting replay rejection, permanent lot IDs, and no false asset generation.
- Deliver code + focused failure-injection tests + before/after full-state assertions.

### 4. Implement real Tree production, harvesting and seed funding (P1)
- Validate/fix Tree food and fruit creation with actual accessible plant, chemical fuel, work and finite CE substrate; no recurring free food/charge.
- Harvest transfers exactly one identified physical lot to the correct Founder; ownership and energy move together; stale knowledge may produce rejection, not magical access.
- Confirm seed funding and germination consume the same named fruit and CE once, and upkeep/collapse transforms or transfers balances without duplication.
- Check concurrent/multiple Tree resource contention, repeated lot IDs, depletion and collapsed Tree access.
- Deliver Book-backed positive and negative resource-lifecycle tests.

### 5. Connect Founder physiology and integrated world to the same Book (P1)
- Validate no double writes between WorldTreeRegistry, SeedRegistry, Founder holdings, nutrition and the WorldBox offline adapter. View/event/observation state may mirror a Book value but must not act as independent spendable stock.
- Ingestion is relocation, not immediate work energy. Digestion is delayed and explicitly funded; rest cannot mint chemical energy or spend fictional time as a currency.
- Preserve voluntary proposal/choice: refusal to tend or harvest must be valid agent behavior, not an engine failure.
- Verify one world clock and Book audit after the integrated step; feature-disabled control path still works.
- Deliver integrated end-to-end tests under explicit opt-in settings.

### 6. Falsification, adversarial and conservation tests (P0 regression gate)
- For each transaction and composite workflow, cover: overdraft; half-available paired material/energy; invalid or reused lot; mismatched CE and chemical energy; wrong owner; stale observation; replay identity collision; missing parent; collapse during operation; deliberate failure at each commit stage.
- Failure must be **fail-closed** with unchanged mass/energy accounts, ownership, operations, unique assets, relevant actor/creation state and no committed success event.
- On valid work, require `Book.audit()` conservation and exact expected deltas, a single authoritative transaction trail, no double spend/mint, and deterministic replay.
- Deliver executable regression suite. Do not count instrumentation or plans as repairs.

### 7. Run matched integration and CI acceptance
- Run focused G1 tests and **all existing Core151 regressions**; retain historical provenance and mutation rejection tests.
- Use matched seed scenarios (minimum 10 fixed seeds; 30-day and 180-day horizons) with control and G1-enabled arms, including multiple Trees, resource scarcity, Founder refusal, ingestion, depletion and collapse. These are conservation/integration checks, not claims of G4 ecological stability.
- On each tested run assert one clock, Book audit, no negative spendable balances, no duplicate transaction/asset IDs, and traceability of transfers to Book entries.
- Re-run the offline WorldBox bridge tests without claiming an actual live WorldBox test.
- Log commands, exact seed configurations, source SHA, test counts, failures, and any boundary conditions. A single failure blocks promotion until corrected and all gates rerun.

### 8. Exact-source review, promotion and handoff
- Preserve G0 manifests, historical C018/C036 attestations and run IDs as immutable evidence. For G1 changes, create a **new** exact-source manifest and reviewed G1 attestation, including explicit diff from G0 and rationale for every approved changed file; do not silently rewrite the G0 reference hash.
- Adapt the workflow to enforce the accepted historical G0 baseline **plus** reviewed current G1 delta; the new current-source audit must fail closed on missing, additional, or unapproved changes, generated artifacts, or stale source hashes.
- Require green focused tests, entire Core151 suite, matched scenarios, offline bridge and final enforced audit against the same **exact** Development SHA.
- Only then write `docs/U026_G1_GATE_STATUS.json` with `decision: PROMOTE`, source SHA, manifest/attestation references, CI run IDs and verified scope. Otherwise write `REVISE`, root cause, test evidence, next concrete code change.
- Promotion is the **G1 gate on Development**; a separate reviewed branch promotion/PR is required before changing Core or main. The next gate would be G2 Tree resource value and physical stewardship.

## Explicit promotion criteria

- All physical G1 resource paths go through the one Core151 Book and share its authoritative mass/energy/CE accounts.
- All tested success and failure paths meet atomicity, replay, uniqueness, ownership and conservation invariants.
- No known critical unhandled partial commit or shadow physical ledger.
- Focused G1 tests, full Core151 suite, matched integration runs, reviewed G1 source hashes, fail-closed current audit and offline tests all pass on one recorded commit.
- No ecological-stability, autonomous-adoption, or live WorldBox claims are smuggled into G1 acceptance.

## Immediate engineering priority

**P0 — reproduce or disprove a partial-commit failure in `SeedRegistry.plant()` and `TreeProvisioningPolicy._allocate()`, then implement the smallest Book-native structural fix, not another observation layer.** Record a failing test before the fix and passing tests afterward. G0 source fingerprints must remain historically auditable.
