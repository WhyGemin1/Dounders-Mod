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
