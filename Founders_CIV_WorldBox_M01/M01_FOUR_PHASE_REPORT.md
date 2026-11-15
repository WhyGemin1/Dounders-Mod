# Cycle M01: WorldBox actor identity integration — Four phases

## Engineering decision

Use the existing `WhyGemin1/worldbox-mcp` BepInEx C# bridge, rather than replacing it. The public `query_actors` command returns `name, asset_id, kingdom_id, x, y`; those fields cannot be used as persistent identity. The exact user-uploaded WorldBox `Assembly-CSharp.dll` matches the pinned bridge's WorldBox 0.51.2 fingerprint. ECMA metadata shows `Actor.data` and inherited `BaseSystemData.id`, making a read-only identifier extension plausible. **Actual runtime persistence still needs to be verified.**

## Phase 1 — Inspect and design (completed)

Inputs: actual Core151 source, WorldBox 0.51.2 static metadata and public `QueryActorsCommand.cs`, `WorldAccess.cs`, `Plugin.cs`, `HttpBridge.cs`, `server/src/worldbox_mcp/client.py`.

Found: no actor ID in current bridge query; base system data includes id and actor data includes generation, nutrition, stamina and two parent fields; bridge already supplies read permission, main-thread dispatch and authenticated loopback.

## Phase 2 — Implement a safe M01 bridge (completed in source)

- New original read-only C# `query_actor_identities` returns native ID, species, name, location, generation, parents, nutrition, stamina, creation marker, tick and seed. Requires paused world, disallows >5000, missing or duplicate IDs.
- Safe local fork patcher, with original Plugin.cs backup, refusal on drift and repeat-run idempotency.
- SQLite explicit manual linking from native ID to `WTBIO-` Core ID, separate World ID, explicit world epochs, replay-safe snapshot log, duplicate/mismatch protection.
- Python authenticated loopback client with **no** mutating commands.
- Core151 live-source initializer/shadow read: real seeded animals and eight phenotypic traits, Book shared across components.

**Unverified:** C# compiler compatibility, runtime reflection path and Native `ActorData.id` stability through save/load.

## Phase 3 — Test (completed offline; live blocked)

- All 37 local tests passed (see `VALIDATION_M01.json`).
- Tests include 20 *simulated* reload epochs, ID collisions, same-tick disagreement, name/location change stability, SQLite reopening, and real Core151 initialize/audit.
- Verified in Core151 seed 100001: 68 animals, 13 species, 100 Founders, one shared Book, zero Book rejections, eight actor traits.
- The offline end-to-end demo uses a clearly marked synthetic WorldBox fixture with IDs `11001` and `11002`, not observed game data.

**Not completed:** compiling the C# mod; running WorldBox; testing actual 20 save/reloads; confirming the query's values with a live native actor. No feeding/reproduction/death overriding in M01.

## Phase 4 — Handoff (completed)

- Reusable Python source, tests, C# extension, idempotent local patcher, end-to-end synthetic fixture, CLI and instructions.
- Release is **experimental M01**, not promotion to canonical Founders–CIV Core151.
- No game DLLs, proprietary assets, or debug symbols packaged.

## Next go/no-go gate

**GO** to M02 only if a compiled mod returns real stable actor IDs with matching history across 20 actual WorldBox save/load cycles; no duplicate native IDs; pause and world-load safety; verified Book untouched. **NO GO** if IDs are missing/reused, provenance of snapshots unclear, or C# binary does not load. Investigate and fix the bridge before ecology overrides.

## User contribution that helps most

Run the read-only command on a *disposable* WorldBox save, share redacted `live-probe`, `live_snapshot.json` and any compile/log errors. GitHub write access is optional but would remove repeated ZIP handoffs.
