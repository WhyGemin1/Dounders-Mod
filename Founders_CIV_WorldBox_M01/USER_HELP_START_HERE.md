# What you can do to speed Founders–CIV × WorldBox development

## Highest-value task: build and run the read-only M01 probe on your PC

The game files alone cannot tell us whether `ActorData.id` survives save/reload or whether the new command compiles against the installed plugin. A live probe is the current acceptance gate.

1. Make a **backup** of your WorldBox saves; use a disposable test world, not a valued existing world.
2. Confirm the WorldBox build/assembly matches the 0.51.2 fingerprint in `README.md` (we already matched the uploaded assembly). Keep automatic updates disabled for the test installation if possible.
3. Use the **BepInEx 5** `worldbox-mcp` fork already in GitHub; this specific bridge is BepInEx, not NeoModLoader. Its documented `docs/development.md` calls for `.NET SDK 8` and the existing pinned packages.
4. Clone your fork into a directory, for example `C:\Dev\worldbox-mcp`:
   ```powershell
   git clone https://github.com/WhyGemin1/worldbox-mcp.git C:\Dev\worldbox-mcp
   ```
5. From the extracted M01 package directory, apply the read-only patch to the **local clone**:
   ```powershell
   py apply_to_worldbox_bridge.py C:\Dev\worldbox-mcp
   ```
6. Build and test the local C# bridge:
   ```powershell
   cd C:\Dev\worldbox-mcp
   dotnet restore mod\WorldBoxBridge.sln --locked-mode
   dotnet build mod\WorldBoxBridge.sln --configuration Release -warnaserror
   dotnet test mod\WorldBoxBridge.sln
   ```
7. Follow the fork's existing `docs/development.md` for **local test deployment** into BepInEx. Start WorldBox, create a small temporary world with a few animals, and **pause it**.
8. Set `WORLDBOX_MCP_TOKEN` **locally** from `BepInEx/config/WorldBoxBridge.cfg`. Do not paste that token in chat, a screenshot or GitHub.
9. From the M01 directory run:
   ```powershell
   py m01.py live-probe
   py m01.py live-snapshot --output live_snapshot.json
   ```
10. Make a copy of `live_snapshot.json` and redact any personal values. Keep the original locally. Send the **sanitized** snapshot, the game build/fingerprint, and any build errors or redacted `BepInEx/LogOutput.log` if help is needed.

If a command fails, that is valuable. Send the exact sanitized error and build log; **do not work around missing native IDs by using names or coordinates**.

## Second high-value task: 20 real save/load checks

After the ID query successfully runs, choose two specific living animals in a disposable world. Record their `native_actor_id`, `generation`, and `parent_id_*`. Save WorldBox and reload the same world, then pause and query again. Repeat 20 times, preserving the observed ID and lineage before/after each reload. Changing tile locations or names should NOT change identity. This is a **manual live validation**, not the 20 simulated epochs in this package.

You can send a small CSV with `trial, worldbox_actor_id_before, after, generation_before, after, parents_before, after, match` and no private account details.

## Third task: authorize GitHub publishing (optional)

The connected GitHub repository is readable, but a previous branch-create and documentation commit were rejected with HTTP `403 Resource not accessible by integration`. Check the GitHub App installation under GitHub Settings → Applications → Installed GitHub Apps, grant the connector access to your fork and write permissions for **Contents** as supported, or commit the M01 package manually to a branch in your fork. The assistant cannot override permissions or silently promote into upstream. Keep proprietary DLLs and debug symbols **out of GitHub**.

## You do not need to provide

- Your Steam executable/game license, the entire WorldBox assets directory, or another copy of the assemblies already uploaded.
- Authentication tokens, Steam login, passwords or private GitHub keys.
- More conceptual design documents before we verify actor identity.

## After M01 passes

M02 should implement **shadow physiology traces** and then one isolated, Book-authorized feeding transaction on a managed rabbit. Only after idempotency, save synchronization and exact conservation checks pass should we enable hunting, breeding, deaths or Founder interventions in WorldBox.
