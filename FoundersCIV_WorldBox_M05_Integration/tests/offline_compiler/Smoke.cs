// TEST ONLY: exercise the real compiled M05 queue logic with stub game APIs.
using System;
using System.Collections;
using System.IO;
using System.Reflection;
using FoundersCIV.WorldBoxM05;

internal static class Smoke {
    private const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
    static FieldInfo Field(string name) {
        var f = typeof(M05EventBridge).GetField(name, Private);
        if (f == null) throw new Exception("Missing field " + name);
        return f;
    }
    static void Set(M05EventBridge o, string name, object value) {
        Field(name).SetValue(o, value);
    }
    static object Get(M05EventBridge o, string name) { return Field(name).GetValue(o); }
    static void Call(M05EventBridge o, string name, params object[] args) {
        var m = typeof(M05EventBridge).GetMethod(name, Private);
        if (m == null) throw new Exception("Missing method " + name);
        m.Invoke(o, args);
    }
    static void Check(bool condition, string message) {
        if (!condition) throw new Exception(message);
    }
    static void Main() {
        var o = new M05EventBridge();
        Set(o, "_session", "fixture");
        Set(o, "_worldKey", "copy-only");
        using (var writer = new StreamWriter(new MemoryStream())) {
            Set(o, "_writer", writer);
            for (int i = 0; i < 50001; i++)
                Call(o, "Emit", new M05EventBridge.Event { kind = "nutrition_call" });
            var q = (ICollection)Get(o, "_pending");
            Check(q.Count == 50000, "queue exceeded 50k cap");
            Check((long)Get(o, "_lost") == 1, "expected exactly one lost event");
            Call(o, "Drain", true);
            Check(q.Count == 0, "drain did not empty queue");
            Check((long)Get(o, "_lost") == 0, "drain did not clear lost counter");
            writer.Flush();
            var stream = (MemoryStream)writer.BaseStream;
            stream.Position = 0;
            using (var reader = new StreamReader(stream, System.Text.Encoding.UTF8, false, 1024, true)) {
                int count = 0, markers = 0;
                string line;
                while ((line = reader.ReadLine()) != null) {
                    count++;
                    if (line == "bridge_loss") markers++;
                }
                Check(count == 50001, "expected 50k events plus one loss marker");
                Check(markers == 1, "missing or duplicated loss marker");
            }
        }
        Console.WriteLine("C044 C# M05 queue smoke PASS: 50,000 cap, one dropped event, one loss marker, full drain");
        // C046: the real observer Update must detach hooks and stop recording
        // after a user creates disable.flag. No game API hooks are invoked here.
        var flag = Path.GetTempFileName();
        try {
            var disabled = new M05EventBridge();
            var harmony = new HarmonyLib.Harmony("c046-test");
            Set(disabled, "_session", "disabled-fixture");
            Set(disabled, "_worldKey", "copied-save");
            Set(disabled, "_harmony", harmony);
            Set(disabled, "_disablePath", flag);
            using (var memory = new MemoryStream())
            using (var sink = new StreamWriter(memory, new System.Text.UTF8Encoding(false), 1024, true)) {
                Set(disabled, "_writer", sink);
                UnityEngine.Time.unscaledTime = 1f;
                Call(disabled, "Update");
                Check((bool)Get(disabled, "_observerDisabled"), "disable flag did not disable observer");
                Check(harmony.WasUnpatched, "disable flag did not unpatch Harmony hooks");
                sink.Flush();
                var firstLength = memory.Length;
                Check(firstLength > 0, "disable marker not recorded");
                memory.Position = 0;
                using (var reader = new StreamReader(memory, System.Text.Encoding.UTF8, false, 1024, true)) {
                    Check(reader.ReadLine() == "observer_disabled", "wrong first disable record");
                    Check(reader.ReadLine() == null, "disabled observer wrote an unexpected heartbeat");
                }
                File.Delete(flag);
                UnityEngine.Time.unscaledTime = 2f;
                Call(disabled, "Update");
                Check((bool)Get(disabled, "_observerDisabled"), "observer re-enabled without restart");
                // Native callback Send must remain a no-op even if Harmony unpatch failed.
                M05EventBridge.Current = disabled;
                try {
                    var send = typeof(M05EventBridge).GetMethod(
                        "Send", BindingFlags.Static | BindingFlags.NonPublic);
                    Check(send != null, "missing native callback output guard");
                    send.Invoke(null, new object[] { new M05EventBridge.Event { kind = "nutrition_call" } });
                    Call(disabled, "Drain", true);
                } finally {
                    M05EventBridge.Current = null;
                }
                Check(memory.Length == firstLength, "disabled observer continued recording native events");
            }
            Console.WriteLine("C046 C# disable smoke PASS: unpatch, one disable marker, no heartbeat, no callback, no automatic re-enable");
        }
        finally {
            if (File.Exists(flag)) File.Delete(flag);
        }
    }
}
