# Founders–CIV repository data catalog

Audit origin: `main` at `26a02ba50a53770b14eae0368315ea01036d0b3c`, 2026-11-15. This catalog uses the repository tree and inspected source documentation. **Inventory does not imply validation or ownership of every upstream game asset.**

| Data class | Representative existing paths | Classification and policy |
|---|---|---|
| Python/C# source | `FoundersCIV_WorldBox_M05_Integration/m05_core.py`; `bridge/FoundersCIV_M05_Observer.cs`; `Founders_CIV_WorldBox_M01/founders_worldbox/*.py` | Review active dependencies before any migration; preserve tests and file history. |
| Configuration and contracts | `FoundersCIV_WorldBox_M05_Integration/MANIFEST.json`, `assembly_compatibility.json`, `docs/CORE151_ADAPTER_CONTRACT.md` | Historical evidence, not proof of current runtime compatibility. |
| Synthetic fixtures | `FoundersCIV_WorldBox_M05_Integration/examples/*.json*`, `Founders_CIV_WorldBox_M01/fixtures/` | Retain only documented synthetic and non-sensitive test data. |
| Test reports | `FoundersCIV_WorldBox_M05_Integration/reports/`, `Founders_CIV_WorldBox_M01/validation/test_results.log` | Preserve original provenance, commands, seeds and result semantics; do not call synthetic baselines real WorldBox results. |
| Runtime/saves | `FoundersCIV_WorldBox_M05_Integration/data/house.sqlite`, `local_world.json`, `Founders_CIV_WorldBox_M01/after_reload.json` | Quarantine from new commits until privacy, identity, size and determinism are audited. No automatic removal of already tracked files. |
| Build outputs | `FoundersCIV_WorldBox_M05_Integration/build/refs/*.dll`, `bridge/obj/`, `__pycache__/` | Existing tracked generated artifacts; preserve until dependency licensing and reproducible builds are independently verified. New generated files should normally be ignored. |
| Historical archives | Root `Founders_CIV_*.zip`, `FoundersCIV_WorldBox_M05_v0.5.3_REPAIR.zip` | Preserve for provenance; indexed source extraction and deduplication require separate PR and build/test gates. |
| Mod repair scripts | `Repair-M05.ps1`, `M05_052_Repair/`, `payload/` | Do not run or merge without reviewing paths, backup semantics, game version compatibility and user environment. |

## Provenance requirements for every imported artifact

Record `source_uri`, `source_sha256`, `repository_commit`, `original_path`, `license_or_permission_status`, `date_verified`, `classification` (source/fixture/report/binary/archive), and `validation_status` (verified/provisional/unapplied/not-run). Unknowns stay explicit, never inferred.

For experiment outputs also record source SHA, baseline and candidate arms, seed IDs, horizon, population initial conditions, habitat configuration, exact command, exit code, Book audit, first failed ecological gate, checkpoint file hash, and whether results were obtained in a headless simulation or real WorldBox session.

## First migration batch recommendation

1. Audit existing tracked generated artifacts and data for redistribution/privacy risk without deleting them.
2. Pin a known, runnable Core151 / Cycle152 extracted source snapshot to a new experimental branch, with SHA-256 manifest and a minimum reproducible test.
3. Preserve M05 and M01 old source roots until imports are mechanically verified.
4. Link the later M01 gateway Cycle1–23 patches with their actual bytes and hashes. Prior hourly summaries alone are insufficient and they must not be advertised as already in this repository.
5. Only then propose scoped moves/deduplication/CI. A catalog or plan is not functioning engine integration.
