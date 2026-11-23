# Single-engine authority — Core151 + M01

**Status:** Experimental boundary tested headlessly with recovered Core151/Cycle152 code and M01 Cycle14 overlay. Not yet merged to main; no in-game WorldBox test.

## Authoritative engine

Use `founders_civ.experimental.world_integration.IntegratedWorld` from the recovered Core151/Cycle152 source as the **single running simulation**. Its `world.book` is the only writable resource Book; `world.tick` is the only simulation clock. One registry holds 100 Founder identities and the real World Tree records.

The M01 `WorldBoxGatewayM01` only moves *existing* material and chemical-energy stock within that same Book. No external WorldBox material is credited without a source-identity/ACK protocol. `SingleEngineSession` enforces the shared Book/clock identity and exposes `step`, `harvest` and `audit`. The M05 independent SQLite virtual ledger **must not** run as another resource authority. Until migrated into the canonical Book, M05 may only supply read-only observations with explicit source provenance.

## Current source dependency and exact reproduction

The repo currently contains prior source archives, but does **not** yet contain the consolidated Core151 Python source tree as Git-tracked text in the required package layout. This integration file is therefore **not independently runnable from a clean Git checkout**. Follow-up integration must import that tree with provenance and verify tests. Do not silently fall back to M05's virtual Book.

For local validation in this cycle, unpack the actual `Founders_CIV_Cycle152_SparseFounding_Experimental.zip` (SHA256 must be independently verified) and place the later Cycle14 M01 overlay modules into its `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/experimental/`. Then run:

```shell
PYTHONPATH=src:<Core151-unpacked>/Founders_CIV_CoreCompletion151/source/world023024 python -m unittest discover -v -s tests -p test_authority.py
```

On 2026-11-15, this targeted integration suite passed 6/6 against the actual local recovered engine. It verified 100 Founders, one Book, monotonic clock, failure to add a shadow Book/clock, and rejection of an invalid harvest without changing Book sequence. This is a HEADLESS local test, not GitHub CI or WorldBox gameplay evidence.

## Promotion blockers

Import the validated single engine and its real dependencies into this repository. Preserve game-side read-only adapter separately; no independent Book. Run all regression tests and checkpoint/restart conservation gates. Add WorldBox-specific integration only when native IDs, units, game version, and exactly-once transaction protocol are independently verified. Do not delete old historical engines until all clients are migrated and tests pass.

**Next iteration:** import Core151/Cycle152 runtime source as text into `src/founders_civ/`, use compatibility shims for old paths, and make this integration test executable in CI without any ZIP extraction or machine-specific paths.
