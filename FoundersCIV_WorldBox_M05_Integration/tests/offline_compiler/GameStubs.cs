// TEST-ONLY STUBS for compiling M05 behavior without licensed WorldBox DLLs.
// These do not assert compatibility with the real game's API or BepInEx runtime.
using System;
using System.Reflection;

namespace BepInEx {
  [AttributeUsage(AttributeTargets.Class)]
  public sealed class BepInPluginAttribute : Attribute {
    public BepInPluginAttribute(string id, string name, string version) { }
  }
  public static class Paths { public static string BepInExRootPath = ""; }
  public sealed class StubLog {
    public void LogWarning(object x) { }
    public void LogError(object x) { }
    public void LogInfo(object x) { }
  }
  public class BaseUnityPlugin : UnityEngine.MonoBehaviour {
    public readonly StubLog Logger = new StubLog();
  }
}
namespace HarmonyLib {
  public class HarmonyMethod {
    public HarmonyMethod(MethodInfo method) { }
  }
  public class Harmony {
    public bool WasUnpatched {get;private set;}
    public Harmony(string id) { }
    public void Patch(MethodInfo method, HarmonyMethod prefix, HarmonyMethod postfix,
                      HarmonyMethod transpiler, HarmonyMethod finalizer, HarmonyMethod without) { }
    public void UnpatchSelf() { WasUnpatched = true; }
  }
  public static class AccessTools {
    public static Type TypeByName(string name) { return null; }
    public static MethodInfo Method(Type type, string name, Type[] args) { return null; }
    public static FieldInfo Field(Type type, string name) { return null; }
  }
}
namespace UnityEngine {
  public class MonoBehaviour { }
  public static class Time { public static float unscaledTime; }
  public static class Screen { public static int width = 1920; }
  public struct Rect {
    public Rect(float x, float y, float width, float height) { }
  }
  public static class GUI {
    public static void Box(Rect rect, string text) { }
    public static void Label(Rect rect, string text) { }
  }
  public static class JsonUtility {
    public static string ToJson(object o) {
      // The queue test only needs the event's observable kind.
      return (string)o.GetType().GetField("kind").GetValue(o);
    }
    public static T FromJson<T>(string json) { return default(T); }
  }
}
