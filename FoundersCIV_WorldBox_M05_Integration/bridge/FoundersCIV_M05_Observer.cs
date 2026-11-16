// M05 SOURCE — safety-first observer; requires local C# build and live validation.
// BepInEx 5 (Unity Mono) + Harmony 2; add as a separate plugin to your locally
// installed WorldBox. WorldBox remains the ONLY gameplay/physiology authority.
using BepInEx;
using HarmonyLib;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace FoundersCIV.WorldBoxM05
{
    [BepInPlugin("org.foundersciv.worldbox.m05.events", "FoundersCIV M05 Native Event Observer", "0.5.4")]
    public sealed class M05EventBridge : BaseUnityPlugin
    {
        internal static M05EventBridge Current;
        private Harmony _harmony;
        private StreamWriter _writer;
        private readonly Queue<string> _pending = new Queue<string>();
        private readonly object _guard = new object();
        private long _nextSequence = 0;
        private long _lost = 0;
        private string _session;
        private string _worldKey;
        private string _output;
        private string _projectionPath;
        private float _nextProjectionRead;
        private float _nextDiagnosticRead;
        private long _updateFrames;
        private static long _hitNutrition, _hitPrey, _hitFood, _hitKill, _hitDeath, _hitBaby, _hitBirth;
        private static long _callbackErrors, _emitErrors;
        private LiveState _live;
        [Serializable] private sealed class LiveTree {
            public string tree_id = "";
            public float health;
            public bool alive;
            public int unharvested_fruit;
            public string native_status = "";
        }
        [Serializable] private sealed class LiveState {
            public string world_key = "";
            public string projection_kind = "";
            public int period;
            public int shared_river_remaining;
            public LiveTree[] trees = new LiveTree[0];
        }
        private readonly List<string> _activeHooks = new List<string>();
        private const int MaxQueue = 50000;
        private const int FlushBatch = 8192;
        private static MethodInfo _getNutrition;
        private static MethodInfo _getId;
        private static MethodInfo _hasDied;
        private static long _nextContext;
        [ThreadStatic] private static Stack<string> _consumptionContexts;

        [Serializable]
        internal sealed class Event
        {
            public int schema = 1;
            public string session_id = "";
            public string world_key = "";
            public long seq;
            public string kind = "";
            public string observed_utc = "";
            public string source_method = "";
            public long actor_id = -1;
            public long target_id = -1;
            public string context_id = "";
            public int native_amount = 0;
            public int nutrition_before = -1;
            public int nutrition_after = -1;
            public int native_delta = 0;
            public bool native_success = false;
            public string resource = "";
            public string notes = "";
            public long dropped = 0;
            public string assembly_sha256 = "";
            public string[] active_hooks = new string[0];
        }

        private void Awake()
        {
            Current = this;
            _session = Guid.NewGuid().ToString("N");
            var baseDir = Path.Combine(Paths.BepInExRootPath, "FoundersCIV_M05");
            Directory.CreateDirectory(baseDir);
            var worldKeyPath = Path.Combine(baseDir, "world_key.txt");
            _worldKey = File.Exists(worldKeyPath) ? File.ReadAllText(worldKeyPath).Trim() : "UNBOUND";
            if (string.IsNullOrWhiteSpace(_worldKey)) _worldKey = "UNBOUND";
            _output = Path.Combine(baseDir, "m05_" + _session + ".jsonl");
            _projectionPath = Path.Combine(baseDir, "live_state.json");
            _writer = new StreamWriter(new FileStream(_output, FileMode.CreateNew, FileAccess.Write,
                FileShare.Read, 65536), new UTF8Encoding(false), 65536);

            var actor = AccessTools.TypeByName("Actor");
            var baseSim = AccessTools.TypeByName("BaseSimObject");
            _getNutrition = actor == null ? null : AccessTools.Method(actor, "getNutrition", new Type[0]);
            _hasDied = actor == null ? null : AccessTools.Method(actor, "hasDied", new Type[0]);
            _getId = baseSim == null ? null : AccessTools.Method(baseSim, "getID", new Type[0]);
            _harmony = new Harmony("org.foundersciv.worldbox.m05.events");
            const string ExpectedAssemblySha = "51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f";
            string detectedSha = "";
            try {
                if (actor != null) using (var sha = SHA256.Create())
                using (var fs = File.OpenRead(actor.Assembly.Location))
                    detectedSha = BitConverter.ToString(sha.ComputeHash(fs)).Replace("-", "").ToLowerInvariant();
            } catch (Exception ex) { Logger.LogWarning("Assembly hash unavailable: " + ex.Message); }
            bool mayPatch = _worldKey != "UNBOUND" && detectedSha == ExpectedAssemblySha;
            if (!mayPatch) Logger.LogError("M05 observer fail-closed: bind a unique world_key and use the verified WorldBox build. Assembly SHA=" + detectedSha);
            if (mayPatch) {

            TryPatch("Actor", "addNutritionFromEating", 3, "Actor.addNutritionFromEating",
                nameof(NutritionPrefix), nameof(NutritionFinalizer));
            TryPatch("ai.behaviours.BehConsumeActorTarget", "consume", 2,
                "ai.behaviours.BehConsumeActorTarget.consume", nameof(PreyPrefix), nameof(PreyFinalizer));
            TryPatch("Actor", "consumeFoodResource", 1, "Actor.consumeFoodResource",
                nameof(ResourcePrefix), nameof(ResourceFinalizer));
            TryPatch("Actor", "newKillAction", 3, "Actor.newKillAction", nameof(KillPrefix), nameof(KillFinalizer));
            TryPatch("Actor", "die", 4, "Actor.die", nameof(DiePrefix), nameof(DieFinalizer));
            TryPatch("ActorManager", "createBabyActorFromData", 3,
                "ActorManager.createBabyActorFromData", null, nameof(BabyFinalizer));
            TryPatch("Actor", "birthEvent", 2, "Actor.birthEvent", null, nameof(BirthFinalizer));

            }
            Emit(new Event {kind = "session_open", assembly_sha256 = detectedSha,
                active_hooks = _activeHooks.ToArray(), notes = "Native gameplay unmodified; source functions require runtime semantic validation"});
            Logger.LogInfo("M05 event observer started: " + _output + ", hooks " + _activeHooks.Count);
        }

        private void TryPatch(string typeName, string methodName, int argCount,
            string label, string prefixName, string finalizerName)
        {
            try {
                var t = AccessTools.TypeByName(typeName);
                if (t == null) { Logger.LogWarning("Missing type " + typeName); return; }
                var found = t.GetMethods(BindingFlags.Instance|BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)
                    .Where(x=>x.Name == methodName && x.GetParameters().Length==argCount).ToArray();
                if (found.Length!=1) {
                    Logger.LogWarning("Ambiguous/missing hook " + label + " with " + argCount + " params; matches=" + found.Length);
                    return;
                }
                var binding = BindingFlags.Static|BindingFlags.NonPublic;
                var prefix = prefixName == null ? null : typeof(M05EventBridge).GetMethod(prefixName, binding);
                var finalizer = finalizerName == null ? null : typeof(M05EventBridge).GetMethod(finalizerName, binding);
                // HarmonyX marks the five-argument overload obsolete with error=true.
                // Explicit sixth argument resolves to the supported overload.
                _harmony.Patch(found[0], prefix == null ? null : new HarmonyMethod(prefix), null,
                    null, finalizer == null ? null : new HarmonyMethod(finalizer), null);
                _activeHooks.Add(label);
            } catch (Exception ex) { Logger.LogError("Failed to attach " + label + ": " + ex); }
        }

        private static int Nutrition(object actor)
        {
            try {return _getNutrition == null || actor == null ? -1 : Convert.ToInt32(_getNutrition.Invoke(actor, null));}
            catch { return -1; }
        }
        private static bool HasDied(object actor)
        {
            try {return _hasDied != null && actor != null && Convert.ToBoolean(_hasDied.Invoke(actor,null));}
            catch {return false;}
        }
        private static long Id(object actor)
        {
            try { return _getId == null || actor == null ? -1 : Convert.ToInt64(_getId.Invoke(actor, null)); }
            catch { return -1; }
        }
        private static int SafeInt(object value)
        {
            try {return Convert.ToInt32(value);} catch {return 0;}
        }
        private static string ResourceLabel(object resource)
        {
            if (resource == null) return "";
            try {
                var type = resource.GetType();
                var field = AccessTools.Field(type, "id") ?? AccessTools.Field(type, "name");
                string value = field == null ? type.Name : Convert.ToString(field.GetValue(resource));
                return value == null ? "" : (value.Length > 100 ? value.Substring(0,100) : value);
            } catch { return "unresolved_resource"; }
        }

        private void Emit(Event ev)
        {
            try {
                lock (_guard) {
                    if (_pending.Count >= MaxQueue) {
                        ++_nextSequence; ++_lost; // forced sequence discontinuity prevents false completeness
                        return;
                    }
                    if (_lost > 0) {
                        var lost = new Event {kind="bridge_loss", dropped=_lost,
                            notes="Event observer queue overflow; dataset MUST NOT be promoted"};
                        _lost = 0;
                        EnqueueLocked(lost);
                    }
                    EnqueueLocked(ev);
                }
            } catch (Exception ex) {
                var n = System.Threading.Interlocked.Increment(ref _emitErrors);
                if (n <= 5) Logger.LogError("M05 event emission failed: " + ex);
            }
        }
        private void EnqueueLocked(Event ev)
        {
            ev.session_id = _session;
            ev.world_key = _worldKey;
            ev.seq = ++_nextSequence;
            ev.observed_utc = DateTime.UtcNow.ToString("o");
            _pending.Enqueue(JsonUtility.ToJson(ev));
        }
        private static void ReportCallbackFailure(string origin, Exception ex)
        {
            var n = System.Threading.Interlocked.Increment(ref _callbackErrors);
            if (n <= 10) {
                try { if (Current != null) Current.Logger.LogError("M05 callback " + origin +
                    " failed (gameplay unchanged): " + ex); } catch { }
            }
        }
        private static void Hit(ref long counter, string method)
        {
            if (System.Threading.Interlocked.Increment(ref counter) == 1)
                Send(new Event {kind="hook_probe", source_method=method,
                    notes="target_entered; outcome_unverified"});
        }
        private static string HookCounts()
        {
            return "nutrition=" + System.Threading.Interlocked.Read(ref _hitNutrition) +
                ";prey=" + System.Threading.Interlocked.Read(ref _hitPrey) +
                ";food=" + System.Threading.Interlocked.Read(ref _hitFood) +
                ";kill=" + System.Threading.Interlocked.Read(ref _hitKill) +
                ";death=" + System.Threading.Interlocked.Read(ref _hitDeath) +
                ";baby=" + System.Threading.Interlocked.Read(ref _hitBaby) +
                ";birth=" + System.Threading.Interlocked.Read(ref _hitBirth);
        }
        private static void Send(Event ev)
        {
            try { if (Current != null) Current.Emit(ev); } catch (Exception ex) { ReportCallbackFailure("Send", ex); }
        }
        private static string CurrentContext()
        {
            return _consumptionContexts != null && _consumptionContexts.Count > 0 ?
                _consumptionContexts.Peek() : "";
        }

        // Void Harmony finalizers OBSERVE exceptions without changing them.
        // No prefix returns false, changes an argument, or changes a result.
        private static void NutritionPrefix(object __instance, out int __state)
        { Hit(ref _hitNutrition, "Actor.addNutritionFromEating"); __state = Nutrition(__instance); }
        private static void NutritionFinalizer(object __instance, object[] __args,
            int __state, Exception __exception)
        {
            try {
            int after = Nutrition(__instance);
            Send(new Event {kind="nutrition_call", actor_id=Id(__instance), source_method="Actor.addNutritionFromEating",
                native_amount=__args.Length>0 ? SafeInt(__args[0]) : 0,
                nutrition_before=__state,nutrition_after=after,
                native_delta=(__state>=0&&after>=0) ? after-__state : 0,
                context_id=CurrentContext(),native_success=__exception==null,
                notes=__exception==null?"native_nutrition_change_not_physical_energy":"native_exception"});
        
            } catch (Exception ex) { ReportCallbackFailure("NutritionFinalizer", ex); }
        }

        private static void PreyPrefix(object[] __args, out string __state)
        {
            Hit(ref _hitPrey, "ai.behaviours.BehConsumeActorTarget.consume");
            var current = Current;
            __state = current==null ? "" : current._session+":"+ System.Threading.Interlocked.Increment(ref _nextContext);
            if (_consumptionContexts == null) _consumptionContexts=new Stack<string>();
            _consumptionContexts.Push(__state);
            Send(new Event {kind="prey_consume_attempt",source_method="BehConsumeActorTarget.consume",
                actor_id=__args.Length>0?Id(__args[0]):-1,
                target_id=__args.Length>1?Id(__args[1]):-1,
                context_id=__state,notes="argument_roles_and_success_unverified"});
        }
        private static void PreyFinalizer(object[] __args, string __state, Exception __exception)
        {
            try {
            Send(new Event {kind="prey_consume_end",source_method="BehConsumeActorTarget.consume",
                actor_id=__args.Length>0?Id(__args[0]):-1,
                target_id=__args.Length>1?Id(__args[1]):-1,
                context_id=__state,native_success=__exception==null,
                notes="callback_completed_not_verified_prey_killed"});
            try {
                if (_consumptionContexts != null && _consumptionContexts.Count>0)
                    _consumptionContexts.Pop();
            } catch { }
        
            } catch (Exception ex) { ReportCallbackFailure("PreyFinalizer", ex); }
        }

        private static void ResourcePrefix(object __instance, out int __state)
        { Hit(ref _hitFood, "Actor.consumeFoodResource"); __state=Nutrition(__instance); }
        private static void ResourceFinalizer(object __instance, object[] __args, int __state, Exception __exception)
        {
            try {
            int after=Nutrition(__instance);
            Send(new Event {kind="resource_consume_call",source_method="Actor.consumeFoodResource",
                actor_id=Id(__instance),nutrition_before=__state,nutrition_after=after,
                native_delta=(__state>=0&&after>=0) ? after-__state : 0,
                resource=__args.Length>0?ResourceLabel(__args[0]):"",
                context_id=CurrentContext(),native_success=__exception==null,
                notes="can_overlap_nutrition_call_do_not_sum_as_separate_intake"});
        
            } catch (Exception ex) { ReportCallbackFailure("ResourceFinalizer", ex); }
        }
        private struct KillState { public long ActorId; public long TargetId; }
        private static void KillPrefix(object __instance, object[] __args, out KillState __state)
        {
            Hit(ref _hitKill, "Actor.newKillAction");
            __state = new KillState {ActorId=Id(__instance),TargetId=__args.Length>0?Id(__args[0]):-1};
        }
        private static void KillFinalizer(KillState __state, Exception __exception)
        {
            try {
            Send(new Event {kind="kill_callback",source_method="Actor.newKillAction",
                actor_id=__state.ActorId,target_id=__state.TargetId,
                native_success=__exception==null,context_id=CurrentContext(),
                notes="kill_callback_not_independently_verified_predation"});
        
            } catch (Exception ex) { ReportCallbackFailure("KillFinalizer", ex); }
        }
        private struct DeathState { public long ActorId; public bool WasDead; }
        private static void DiePrefix(object __instance, out DeathState __state)
        { Hit(ref _hitDeath, "Actor.die"); __state=new DeathState{ActorId=Id(__instance),WasDead=HasDied(__instance)}; }
        private static void DieFinalizer(object __instance, DeathState __state, Exception __exception)
        {
            try {
            bool after=HasDied(__instance);
            Send(new Event {kind="death_callback",source_method="Actor.die",
                actor_id=__state.ActorId,native_success=__exception==null && !__state.WasDead && after,
                context_id=CurrentContext(),notes="success_requires_false_to_true_hasDied"});
        
            } catch (Exception ex) { ReportCallbackFailure("DieFinalizer", ex); }
        }
        private static void BabyFinalizer(object __result, Exception __exception)
        {
            Hit(ref _hitBaby, "ActorManager.createBabyActorFromData");
            try {
            Send(new Event {kind="baby_factory_call",source_method="ActorManager.createBabyActorFromData",
                actor_id=__exception==null?Id(__result):-1,
                native_success=__exception==null && __result!=null,
                notes="factory_can_be_used_for_reload_or_creation_not_certified_birth"});
        
            } catch (Exception ex) { ReportCallbackFailure("BabyFinalizer", ex); }
        }
        private static void BirthFinalizer(object __instance, Exception __exception)
        {
            Hit(ref _hitBirth, "Actor.birthEvent");
            try {
            Send(new Event {kind="birth_callback",source_method="Actor.birthEvent",
                actor_id=Id(__instance),native_success=__exception==null,
                notes="requires validation of birthEvent meaning in live game"});
        
            } catch (Exception ex) { ReportCallbackFailure("BirthFinalizer", ex); }
        }

        private void Update()
        {
            ++_updateFrames;
            if (Time.unscaledTime >= _nextDiagnosticRead) {
                _nextDiagnosticRead = Time.unscaledTime + 15f;
                Emit(new Event {kind="observer_heartbeat",
                    active_hooks=_activeHooks.ToArray(),
                    notes="update_frames=" + _updateFrames + ";hook_hits=" + HookCounts() +
                        ";callback_errors=" + System.Threading.Interlocked.Read(ref _callbackErrors) +
                        ";emit_errors=" + System.Threading.Interlocked.Read(ref _emitErrors)});
            }
            if (Time.unscaledTime >= _nextProjectionRead) {
                _nextProjectionRead = Time.unscaledTime + 3f;
                try {
                    if (File.Exists(_projectionPath)) {
                        var candidate = JsonUtility.FromJson<LiveState>(File.ReadAllText(_projectionPath));
                        if (candidate != null && candidate.world_key == _worldKey &&
                            candidate.projection_kind == "VIRTUAL_M05_NOT_NATIVE_WORLD_STATE")
                            _live = candidate;
                        else _live = null;
                    }
                } catch (Exception ex) { Logger.LogWarning("M05 projection read: " + ex.Message); }
            }
            try { Drain(false); }
            catch (Exception ex) { Logger.LogError("M05 write failure, not modifying game: " + ex.Message); }
        }
        private void Drain(bool full)
        {
            if (_writer == null) return;
            int n=0;
            lock(_guard) {
                while(_pending.Count>0 && (full || n<FlushBatch)) {
                    _writer.WriteLine(_pending.Peek()); _pending.Dequeue(); ++n;
                }
                if (full && _lost>0) {
                    var ev=new Event{kind="bridge_loss",dropped=_lost,
                        notes="Final observer losses; do not promote"};
                    _lost=0;EnqueueLocked(ev);
                    while(_pending.Count>0) { _writer.WriteLine(_pending.Peek()); _pending.Dequeue(); }
                }
            }
            _writer.Flush();
        }
        private void OnGUI()
        {
            if (_live == null || _live.trees == null) return;
            try {
                int n = Math.Min(5, _live.trees.Length);
                float width = 330f;
                float height = 90f + n * 21f;
                float left = Math.Max(8f, Screen.width - width - 10f);
                GUI.Box(new Rect(left, 55f, width, height), "Founders–CIV M05 (VIRTUAL / READ ONLY)");
                GUI.Label(new Rect(left+10, 82, width-20, 22),
                    "Period " + _live.period + " | River CE " + _live.shared_river_remaining);
                for (int i=0; i<n; i++) {
                    var t = _live.trees[i];
                    GUI.Label(new Rect(left+10, 110+i*21, width-20, 21),
                        t.tree_id + "  Health " + t.health.ToString("0.00") +
                        "  Fruits " + t.unharvested_fruit);
                }
            } catch { /* never affect WorldBox's own UI/gameplay */ }
        }

        private void OnDestroy()
        {
            try {
                Emit(new Event{kind="session_close",
                    notes="best_effort_graceful_plugin_shutdown;update_frames=" + _updateFrames +
                        ";hook_hits=" + HookCounts() +
                        ";callback_errors=" + System.Threading.Interlocked.Read(ref _callbackErrors) +
                        ";emit_errors=" + System.Threading.Interlocked.Read(ref _emitErrors)});
                Drain(true);
                if(_harmony!=null) _harmony.UnpatchSelf();
                if(_writer!=null) {_writer.Dispose();_writer=null;}
            } catch(Exception ex) { Logger.LogError("M05 shutdown error " + ex.Message); }
            Current=null;
        }
    }
}
