# Single-engine development ledger

## 2026-11-15 — unified engine cycle 1

- Main SHA at branch creation: `26a02ba50a53770b14eae0368315ea01036d0b3c`.
- Working branch: `feat/single-core151-authority`.
- Actual recovered source: local `Founders_CIV_Cycle152_SparseFounding_Experimental.zip` plus M01 runtime/gateway overlays from historical packages, including Cycle14 crash runtime. This engine retains the original Book and clock.
- Change: `src/founders_engine/authority.py`, `tests/test_authority.py`, `docs/SINGLE_ENGINE_AUTHORITY.md`, `engine/ACTIVE_ENGINE.json`. No alternate simulator implemented.
- Executed locally against recovered Core151 source: `PYTHONPATH=<patch>/src:<Core151>/source/world023024 python -m unittest discover -v -s <patch>/tests -p test_authority.py`: **6/6 passed**. One tick of actual `IntegratedWorld`, Book audit, 100 Founder check, invalid Founder claim rollback check, rejection of second Book and clock.
- Not run: GitHub CI, WorldBox in-game, complete Core151 regression suite, 30+ day ecological tests. No actual WorldBox mutation. Do not infer M05 live integration from its compiled source/repair instructions.
- Blocker: Core151 full Python source is available locally in the verified historical archive but is still not tracked as individual source files in GitHub. This PR is a tested integration boundary, not a complete executable engine checkout.
- Next: Git-track the original validated Core151 source files, reconcile M01 overlays, run full regression and Book checkpoint tests. Preserve all prior code history until verified migration.

## 2026-11-15 — unified engine cycle 2: source recovery and deterministic importer
- Recovered the exact authorized Drive archive `Founders_CIV_Cycle152_SparseFounding_Experimental.zip` (956,121 bytes), SHA-256 `29c6bc0a650a6b3c48d3f7cdc2ab49e94592f6243cdfc36a168416b514a54cd8`. This matches the prior historical handoff fingerprint.
- Source inspection identified 27 Python files under `Founders_CIV_CoreCompletion151/source/world023024/`: 25 `founders_civ/` modules plus `knowledge_architecture.py` and `run_world_tree_pilot.py`.
- Implemented and committed `tools/import_core151.py` and `tools/test_import_core151.py` on `feat/single-core151-authority`. Importer verifies full archive SHA, selects only the single world source tree, rejects modified existing files and missing required dependencies, and generates a per-file SHA-256 manifest.
- **Executed locally:** `python -m unittest -v test_import_core151` => 3/3 PASS (0.036 seconds). `python import_core151.py <authorized_zip> <staging_dir>` => 27 source files extracted. This is a source-import staging test, not an ecological simulation.
- **NOT RUN:** Book audit, Founder tick, full regression, GitHub CI, WorldBox in-game, clean-checkout authority tests. No additional energy/resource mechanics implemented.
- **BLOCKER:** GitHub now has the importer but does NOT yet contain the 27 extracted engine source files as separately tracked Python modules. The local staging directory is not GitHub; do not report source migration as complete. No canonical/main changes or merges.
- **NEXT:** Commit the 27 verified source text modules and manifest to `src/` on this same branch, then execute clean-checkout tests and checkpoint/Book audits.

## 2026-11-15 — unified engine cycle 3: source-import hardening
- Working branch: `feat/single-core151-authority`, main baseline remains `26a02ba50a53770b14eae0368315ea01036d0b3c`; PR #2 remains draft.
- Verified Google Drive metadata for the Cycle152 archive: ID `1qHrQpL41J9v-mNxP-uPNS0ZtTzal3bUE`, 956121 bytes. **Archive bytes could not be materialized in this invocation**, so prior SHA-256 is historical, not freshly recomputed.
- Source change: `tools/import_core151.py` rejects duplicate ZIP members, path traversal, symlink source members, oversized/overcounted source trees, symlink destination paths, and mismatched existing manifests before writing; `tools/test_import_security.py` adds nine synthetic fixture tests. No second simulation engine.
- **Executed locally** using an equivalent import implementation and synthetic ZIP fixtures: `python -m unittest -v test_import_security` => 9/9 PASS (0.021s). This was not executed against a clean GitHub checkout; committed version still needs CI validation.
- **NOT RUN:** real Cycle152 import, 27-source-file GitHub commit, Book conservation audit, Founders step/checkpoint, WorldBox in-game, ecological simulation, GitHub CI.
- **BLOCKED:** exact Drive ZIP is visible as metadata but its bytes are not exposed by the available connector; Library search and local runtime did not contain it. Importer and source tree are still separate. No canonical/main change.
- **NEXT:** acquire the actual archive bytes through an authorized file-materialization route, verify archive hash, commit 27 .py modules and manifest to `src/`, then run clean-checkout authority and checkpoint tests.

## 2026-11-15 — Cycle4: actual source import

- Verified Google Drive archive bytes and SHA256 `29c6bc0a650a6b3c48d3f7cdc2ab49e94592f6243cdfc36a168416b514a54cd8` (956,121 bytes).
- Imported 27 original Core151 Python modules as individually tracked text files under `src/founders_civ/` plus `src/knowledge_architecture.py` and `src/run_world_tree_pilot.py`; commit `7f96cba5cb283688e0c30a40e75a049d05c7e772`. No alternate engine created or historical source overwritten.
- Tests executed locally from exact recovered source: 6/6 knowledge architecture unittest PASS; 1/1 Book/clock/100-Founder smoke PASS; seed400 1-day pilot PASS, 16 World Tree residents, Book mass error -2.7284841053187847e-12, energy error -1.1175870895385742e-08. These are headless, not game tests.
- Git clone from container failed DNS resolution (`Could not resolve host: github.com`); no clean GitHub checkout or CI run claimed. M01 gateway overlay still missing from GitHub, so preexisting `tests/test_authority.py` cannot run from clean checkout. WorldBox in-game NOT RUN.
- Next: recover and import M01 Book gateway overlay; execute clean-checkout tests and checkpoint/rollback verification; preserve single Book and clock.

## 2026-11-15 — Cycle5 M01 integrated Book-funded harvest
- Branch: `feat/single-core151-authority`, base main `26a02ba50a53770b14eae0368315ea01036d0b3c` (main not edited).
- Recovered exact Drive Cycle152 ZIP to local runtime; extracted Core151 sources. GitHub tree at `358dcd1deb67b567cfec05ffbad9e0d03a27b2d0` contained 27 tracked Python modules and no `worldbox_gateway_m01.py`.
- Added `src/founders_civ/experimental/worldbox_gateway_m01.py` (commit `ecc161a1a0aa3e542a22d9af601bc5099f0daa29`) and `tests/test_m01_gateway_integration.py` (commit `8b5defa0397874e3bfe6b11946823e4f7d4bcba9`). Gateway transfers already-existing plant/detritus mass and optional chemical energy from the living World Tree to Founder inventory using the SAME Core151 Book; no new simulator, no external WorldBox API, no minting. Invalid Founder, collapsed tree, overdraw, duplicate local request rejected.
- Executed locally: `cd /mnt/data/core_run && python -m unittest -v test_m01_gateway_integration.py` -> 6/6 PASS (0.650s). First test attempt failed 2/6 because tests shared mutable world across cases; corrected test isolation (fresh bootstrap per case), reran PASS. No fabricated checkpoint or in-game results.
- Verified 100 Founder identities, one clock advances by one, one Book authority; mass/energy move audit passed and failed/duplicate request leaves Book sequence unchanged. Does not establish digestion, biological usefulness, WorldBox transfer, or native actor behavior.
- Critical blocker: request replay guard uses in-memory authoritative world events; checkpoint persistence and exactly-once recovery after process restart NOT VERIFIED. The logging-after-Book-commit crash boundary also requires durable atomicity design. Do not enable native WorldBox transfers or claim production-ready gateway.
- Next: run clean-checkout tests from the GitHub branch and implement/test checkpoint-persistent idempotency/atomicity without a second ledger.


## 2026-11-15 — M01 replay repair: Book-owned request receipts

- Inspected PR #2 branch at `738ba4887b173bc1402283dab29ff44bd0090477` before changes, `src/founders_civ/core/ledger.py`, `src/founders_civ/experimental/worldbox_gateway_m01.py`, existing six gateway tests and world checkpoint API surface.
- Functional change: `Book.move_once(request_id, material, energy)` now stores settlement receipt and exact transfer legs in the **same authoritative Book instance**. Exact replay returns original transaction without a second resource transfer; conflicting same-ID payload raises. Rejected overdraw does not reserve a receipt.
- Gateway now uses Book-owned receipt instead of event-only duplicate detection; emits `m01_harvest` only for initial settlement. Existing duplicate-rejection test updated to idempotent-return semantics; three replay/pickle/overdraw tests added.
- Added `.github/workflows/core151-m01-tests.yml` for clean-checkout compile, authority and gateway regression tests. Checked GitHub Actions API after commit: **zero workflow runs observed**.
- Local container Git clone failed: `Could not resolve host: github.com`. GitHub API file edits succeeded. No fresh unit tests, Book audit, whole-world checkpoint test, native WorldBox test or ecological horizon simulation executed this cycle. Test changes are AUTHORED / NOT RUN.
- Important limitation: Book receipt survives Python pickle of the Book by design, but full `IntegratedWorld` checkpoint restore and durable atomic disk writes are **NOT VERIFIED**. If event logging fails after Book settlement, the Book receipt prevents duplicate transfer but event history can be missing. Native WorldBox transfer must remain disabled.
- Exact GitHub source commits: ledger `cd3ca3858b1cf9cd524c6c6a273f78c351068cac`, gateway `349d5d291f8287b7c2d2eb0551c87624a068571b`, tests `5bf74669e24e1737b3746db4c0ef022c7de5e929`, CI workflow `c14b43ae63668d3d4f429f00e758e34e11f4ea0b`.
- Decision: retain experimental, M01 iteration 3 repair locked; no canonical promotion. Next: run CI and implement/verify whole-world checkpoint with durable Book receipts.

## 2026-11-15 — M01 iteration 3 repair: atomic whole-world checkpoint source
- Baseline: main `26a02ba50a53770b14eae0368315ea01036d0b3c`; experimental branch before this cycle `79629570a345743c382cda69fcc5379c585453ed`; draft PR #2 remains open and unmerged.
- Inspected actual `src/founders_civ/core/ledger.py` Book.move_once receipt storage, `worldbox_gateway_m01.py`, `world_integration.py`, WorldTree references, pilot bootstrap and existing replay tests.
- Source change: `src/founders_engine/checkpoint.py` saves the **complete existing IntegratedWorld** with its Book receipts, clock, tree and Founder references; validates the one-Book authority before saving and after restoration; SHA-256 checks envelope bytes, validates length and uses fsync + atomic replace of a local checkpoint file. No new engine or ledger. Only trusted local pickle files may be loaded; pickle is not safe for untrusted files. This does not implement native WorldBox ACK or cross-process exactly-once delivery.
- Test source: `tests/test_checkpoint.py` has four envelope corruption/roundtrip tests and two actual-world integration tests for replay idempotency and one-step restarted vs uninterrupted Book/tick equivalence.
- **EXECUTED locally:** `PYTHONPATH=/mnt/data/cycle24 python -m unittest -v test_checkpoint.EnvelopeTests` against an equivalent local copy of the new checkpoint module => 4/4 PASS. The local container cannot resolve github.com, so **the committed GitHub checkout itself was NOT RUN**. The two actual Core151 world tests were authored but **NOT RUN** this cycle; no new Book audit, long ecology run or WorldBox gameplay test occurred.
- Known risk: whole-world object graph might not pickle cleanly; test must fail and be repaired rather than marking the iteration complete. Checkpoint files do not prove external resource provenance or crash-safe WorldBox acknowledgements.
- Decision: retain experimental, M01 iteration 3 repair blocked on executing actual whole-world tests; no canonical promotion or main writes.
- Next: run clean-checkout CI/restart integration tests; repair serialization/clock/Book alias issues and confirm no duplicate settlement after reload.
