# Dounders-Mod — repository navigation and source status

Repository audit: 2026-11-15. Baseline: `main` commit `26a02ba50a53770b14eae0368315ea01036d0b3c` (147 tree entries, not all source files). The statuses below are inferred from inspected files and manifests; no fresh compilation, game launch, or 30–1080-day run was performed during this audit.

## Existing primary source locations (do not move automatically)

| Existing path | Type / purpose | Verification boundary |
|---|---|---|
| `FoundersCIV_WorldBox_M05_Integration/` | Python `m05_core.py`, `m05.py`, C# `bridge/FoundersCIV_M05_Observer.cs`, build script, documentation and tests | `MANIFEST.json` describes offline Python testing; marks C# compilation and live WorldBox tests false, and Core151 Book integration incomplete. README discusses later focused build repair; verify current build separately. |
| `Founders_CIV_WorldBox_M01/` | Python WorldBox identity bridge, C# query patch, registry, adapters, tests and snapshot examples | Its README says Python/read-only bridge tested offline; WorldBox patch not verified in-game. This is **not** the same lineage as the later experimental M01 Book resource gateway discussed in hourly cycles. |
| `M05_052_Repair/`, `M05_BepInEx_Diagnostic_Repair/`, `payload/`, `Repair-M05.ps1` | Source and scripts for diagnostic/compilation repair | Treat as patch candidates; inspect content and hashes before applying. |
| `Founders_CIV_Core151_Physiology_PredatorPrey_Experimental.zip` | Earlier Core151 experimental engine source archive | Archive is not an independently buildable source tree on GitHub until extracted/validated into version-controlled source. |
| `Founders_CIV_INTEGRATION_025_Compatibility_Release(4).zip`, `Founders_CIV_WORLD_024_100_Stress_Release*.zip`, `Founders_CIV_U026_Blueprint_Package.zip` | Historical integration/world/blueprint archives | Historical, not proven current canonical executable sources. |
| `Founders_CIV_v018_*`, `Founders_CIV_v019_*`, `Founders_CIV_v016_*` | Historical design documents and archives | Preserve until provenance and promotion status are verified. |
| `OBSERVED_DEPENDENCIES.json`, `PATCH_MANIFEST.json` | Root diagnostic/repair metadata | Keep tied to exact repair version and source fingerprints. |

## Repository hazards observed in main

- Both M05 and M01 trees contain tracked `__pycache__/` and `*.pyc`; M05 contains tracked `bridge/obj/` and `build/refs/*.dll`.
- M05 contains `data/house.sqlite`, `local_world.json` and a .bak file; M01 contains JSON snapshots and `validation/demo.sqlite`. Treat as recorded test/runtime state, not immutable canonical data, until provenance and privacy review.
- `Founders_CIV_WORLD_024_100_Stress_Release 2.zip` and `Founders_CIV_WORLD_024_100_Stress_Release(1).zip` have identical Git blob SHA (`ab8fece1d61b104352f96bac7c8528715aa0dd83`); similarly named 0.18 canon archives share a SHA. Do not remove duplicates without an explicit reviewed change.
- GitHub repository visibility is **public**. Before importing save files, private logs, game binaries, or licensing-restricted artifacts, review privacy and redistribution rights. Do not commit secrets.

## Suggested target layout (NOT YET MIGRATED)

```text
src/core/                 # One authoritative Python Founders–CIV simulation (after audited import)
src/worldbox_bridge/      # C# sources + verified protocol adapter
tests/core/ tests/bridge/ tests/integration/
experiments/M01/          # Review-only patches and reproducible manifests
data/examples/            # Sanitized fixtures only
docs/architecture/ docs/provenance/ docs/development/
archive/                  # Curated immutable historical releases
.github/workflows/        # CI after dependency verification
```

These are *proposed* destinations. Current modules should continue resolving at their original paths until migration PRs prove imports, builds, tests, Book authority, and checkpoint compatibility. Do not bulk move binaries or erase history.

## Gate to canonical source

A source candidate must have: known commit+SHA provenance; reviewed mainline dependency interface; demonstrated one authoritative Book ledger and clock; deterministic seed/checkpoint regression; a runnable test command with captured exit status; and, for game claims, actual WorldBox build and in-game evidence. `MANIFEST.json` historical pass counts are not new CI results.

See [DATA_CATALOG.md](DATA_CATALOG.md), [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md), and [cycle_state.json](cycle_state.json).
