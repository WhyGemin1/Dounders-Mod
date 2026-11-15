# M05 engineering and validation report

## Sources inspected

- User-supplied M04 package (`m04_energy.py`, `m04_worldbox_adapter.py`, 37 tests, design and README).
- User-supplied M03 source, event store, metadata-based assembly compatibility and read-only event bridge C#.
- User-supplied `Assembly-CSharp.dll`, whose SHA256 matches `assembly_compatibility.json`. Ten native method signatures were verified against its actual ECMA-335 metadata in the prior inspection, and can be reverified with `tools/verify_hooks.py`.
- The user's description of M02 snapshots: first 2,293, later 4,900, 559 common IDs; no raw M02 capture files/source were available to rerun that analysis.

## Implemented

1. M05 SQLite state with `balances`, unique `transfers`, transaction-hash-checked operations, period replay checking and a reconstructed-journal conservation audit; one serialized writer per DB.
2. World identity binding and per-session native JSONL import with exact SHA verification (when source session contains a SHA), seven expected Harmony hook labels, native integrity classification and actor counts beyond 5,000.
3. Normalized snapshot import and continuity comparison. Identical actor IDs with equal recorded species/generation/creation/parents are counted as matches; snapshot entry/exit is **not** mortality/reproduction.
4. Four-habitat Tree ecology with weighted environmental capture; source accounting for solar production, ecological maintenance, food-web provision, shared river allocation and biological reserves.
5. Distinct BIO and fictional CE assets, no automatic conversion from WorldBox nutrition. Fruit can grow only if stored matter and charge suffice, remains individual, can be harvested once and decays into explicit destination accounts if uncollected.
6. Founder body digestion/fuel, fatigue/integrity/rest, no energy-point gates, and funded Creation proposals plus virtual Tree establishment.
7. Local BepInEx 5/Harmony observer C# project, fail-closed assembly/save guard, read-only virtual HUD projection and PowerShell game-local build/install path.
8. Matched-seed synthetic sensitivity runner with eight *newly defined M05 arms*. It is not the canonical Core151 8-arm test matrix and cannot be treated as 30 actual WorldBox runs.

## Measured validation at packaging time

- `python -m unittest discover -s tests -v`: **37/37 passed** (before final packaging checks; rerun after editing).
- 6,001 synthetic native actor IDs imported without a 5,000 fixed limit.
- Synthetic 2,293 vs. 4,900 snapshot continuity yielded 559 shared, zero conflicts, 1,734 earlier-only and 4,341 later-only.
- A synthetic 360-period, two-Tree test passed journal conservation.
- An eight-arm × two-seed × 30/180 horizon smoke test returned 32 rows with balance check `True` in all rows (not population outcomes).
- A baseline single-seed 1,080-period synthetic run completed all five milestones (30/180/360/720/1080) and the Book remained balanced.
- **C# not compiled or live-tested**; no Unity/BepInEx plugin dependencies or .NET SDK available in this container. Don't claim functional native hooks, a working GUI, or actual WorldBox frame performance until your local build and runtime check.

## Ecological interpretation

`BIO` is illustrative chemical-equivalent accounting with modeled solar input and sinks; it is *not* measured native biomass. `CE` is fictional energy from a bounded river, with explicit upstream recharge. In baseline synthetic runs the model produces fruits once mature. Severe habitat-support loss can kill Trees, while drought reduces fruit supply. This is expected sensitivity from uncalibrated coefficients, not a validated ecological law. Gross fruit counts can exceed net harvested fruits because decayed CE returns to the finite shared river pool and can be used again.

## Completion status

| Work item | Status |
|---|---|
| Persistent M05 virtual BIO/CE Book | **Implemented and offline-tested** |
| Four habitats, Tree failure and shared river | **Implemented and offline-tested** |
| Replay-safe fruit harvest / virtual creation | **Implemented and offline-tested** |
| Founder digestion, fatigue and rest | **Implemented and offline-tested** |
| Native event intake / snapshot continuity | **Implemented and synthetic-tested** |
| Local observer compile and live hook attach | **Unverified — user machine required** |
| In-game HUD | **Source implemented; runtime unverified** |
| Correct real-world tile habitat production | **Not integrated — map probes/calibration missing** |
| Native fruit pickup and WorldBox world spawning | **Not implemented** |
| One Core151 authoritative physical Book | **Not integrated — actual Core151 source unavailable** |
| Native animal energy/reproduction changes | **Not implemented by design — avoid dual authority** |

## What to test first on the user machine

1. Run `doctor` and compare WorldBox SHA to supplied assembly.
2. Compile separate M05 observer, confirm seven hooks, capture native session on a copied save.
3. Audit session coverage/loss and trace several confirmed visible eating and hunting events.
4. Publish HUD and verify in-game read-only projection matches status after a virtual fruit harvest.
5. Export the native event audit and full Book audit; compare isolated behavior against the unmodded game.
6. Bring in actual Core151 and M02 source/API for a single-Book native-quantity integration phase.

## Prohibited claims

Never present source-only C# as already compiled; synthetic Tree survival as animal viability; unverified native events as calibrated calories; snapshot ID membership as birth/death rates; or a funded virtual seed as a native WorldBox created World.
