# Apply the original read-only command to the existing WorldBox MCP fork

1. Copy `QueryActorIdentitiesCommand.cs` into `mod/src/WorldBoxBridge/Commands/Read/`.
2. In `mod/src/WorldBoxBridge/Plugin.cs`, locate `registry.Register(new QueryActorsCommand(worldAccess));` and append one line:
   ```csharp
   registry.Register(new QueryActorIdentitiesCommand(worldAccess));
   ```
3. Existing `using WorldBoxBridge.Commands.Read;` already covers the new class.
4. Rebuild with the pinned SDK/packages from `docs/development.md`:
   ```powershell
   dotnet restore mod/WorldBoxBridge.sln --locked-mode
   dotnet build mod/WorldBoxBridge.sln --configuration Release -warnaserror
   cd mod
   dotnet test
   ```
5. Deploy via the documented script to your own WorldBox 0.51.2 test installation. Back up the save first.
6. In game, pause, then test `query_actor_identities` using the companion Python CLI.

## Scope / caveats
- Original source file, **not compiled or live-tested here** (no .NET SDK or WorldBox executable).
- Existing `query_actors` does **not** contain actor IDs and must not be used for persistence.
- This read command does not change nutrition, births, lineage or WorldBox saves.
- `ActorData.id` is inferred from exact 0.51.2 metadata (`BaseSystemData.id` + `Actor.data`) and needs a live probe. If missing, fail closed rather than using names/positions.
- Requires a **paused and fully loaded map**; small worlds only (at most 5000 visible permitted actors). The command is intentionally not a general concurrent pagination API.
- Authenticated loopback connection only. Never upload private BepInEx tokens/log files without redaction.
- No proprietary WorldBox binaries or code are redistributed.
