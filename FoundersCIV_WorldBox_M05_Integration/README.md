# Founders–CIV × WorldBox M05 — Living Energy Integration (Release Candidate)

**Release status: implemented offline Python sidecar + source-only BepInEx observer and optional in-game HUD. The C# bridge has NOT been compiled or run inside the user's WorldBox installation. Core151's actual source/API, M01/M02 bridge source, real map anchors, and confirmed native feeding-energy quantities are not available in this package. This is NOT a fully proven shared gameplay integration.**

**Start with [docs/INSTALL_WINDOWS.md](docs/INSTALL_WINDOWS.md).** It covers backups, preflight checks, Python setup, local C# build, native event import, HUD projection, creation experiments, rollback and safety gates.

## What actually changed from M04

| Feature | M04 | M05 |
|---|---|---|
| Book lifecycle | In-memory, synthetic | Durable SQLite single-writer virtual Book with atomic transfers, journal reconstruction and replay checking |
| World Trees | One normalized synthetic condition | Explicit four habitats, site anchors, per-habitat conditions and Tree failure |
| Shared river | Single balance | Deterministic fair sharing between any number of virtual Trees |
| Fruits | Produce and harvest | Plus unique fruit ownership, unharvested decay and resource recycling |
| Founder body | Gut/fuel/fatigue/integrity | Persisted physiology cycles, nutrition/recovery accounting and replay checks |
| Creation | Reserved synthetic substrate | Persistent funded design/seed state and virtual Tree establishment; **not** native WorldBox creation |
| Native observation | Separate M03 importer | M05 WorldBox C# listener + native read-only event intake + session/assembly checks |
| Native population | M02 results referenced but raw absent | Large normalized snapshot ingest and continuity comparison; **does not infer births/deaths** |
| Visualization | CLI only | Optional read-only WorldBox HUD projection (requires compiling plugin) |
| Testing | 37 M04 offline tests | 37 M05 offline tests; 8-arm ×2-seed smoke; baseline 1080 observation periods |

## Model contract

- **WorldBox owns** native animals, feeding, kills, reproduction, map and native game clock.
- **M05 virtual Book owns** only `bio_equiv` (BIO) and `creation_charge` (CE) for experimental Founder/Tree systems. **M05 is not yet the authoritative Core151 Book**; it is not allowed to write into Core151 or native actor energy. Use the included `export-core151-review` as a review artifact, not automatic dual-write.
- **Founders choose actions freely.** No action-point meter, cooldown time budget, or automatic energy deduction for each decision. Workload affects metabolism and fatigue *after observation*, not action selection.
- **Eating** transfers actual verified virtual food into a virtual gut, then digestion assimilates BIO into virtual fuel. Rest reduces fatigue, while metabolism continues; rest does not create BIO.
- **World Tree fruit** needs excess modeled biomass and fictional shared river charge, while maintenance and food-web obligations take priority. CE and BIO never convert into each other.
- **Creation** stores resources in an identified seed account and changes a virtual Creation state. It does **not** instantiate a WorldBox world, terrain, native fruit, or actor yet.
- **Time** is a measurement and period coordinate, never a currency. Don't map WorldBox tick (which can reset after reload) into an M05 lifetime clock.
- **Snapshot actors and event callbacks** remain evidence, not automatic metabolic transfers or proof of births/deaths. Default habitat values are uncalibrated scenario parameters, not measurements of a WorldBox tile region.

## Files

- `m05_core.py` — persistent ledger + four-habitat ecology + fruit lifecycle + Founder body + Creation + native observation + snapshot continuity.
- `m05.py` — CLI for init, setup, cycles, harvest, creation, import, auditing, report and projection.
- `bridge/FoundersCIV_M05_Observer.cs` — read-only BepInEx/Harmony hooks and WorldBox overlay; never modifies native animals.
- `bridge/FoundersCIV_M05_Observer.csproj`, `build_bridge.ps1` — game-local C# build and installation guard; does not overwrite M01/M02.
- `tools/verify_hooks.py`, `tools/inspect_assembly.py`, `assembly_compatibility.json` — independent actual WorldBox DLL metadata checks.
- `tools/run_batches.py` — optional 8-arm ×30 matched-seed synthetic scenario harness, horizons 30/180/360/720/1080. Do not confuse it with native WorldBox outcome testing.
- `tests/test_m05.py` — offline validations.
- `examples/world.json` — *hypothetical* example Tree and founders; replace identity, anchor and habitat inputs before use.
- `examples/conditions_dry.json` — example scenario shock.
- `docs/INSTALL_WINDOWS.md` — step-by-step guide and troubleshooting.
- `docs/ENGINEERING_REPORT.md` — exact implementation, limitations, evidence gates and integration plan.
- `docs/SNAPSHOT_FORMAT.md` — normalized input format for M01/M02 snapshot data, not an assumed M02-specific format.
- `docs/CORE151_ADAPTER_CONTRACT.md` — handoff requirements for the real authoritative Book.

## Offline smoke test (no WorldBox required)

From an extracted folder:

```powershell
py -m unittest discover -s tests -v
py m05.py --db data\demo.sqlite setup --config examples\world.json
py m05.py --db data\demo.sqlite cycle --period 1 --river-supply 90
py m05.py --db data\demo.sqlite status
py m05.py --db data\demo.sqlite audit
```

The demo's `world_key` **must never be reused as the identifier for a different real game save**. Use a separate database for each save and make a backup before changing it.

## Experimental model status

All physiological coefficients, tree production parameters, energy units and creation costs are hypotheses. Solar BIO is modeled as an external input; fictional CE is explicitly drawn from a shared river source. Stress tests check software properties and directional sensitivity, **not** animal viability or accurate photosynthesis. The 1,080-period baseline produces 1,080 *gross* fruits because expired unharvested CE is returned to the shared river and reused; this is not evidence of 1,080 permanent energy harvests.

## Sources

- M03 prototype supplied with this project (actual WorldBox assembly signature inventory and draft observer).
- M04 Living Energy Prototype supplied with this project (embodied energy, fruit/river split, in-memory logic).
- WorldBox's BepInEx mod bridge project and loader context: <https://github.com/fullya99/worldbox-mcp> and <https://github.com/bepinex/bepinex>.
- Scientific baseline for food-web energy flow: OpenStax Biology 2e, <https://openstax.org/books/biology-2e/pages/46-2-energy-flow-through-ecosystems>.

No game DLLs, game assets, user saves, or secret bridge tokens are bundled in this release.
