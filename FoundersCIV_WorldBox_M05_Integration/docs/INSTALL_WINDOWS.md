# M05 Windows implementation guide — step by step

> **Scope:** install a read-only WorldBox observer and a separate persistent M05 energy simulator. The optional HUD displays *virtual* Tree and fruit stocks. This package does not spawn native fruit or change native game physiology. You need your own installed WorldBox, functioning BepInEx 5 Unity Mono environment and .NET SDK to build the plugin. The C# observer is source-only because this environment has no .NET compiler or installed game/plugin references.

## Phase 0 — backups and prerequisites

1. **Exit WorldBox completely.** Back up the save you want to experiment on through the game/Steam save location you use. Back up the existing `WorldBox/BepInEx` folder or at least its `plugins` and `config` subfolders. Keep a pristine backup save and a copied experimental save.
2. On your computer install or confirm **Python 3.10+** (`py --version`) and **.NET SDK** (`dotnet --version`). A compatible existing BepInEx 5 + Harmony 2 installation is required. If M01 was already working, retain it rather than installing another loader.
3. In Steam, open WorldBox > Manage > **Browse local files**. Copy its actual folder path. Set this in PowerShell (replace the sample):

   ```powershell
   $game = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox'
   ```

4. Extract `FoundersCIV_WorldBox_M05_Integration.zip` into `C:\Dev\FoundersCIV_WorldBox_M05_Integration`. In PowerShell:

   ```powershell
   cd C:\Dev\FoundersCIV_WorldBox_M05_Integration
   py --version
   dotnet --version
   py -m unittest discover -s tests -v
   py m05.py doctor --game "$game"
   ```

5. **Stop if doctor reports a missing library or `MISMATCH_FAIL_CLOSED`.** The observer expects exactly the uploaded game's `Assembly-CSharp.dll` SHA256 `51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f`. A later WorldBox update may have different signatures. **Never replace your current WorldBox game assembly with the uploaded one** to make this pass. Instead, update and revalidate the observer source against the installed version.

## Phase 1 — bind the real world and initialize virtual Trees

6. Choose one **stable, unique save-world identifier** for the copied save, for example `house-save-2026-11-13-test1`. The name is not a password. Preserve it across play sessions of that same save, and never reuse it for a different save. Each independently cloned scenario should have its own key and SQLite file.
7. Make an editable configuration and replace `example-HOUSE-SAVE-001` with your unique identifier. Edit the Forest/Grassland/Wetland/Ridge habitat coefficients, Tree ID and `anchor` coordinates based on your own scenario planning. Until real map probes exist, these are **hypothetical manual conditions**; the anchor is metadata, not native terrain binding.

   ```powershell
   Copy-Item .\examples\world.json .\local_world.json
   notepad .\local_world.json
   ```

8. Set up the virtual sidecar Book. It will not change your WorldBox save:

   ```powershell
   py m05.py --db data\house.sqlite setup --config local_world.json
   py m05.py --db data\house.sqlite status
   py m05.py --db data\house.sqlite audit
   ```

9. Bind the observer to the **exact same world key**. Replace the value below with the value in `local_world.json`. This writes only M05's text identity file:

   ```powershell
   New-Item -ItemType Directory -Force "$game\BepInEx\FoundersCIV_M05" | Out-Null
   Set-Content -Path "$game\BepInEx\FoundersCIV_M05\world_key.txt" -Value 'house-save-2026-11-13-test1' -NoNewline
   ```

   If you later change to another save, use **a new world key and new database**, and update this file before launching.

## Phase 2 — compile and install the native observer

10. Find and move any standalone **M03 event observer** DLL out of `BepInEx/plugins` (leave your existing M01/M02 bridge in place). Do not load M03 and M05 observers at once; both could duplicate callbacks. Do not delete your older working files: move the observer into a backup folder **outside** `BepInEx/plugins`.
11. Compile M05 using the game's installed BepInEx/Harmony/Unity libraries. Build only first:

    ```powershell
    .\build_bridge.ps1 -GameDir "$game"
    ```

    This may download the .NET Framework 4.6.2 reference package through NuGet during restore. If the build fails, see troubleshooting. It does not install a DLL when build fails.
12. Install the compiled observer only after build succeeds:

    ```powershell
    .\build_bridge.ps1 -GameDir "$game" -Install
    ```

    This installs only `BepInEx/plugins/FoundersCIV_M05_Observer.dll`. It backs up an existing M05 DLL if updating. Do not put Python files in BepInEx plugins.

## Phase 3 — first real WorldBox capture and audit

13. Launch WorldBox and load the **copied** experimental save. Check BepInEx logs for `M05 event observer started` and a count of **7 active hook targets**. If there are zero hooks, the observer has refused to attach (unbound save identity, assembly mismatch or reflection error). Do not proceed with native analysis until fixed.
14. With the game running, observe a few actual animals for a short interval including some feeding, predation or reproduction if those naturally occur. **Do not infer that every `baby_factory_call` was a birth or every `kill_callback` was prey killed**. Close WorldBox normally to flush `session_close`.
15. Import the emitted event files (this is read-only; no BIO is written from native data):

    ```powershell
    Get-ChildItem "$game\BepInEx\FoundersCIV_M05\m05_*.jsonl" | ForEach-Object {
        py m05.py --db data\house.sqlite ingest-events "$($_.FullName)"
    }
    py m05.py --db data\house.sqlite native-audit --output results\native_audit.json
    py m05.py --db data\house.sqlite audit --output results\ledger_audit.json
    ```

    A clean capture should have `native_capture_integrity_ok: true`, every session opened/closed, all seven hook labels, the expected native assembly SHA, no sequence gaps and no dropped events. Missing hooks, incomplete tails or other issues mean **capture is not acceptable for promotion**. Run the importer again after graceful shutdown for any files written while the game was still running.

## Phase 4 — run and inspect M05 living-energy scenarios

16. Advance the **virtual** World Tree separately from WorldBox. Each period is an ordinal observation interval, **not** a game tick and not an action allowance. The values are experimental scenario parameters:

    ```powershell
    py m05.py --db data\house.sqlite cycle --period 1 --river-supply 90
    py m05.py --db data\house.sqlite cycle --period 2 --river-supply 90
    py m05.py --db data\house.sqlite status --output results\virtual_status.json
    py m05.py --db data\house.sqlite audit --output results\ledger_audit.json
    ```

17. Optional environmental stress example (scenario, **not** measured WorldBox weather):

    ```powershell
    py m05.py --db data\house.sqlite cycle --period 3 --river-supply 20 --conditions examples\conditions_dry.json
    ```

    Every period must increase by exactly one. A repeated command with identical input returns the same result and does not spend again. A repeated period with changed inputs fails; use a different backed-up experiment database for alternate scenarios.
18. If you want a read-only HUD in WorldBox, after ensuring the saved world and M05 `world_key` match, publish the virtual projection:

    ```powershell
    py m05.py --db data\house.sqlite publish-overlay --game "$game"
    ```

    Reopen WorldBox on that save. The HUD says `VIRTUAL / READ ONLY` and displays model Tree health, CE river stock and fruit count. It is **not a native WorldBox tree or pickup inventory**.

## Phase 5 — virtual harvest, Founder recovery and Creation

19. To find fruits after enough virtual cycles (the default Tree matures at period 12), use:

    ```powershell
    py m05.py --db data\house.sqlite status
    ```

    For individual fruit IDs, use the included read-only helper:

    ```powershell
    py tools\list_fruit.py --db data\house.sqlite
    ```

    Each fruit has an immutable ID such as `WORLD-TREE-001-F0000001`.
20. Harvest one *virtual* fruit for a registered Founder. Replace the ID with an actually available one:

    ```powershell
    py m05.py --db data\house.sqlite harvest --fruit WORLD-TREE-001-F0000001 --founder Solace --operation harvest-fruit-001
    ```

    The fruit can be harvested once. Repeating the identical operation is safe; changing the recipient or transaction identity cannot duplicate it.
21. Observe *virtual* digestion and restoration. Feeding here explicitly transfers from the virtual Tree's food-web resource pool, **not from WorldBox's animal nutrition**:

    ```powershell
    py m05.py --db data\house.sqlite feed-virtual --founder Solace --tree WORLD-TREE-001 --amount 2 --event feed-001
    py m05.py --db data\house.sqlite body-cycle --founder Solace --cycle body-001 --rest 1.0 --workload 0.0
    ```

    Rest may reduce fatigue but does not create chemical fuel. No action request is gated by a time or energy-point balance.
22. A Founder can submit a Creation design even with zero charge. If enough virtual fruit substrate has been harvested, the `create` command funds a **virtual** seed; otherwise it records an unfunded design:

    ```powershell
    py m05.py --db data\house.sqlite create --founder Solace --kind world_seed --attempt attempt-001
    ```

    A successfully funded world seed can establish another **virtual** Tree with four habitats:

    ```powershell
    py m05.py --db data\house.sqlite establish-tree --id WORLD-TREE-002 --attempt attempt-001 --config local_tree_002.json
    ```

    **Important:** `establish-tree --config` needs a single Tree configuration (the nested `config` object), not the whole world setup JSON. Copy `examples\tree_config_for_new_world.json` to `local_tree_002.json`, update its anchor and values, and use the edited file. The Tree is marked `virtual_pending`; no game map or new WorldBox World is spawned.
23. For independent matched-seed synthetic comparisons, use a fresh folder:

    ```powershell
    py tools\run_batches.py --output-dir results\batch-001 --seeds 30 --horizons 30,180,360,720,1080
    ```

    This eight-arm full batch can take substantial time and disk space. Start with `--seeds 2 --horizons 30,180` to validate your environment. Batch runs are **synthetic ecological sensitivity checks**, not verified outcomes from 30 real WorldBox game runs.

## Phase 6 — optional M02 snapshot continuity

24. Normalize each existing snapshot to `founders-native-snapshot-1` format described in `docs/SNAPSHOT_FORMAT.md`. The actual M02 source or raw snapshots were not supplied here, so an automatic converter cannot safely assume M02 field names. Import only verified mappings:

    ```powershell
    py m05.py --db data\house.sqlite import-snapshot local_snapshot_before.json
    py m05.py --db data\house.sqlite import-snapshot local_snapshot_after.json
    py m05.py --db data\house.sqlite compare-snapshots before after --output results\continuity.json
    ```

    Membership changes are not deaths or births; the later capture's lower WorldBox tick does not establish lifetime ordering.

## Phase 7 — acceptance, export, rollback

25. Confirm `book_balanced: true` and inspect `native_capture_integrity_ok` independently. Native capture integrity can fail while the virtual ledger remains balanced; neither is proof of ecology stability.
26. If you have the real Core151 source package, produce a **review-only** transaction export:

    ```powershell
    py m05.py --db data\house.sqlite export-core151-review --output results\core151_review.json
    ```

    **Do not automatically replay this file into a running Core151 Book.** Core151 needs an idempotent adapter, asset and authority mapping, atomic commit, ownership reconciliation, migration markers and regression tests; see `docs/CORE151_ADAPTER_CONTRACT.md`.
27. **Rollback:** exit WorldBox, move `BepInEx/plugins/FoundersCIV_M05_Observer.dll` out of plugins, optionally restore your backed-up M03 observer, restore the original save, and retain or restore your `.sqlite` database backup. M05 does not edit the game's managed DLLs or native animal energy; removing its plugin and virtual database should restore the previous game behavior subject to other installed mods.

### Troubleshooting

| Symptom | Action |
|---|---|
| Doctor reports assembly mismatch | Stop. WorldBox build differs; do not copy an older DLL over it. Revalidate and rebuild the observer for the installed version. |
| No `BepInEx.dll` / `0Harmony.dll` | Confirm your BepInEx 5 Mono install; don't mix with a separate game loader without testing. |
| `dotnet` not recognized | Install a current .NET SDK and open a new PowerShell session. |
| NuGet / .NET reference assembly restore error | Confirm network and .NET Framework 4.6.2 reference assemblies; build must succeed before installation. |
| Plugin loads with zero hooks | Check `world_key.txt`, native DLL SHA, BepInEx logs and game version. Observer fails closed by design. |
| Observer event JSONL has gaps/`bridge_loss` | Do not promote event claims. Reduce capture duration/volume and inspect IO and plugin performance. |
| No HUD | Publish projection; confirm matching world key, compiled plugin, and game reload; HUD is a virtual view. |
| `period must be exactly ...` | Do not use game tick or skip an M05 ordinal. Reuse previous command only with identical inputs. |
| Tree produces no fruit | Inspect maturation, biomass capture, maintenance, habitat support, shared river CE and reserve floors. |
| Native actor nutrition didn't change after `feed-virtual` | Expected. Native animals remain WorldBox-controlled. |
| `funded_seed_awaiting_native_execution` | Funding is modeled; a real WorldBox creation interface still has to be built and validated. |

## Stop/go decision

**GO for:** offline energy research, durable virtual economy, read-only native event observation after local build, optional HUD, data continuity comparisons.  
**NO-GO for:** switching off WorldBox native nutrition, mirroring its food events into BIO, native fruit spawning, automatic terrain/world creation, claims of Core151 physical-ledger consolidation, or any live gameplay claim without runtime evidence.
