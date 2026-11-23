# U026 G2–G3 implementation and promotion plan (2026-11-15)

## Verified starting point
G0 PROMOTE exact Development source f604b9d (CI 43784994919, 497/497 fingerprints, 241 regressions).
G1 PROMOTE exact Development source 35af1fa (CI 43791096282, 515/515 fingerprints, 296 regressions, 20 matched runs). No Core/Integration/Outer/main promotion is implied.
G2 and G3 are NOT promoted. The C041 accepted source remains the rollback reference. Source edits after that commit require new exact-source review.
Development has a later G2 candidate; historical gate attestations are immutable.

## G2: physically real, autonomous WORLD-024 Trees and Founder ecology
Goal: a Tree's habitat and reserves determine physical food/fruit production, maturation, decay, accessible harvest, collapse/remnant, and competitive CE use, with a single Book and 100 independently choosing Founders.

1. Baseline: pin exact Development commit and C041 rollback. Inspect autonomous_provisioning, world_trees, founder_harvesting, founder_tree_agency, founder_parent_stewardship, founder_exchange, world_integration and Book. Audit opt-in feature wiring and any hidden direct stock writes.
2. Source mechanisms: maintain minimum habitat plant reserve before allocating real food/fruit lots; charge plant matter, solar/chemical stocks and finite river CE through atomic Book operations. Make Tree collapse recycle/retain physical lots with stable IDs and no resource duplication. Preserve independent Tree competition, finite propagation, and no scripted top-ups.
3. Founder agency: offer locally observed food and mature fruit; no omniscient inventory or arbitrary energy-per-decision cost. Permit fruit-funded personal World creation even for a Founder owning a parent Realm, but prohibit duplicate personal Worlds when the policy intends one. Ensure refusal, ownership, gift/barter and stale observation remain genuine alternatives. Treat founder-parent care as voluntary and Book-funded.
4. Tests: stale/immature/depleted/foreign lots, double harvest, replay conflict, partial transfer failure, collapse between observation and harvest, simultaneous Trees contesting CE, fruit-to-world funding, and checkpoint/restart. Require zero unauthorized minting and no negative typed stock; compare exact Book audit and canonical state digests.
5. Matched ecology: baseline G1, reserve-first G2, G2+harvest, G2+trade, G2+own-world, and interaction combinations. Aim for 8 arms × 30 fixed seeds at 30/180/360/720/1080 days. Start with 10 seeds × 30/180, then expand only after tests pass and runtime allows. Track accessible food per resident, Tree collapse, Founder decisions, world creation, CE balance, mortality and reproduction.
6. Falsification: reject any arm that mints fuel/CE, uses stale observation to steal, loses deterministic replay, or increases production while depleting habitat below minimum. Do not require ecological improvement for correctness promotion; do not call 180-day conservation evidence G4 stability.
7. Gate: full Core151 regression green, focused G2 tests, 515+ exact source manifest clean, failure-injection clean, all matched manifests reproducible, independent review and a separate G2 PROMOTE/REVISE/REVERT record.

## G3: one scheduler, Founder embodied fuel, digestion and recovery
Goal: preserve 100 Founders with stable IDs and autonomous priorities while ensuring physical work is fuel-funded; planning, deciding and time itself do not consume an artificial energy currency.

1. Baseline: inspect world_integration.step/_proposals/_do, founder_nutrition, founder_recovery, founder_autonomy, founder_exchange, founder_parent_stewardship, social_agents and checkpoint serializers. Identify duplicated ticks, action charges, uncheckpointed RNG and any second inventory.
2. Single schedule: one global tick advances Tree metabolism, resource operations, Founder observation/choice, funded work, digestion, recovery, creation upkeep and collapse in documented deterministic order. Do not advance an isolated Founder or Tree clock in the same integrated run.
3. Physical fuel: ingest identified Book-owned food into embodied chemical storage, digest without instant fuel mint, and mobilize stored chemical energy to usable work with heat/waste losses. Rest reduces fatigue and can mobilize existing stores; rest does not create energy or buy time. Charge only performed physical work, not intentions, decisions or the passing of a tick.
4. Decision ecology: let each Founder compare feeding, rest, exploration, trade, study, creation, stewardship and refusal using local observations and personal values. Test starvation avoidance and rest prioritization without compulsory behavior. Failed work must leave Book and fatigue unchanged.
5. Replay: checkpoint Book, Founder identity, embodied state, fatigue, beliefs, offers, observations, scheduler cursor, operation IDs and RNG. Exact retries may not double digest, mobilize, plant, trade or log a paid effect; conflicting payloads must fail closed.
6. Acceptance: focused work/rest/digestion/adversarial tests; full regression; deterministic replay at transaction boundaries; conservation; matched G2 control vs G3 intervention at same seeds and horizons; report choice distributions, body stores, fatigue, work success, starvation and Tree outcomes.
7. Falsification: reject any branch that creates fuel during rest, double-charges a decision, uses a second Book, changes Founder identity, makes compulsory stewardship, or loses replay. G3 promotion requires independent exact-source acceptance and no unresolved correctness failures.

## Five phases each cycle
I Baseline and falsifiable causal hypothesis.
II Real Development source edit, focused regression and reversible diff.
III Full CI plus matched seeded runs with raw RUN_MANIFEST.
IV Ecological analysis against simpler baseline; PROMOTE, REVISE, REVERT or RESEARCH.
V Preserve branch roles: Development implementation → reviewed scoped Core PR → combined Core+approved Outer Integration tests → stable main only after acceptance. Outer owns WorldBox source/build, backup/rollback and WB-PKG. No native live claim before user Windows copied-save logs.

## Mandatory evidence
RUN_MANIFEST: source_commit, full SHA256 manifest, branch, seed, arm, horizon, command, Python version, tests passed/failed, replay hash, Book mass/energy/CE audit, Founder count, Tree/lot identity, population and failures.
DECISION: exact accepted commit, reviewed scope, matched evidence, nonclaims, falsifiers, rollback and gate owner.
Never treat new plans or instrumentation as implementation.

## Current targeted G2 change
On Development: fix the active-stewardship predicate in founder_tree_agency so a stable parent Realm does not incorrectly count as an already established personal food World. Add a fruit-backed Realm-owner regression and refresh exact candidate fingerprints. This is a candidate change, not a promoted gate. Verify CI on the final source commit before any acceptance decision.

## Remaining backlog
G4 juvenile food/prey refuge, density, predator recruitment, migration and second-generation ecology. P1-09 native identity/epoch and read-only reconciliation. P1-10 independently advancing two Worlds with one Book. P2-11 gated native Tree/fruit/Creation visuals and acknowledgements. WB-PKG must include real Windows DLL build, exact game/assembly hashes, safe-disable, copied-save backup/restore, installer/uninstaller, logs and replay; live verification requires actual user logs. P2-12 RSW/CIV-OS stays in backlog.
