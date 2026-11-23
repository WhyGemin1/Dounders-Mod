// Original Founders-CIV M01 adapter source. Read-only; no WorldBox proprietary code.
// Target: WorldBoxBridge 0.51.2 fork, mod/src/WorldBoxBridge/Commands/Read/
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;
using WorldBoxBridge.Commands.Action;
using WorldBoxBridge.Http;
using WorldBoxBridge.Reflection;
using WorldBoxBridge.Session;
using WorldBoxBridge.Threading;

namespace WorldBoxBridge.Commands.Read;

/// <summary>Paused, complete, stable-ID observation for a single WorldBox world.
/// Unlike query_actors, this command never uses names/positions as identity.
/// It exposes actor.data.id (inherited from BaseSystemData) and only read fields.
/// All reflection happens on Unity main thread, dispatched by the existing bridge.
/// </summary>
internal sealed class QueryActorIdentitiesCommand : ICommand
{
    private readonly WorldAccess _world;
    private const int MaxActors = 5000;
    public QueryActorIdentitiesCommand(WorldAccess world) => _world = world;
    public string Name => "query_actor_identities";
    public CommandCategory Category => CommandCategory.Read;
    public string Description => "Read a full, paused snapshot of native actor IDs, ancestry and basic state. "
        + "Fails closed if any visible actor ID is missing/duplicated or more than 5000 actors match.";
    public bool RequiresMainThread => true;
    public JObject ArgsSchema => new(
        new JProperty("type", "object"),
        new JProperty("properties", new JObject(
            new JProperty("asset_id", new JObject(new JProperty("type", "string")))
        )),
        new JProperty("additionalProperties", false));

    private sealed class IdentityRow
    {
        public string native_actor_id { get; set; } = "";
        public string asset_id { get; set; } = "";
        public string? name { get; set; }
        public long? kingdom_id { get; set; }
        public int? x { get; set; }
        public int? y { get; set; }
        public string? parent_id_1 { get; set; }
        public string? parent_id_2 { get; set; }
        public int? generation { get; set; }
        public double? nutrition { get; set; }
        public double? stamina { get; set; }
        public string? native_created_time { get; set; }
    }
    private static string? StringID(object? id)
    {
        if (id is null) return null;
        var s = Convert.ToString(id, CultureInfo.InvariantCulture)?.Trim();
        return string.IsNullOrEmpty(s) ? null : s;
    }
    private static int? IntValue(object? value)
    {
        try { return value == null ? null : Convert.ToInt32(value, CultureInfo.InvariantCulture); }
        catch (Exception) { return null; }
    }
    private static double? DoubleValue(object? value)
    {
        try { return value == null ? null : Convert.ToDouble(value, CultureInfo.InvariantCulture); }
        catch (Exception) { return null; }
    }
    private static long? LongValue(object? value)
    {
        try { return value == null ? null : Convert.ToInt64(value, CultureInfo.InvariantCulture); }
        catch (Exception) { return null; }
    }

    public Task<object?> ExecuteAsync(JObject args, RequestContext ctx, CancellationToken cancellationToken)
    {
        ctx.Require(Permission.ReadOwnFaction);
        if (_world.IsWorldLoading == true)
            throw new BridgeRejectionException(ErrorCode.GameRejected, "World is still loading.");
        if (_world.IsPaused != true)
            throw new BridgeRejectionException(ErrorCode.GameRejected, "Pause WorldBox before a stable-ID snapshot.");
        var manager = _world.UnitsManager;
        var source = manager is null ? null : _world.GetSimpleList(manager);
        if (source is null)
            throw new BridgeRejectionException(ErrorCode.GameRejected, "WorldBox units unavailable.");
        var speciesFilter = args.Value<string?>("asset_id");
        var list = new List<IdentityRow>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        var scanned = 0;
        foreach (var actor in source)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (actor is null) continue;
            scanned++;
            var aliveMethod = _world.CachedMethod(actor.GetType(), "isAlive");
            if (aliveMethod?.Invoke(actor, Array.Empty<object>()) is bool alive && !alive)
                continue;
            var asset = _world.Read(actor, "asset");
            var assetId = asset is null ? null : StringID(_world.Read(asset, "id"));
            if (speciesFilter != null && assetId != speciesFilter) continue;
            var kingdom = _world.Read(actor, "kingdom");
            var kingdomId = kingdom is null ? null : LongValue(_world.Read(kingdom,"id"));
            if (kingdomId.HasValue && !ctx.CanSeeKingdom(kingdomId.Value)) continue;
            var data = _world.Read(actor, "data");
            // ActorData inherits BaseSystemData.id in the recorded 0.51.2 assembly.
            var nativeId = data is null ? null : StringID(_world.Read(data, "id"));
            if (nativeId == null || assetId == null)
                throw new BridgeRejectionException(ErrorCode.GameRejected,
                    "Native ID or asset ID unavailable; cannot safely enroll this actor.");
            if (!seen.Add(nativeId))
                throw new BridgeRejectionException(ErrorCode.GameRejected,
                    "Duplicate native ActorData.id observed; identity mapping unsafe.");
            var tile = _world.Read(actor, "current_tile");
            list.Add(new IdentityRow {
                native_actor_id = nativeId,
                asset_id = assetId,
                name = _world.CachedMethod(actor.GetType(), "getName")?.Invoke(actor,Array.Empty<object>()) as string,
                kingdom_id = kingdomId,
                x = tile is null ? null : IntValue(_world.Read(tile,"x")),
                y = tile is null ? null : IntValue(_world.Read(tile,"y")),
                parent_id_1 = data is null ? null : StringID(_world.Read(data,"parent_id_1")),
                parent_id_2 = data is null ? null : StringID(_world.Read(data,"parent_id_2")),
                generation = data is null ? null : IntValue(_world.Read(data,"generation")),
                nutrition = data is null ? null : DoubleValue(_world.Read(data,"nutrition")),
                stamina = data is null ? null : DoubleValue(_world.Read(data,"stamina")),
                native_created_time = data is null ? null : StringID(_world.Read(data,"created_time"))
            });
            if (list.Count > MaxActors)
                throw new BridgeRejectionException(ErrorCode.GameRejected,
                    "More than 5000 actors; M01 requires a smaller test world.");
        }
        list.Sort((x,y)=>string.CompareOrdinal(x.native_actor_id,y.native_actor_id));
        return Task.FromResult<object?>(new {
            world_seed = _world.WorldSeed,
            tick = MainThreadDispatcher.LastTick,
            paused = true,
            world_loading = false,
            matched = list.Count,
            returned = list.Count,
            total_scanned = scanned,
            missing_identity_count = 0,
            duplicate_identity_count = 0,
            offset = 0,
            has_more = false,
            items = list
        });
    }
}
