# Founders–CIV × WorldBox — M01 Four-Phase Experimental Integration

**Status:** Python implementation and read-only Core151 integration verified locally; **WorldBox mod source prepared but NOT compiled, installed, or tested in-game**.

## Scope

This package creates a safe first boundary between WorldBox's existing actors and the Core151 simulated actors. It does **not** replace WorldBox hunger, breeding, death, AI, or the Book. It contains **no proprietary WorldBox binaries, game assets, or decompiled code**.

### Phase 1 — Source and API audit

- Exact supplied WorldBox main assembly SHA-256: `51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f`.
- Matched the WorldBox 0.51.2 reference recorded in the public [worldbox-mcp game API notes](https://github.com/WhyGemin1/worldbox-mcp/blob/main/docs/game-api-notes.md).
- Located actor `data`, inherited `BaseSystemData.id`, `ActorData` generation/parent/nutrition/stamina fields and the existing `QueryActorsCommand` read API.
- **Critical discovery**: `query_actors` returns no native actor ID. Names and coordinates cannot be used as durable identity.

### Phase 2 — Implement read-only integration

- `worldbox_patch/QueryActorIdentitiesCommand.cs`: new bridge command `query_actor_identities`; requires a paused, loaded World, returns all visible IDs, species and lineage; fails closed when IDs are missing/duplicated or too many actors are present.
- `apply_to_worldbox_bridge.py`: idempotently adds the original source to a **local clone** of `worldbox-mcp` and backs up `Plugin.cs`. Does not run a game or change an upstream repo.
- `founders_worldbox/registry.py`: SQLite registry for explicit WorldBox ↔ Core151 ID mappings, replay-safe snapshot journal, guarded world epochs, mismatch checks, lineage observations. **No automatic fuzzy enrollment.**
- `founders_worldbox/client.py`: authenticated loopback *read-only* WorldBox bridge client; refuses nonlocal endpoints and mutation commands.
- `founders_worldbox/core151_adapter.py`: uses **actual Core151 Python source** to export initial 68 animals, 13 species, eight numeric traits each, and 100 Founders; confirms shared Book. Shadow comparison never changes physical state.

### Phase 3 — Tests

- **37/37 local Python tests pass**, including one integration test with actual Core151, missing/duplicate ID rejection, same-tick conflict, seed mismatch, name/position changes, replay-safe observation, 20 **simulated** save/load epochs, local-only connection, and C# patch installer idempotence.
- A separate end-to-end offline demo successfully maps a **synthetic** WorldBox rabbit ID to a real Core151 burrow-rabbit ID. This is NOT a live game test.
- Actual WorldBox 20-cycle save/load testing is **pending user PC setup**. New C# source was **not compiled** in this environment (no dotnet SDK) and no WorldBox process was run.

### Phase 4 — Packaging and handoff

- Full source, test suite, an illustrative synthetic fixture, CLI, original C# extension, safety instructions and acceptance gates are included.
- No canonical Core151 engine changes and no gameplay edits.
- Require build, live ID verification and 20 live save/load cycles before promoting M01.

## Quick offline verification

From this directory:

```bash
python -m unittest discover -s tests -v
python m01.py --db demo.sqlite init-world --world-id WORLD-001 --seed 9711
python m01.py --db demo.sqlite enroll --world-id WORLD-001 --native-id 11001 --core-id WTBIO-0000041 --asset rabbit --species burrow_rabbit --generation 0
python m01.py --db demo.sqlite observe --world-id WORLD-001 --snapshot fixtures/SYNTHETIC_paused_snapshot.json
```

To export **real Core151** (requires a separately extracted Core151 package):

```bash
python m01.py export-core --core-source /path/to/Founders_CIV_CoreCompletion151/source --output core151_reference.json
python m01.py --db demo.sqlite shadow --world-id WORLD-001 --core-state-json core151_reference.json
```

**All IDs and WorldBox snapshots in `fixtures/` are synthetic and clearly marked; they do not come from a running WorldBox instance.**

## Local WorldBox integration

See `USER_HELP_START_HERE.md` and `worldbox_patch/INTEGRATION.md`. Briefly: clone your *own* WorldBox bridge fork, run the patch installer, build with pinned `.NET SDK`, test the C# mod, deploy to a disposable WorldBox 0.51.2 installation, pause the world, query identities, and provide a redacted health/snapshot report.

**Never share or commit:** WorldBox DLLs/PDBs/decompiled source, config secrets/token, Steam credentials, private saves or other people's unlicensed assets.

## Critical M01 limits

- World ID is currently registered **outside** WorldBox; the native seed is a compatibility guard **not** a unique world identity across game generation. A persistent save identity handshake is required in M02.
- Core151 snapshot exporter creates a **fresh seed-based initial state**, not an ongoing or live Core151 checkpoint. Use a trusted exported JSON state to compare existing actor IDs later.
- Not a WorldBox save/load verification, not a validated mating/feeding patch, and not a second authoritative economy.
- Simulated 20-epoch tests exercise our registry only; they do not prove `ActorData.id` survives WorldBox load or an actor's live lineage remains unchanged.
- Existing bridge and C# runtime behavior can only be validated with the user's running WorldBox installation.
