// chime: plays one short sound when a Claude Code session needs its person.
//
// The hooks in ~/.claude/settings.json call it, and the hook's JSON arrives on stdin:
//   chime.exe done   Stop           Claude finished and is waiting for input
//   chime.exe ask    Notification   a permission prompt or a question has been waiting
//                    PreToolUse     Claude is about to ask a question / show a plan
//   chime.exe fail   StopFailure    the turn died on an API error
// By hand, to hear a cue:                        chime.exe <cue> [pack]     e.g.  chime.exe done soft
// To see how a background command is judged:     chime.exe judge <command>  (or one command per line on stdin)
//
// Which sounds and which rules: chime.json beside this file. What it did and why: chime.log.
// After an edit here, run build.cmd.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;

static class Chime
{
    static readonly string Home = AppDomain.CurrentDomain.BaseDirectory;

    [DllImport("winmm.dll", CharSet = CharSet.Unicode)]
    static extern int mciSendString(string command, StringBuilder answer, int answerLength, IntPtr callback);

    [STAThread]
    static int Main(string[] args)
    {
        // A stuck pipe or sound device must never leave processes behind.
        Timer watchdog = new Timer(delegate { Environment.Exit(0); }, null, 10000, Timeout.Infinite);
        try { Run(args); }
        catch (Exception e) { Log("error  " + e.GetType().Name + ": " + e.Message); }
        GC.KeepAlive(watchdog);
        return 0;       // always 0, and as a hook never a word on stdout: a hook must not steer Claude
    }

    static void Run(string[] args)
    {
        string kind = args.Length > 0 ? args[0].ToLowerInvariant() : "done";
        Dictionary<string, object> cfg = ReadJson(ReadFile(Path.Combine(Home, "chime.json")));
        if (kind == "judge") { Judge(args, cfg); return; }
        Dictionary<string, object> ev = ReadJson(ReadStdin(1000));

        string session = Str(ev, "session_id");
        string cwd = Str(ev, "cwd");
        string who = (session.Length > 0 ? "  session " + (session.Length > 8 ? session.Substring(0, 8) : session) : "")
                   + (cwd.Length > 0 ? "  in " + cwd : "");

        string leftRunning = "";
        if (kind == "done" && Flag(cfg, "quietWhileAgentsWork", true))
        {
            string busy = StillWorking(ev, cfg, out leftRunning);
            if (busy != null) { Log("done   quiet, Claude carries on by itself (" + busy + ")" + who); return; }
        }
        if (kind == "ask" && session.Length > 0 && AskedJustNow(session))
        {
            Log("ask    quiet, already chimed for this a moment ago" + who);
            return;
        }

        object cuesRaw; cfg.TryGetValue("cues", out cuesRaw);
        Dictionary<string, object> cues = cuesRaw as Dictionary<string, object>;
        string cue = cues != null ? Str(cues, kind) : "";
        if (cue.Length == 0) cue = kind == "done" ? "complete" : kind == "ask" ? "notification" : kind == "fail" ? "error" : kind;
        string pack = args.Length > 1 ? args[1] : Str(cfg, "pack");
        if (pack.Length == 0) pack = "minimal";
        string dir = Str(cfg, "soundsDir");
        if (dir.Length == 0) dir = Path.Combine(Home, "sounds");

        string file = Path.Combine(Path.Combine(dir, pack), cue + ".mp3");
        if (!File.Exists(file)) { Log(kind + "   no such sound: " + file + who); return; }

        string healed = Audible();
        string trouble = Play(file, Number(cfg, "volume", 100));
        Log(kind.PadRight(6) + " " + (trouble ?? "played") + " " + pack + "/" + cue + healed + leftRunning + who);
    }

    // ---- is Claude still working? ------------------------------------------------------------------------

    static readonly string[] KnownTypes = { "shell", "subagent", "monitor", "workflow", "teammate", "cloud session", "mcp task" };
    static readonly string[] DefaultQuietWhile = { "subagent", "workflow", "teammate", "cloud session", "shell", "monitor", "scheduled wakeup" };

    // A background command that matches one of these runs until somebody stops it: a server, a watcher, a
    // log tail. Claude is not waiting on it, so it must not keep "done" quiet. Everything else in the
    // background (a render, a test run, a download, a wait loop) is work that ends, and Claude wakes by
    // itself when it does. Matched against the command line only, never the description: a render "through
    // the ComfyUI server" is still a render. A compound command counts as a server if any part of it is one,
    // because that is what it turns into. When in doubt these lean towards "server": ringing a little early
    // is a smaller mistake than never ringing at all.
    // Your own additions: "runsUntilStopped" in chime.json. Your own exceptions: "keepsWorking".
    static readonly string[] RunsUntilStopped =
    {
        @"\b(npm|pnpm|yarn|bun)\b[^;&|]*\s(dev|start|serve|preview|watch|storybook)(:[\w-]+)?(\s|$)",
        @"\b(turbo|nx|lerna)\s+(run\s+)?(dev|serve|start|watch)\b",
        @"\bserve\b",
        @"\brunserver\b",
        @"\b(dev|web)[-_]?server\b",
        @"\bserver\.(js|mjs|cjs|ts|py|rb)\b",
        @"\bhttp\.server\b",
        @"\b(http-server|live-server|browser-sync|nodemon|watchexec|entr)\b",
        @"\bvite(\s+(dev|serve|preview))?\s*($|[;&|]|--)",
        @"\b(next|nuxt|astro|expo|react-scripts|storybook)\s+(dev|start|preview)\b",
        @"\bgatsby\s+develop\b",
        @"\b(uvicorn|gunicorn|hypercorn|daphne)\b",
        @"\bflask\s+(-\S+\s+(\S+\s+)?)*run\b",
        @"\b(streamlit|chainlit)\s+run\b",
        @"\bgradio\s+\S+\.py\b",
        @"\bjupyter\s+(lab|notebook|server)\b",
        @"\btensorboard\b",
        @"\bcelery\b.*\b(worker|beat)\b",
        @"\brails\s+(s|server)\b",
        @"\bphp\s+-S\b",
        @"\bhugo\s+server\b",
        @"\bphx\.server\b",
        @"\b(dotnet|cargo|tsx)\s+watch\b",
        @"\s--watch(\s|=|$)",
        @"\btsc\b.*\s-w\b",
        @"\btail\b[^;&|]*\s(-[a-z0-9]*f|--follow)\b",
        @"\bGet-Content\b.*\s-Wait\b",
        @"\b(logs|journalctl)\b.*\s(-f|--follow)\b",
        @"\bdocker[\s-]compose\b.*\bup\b(?!.*\s(-d|--detach)\b)",
        @"\b(port-forward|ngrok)\b",
        @"\bcloudflared\s+tunnel\b",
        @"\b(redis-server|mongod|mysqld)\b",
        @"\bcaddy\s+run\b",
        @"\bComfyUI[\\/]main\.py\b",
        @"\bwebui(-user)?\.(sh|bat)\b",
        @"\b(llama-server|koboldcpp)\b",
    };

    // Stop also fires when the main loop parks while its own background work is still running: an agent, a
    // workflow, a render in a background shell, a monitor. Claude then wakes by itself, so it is not waiting
    // for a person. The Stop hook's input lists what is in flight. Returns what keeps "done" quiet, or null.
    static string StillWorking(Dictionary<string, object> ev, Dictionary<string, object> cfg, out string leftRunning)
    {
        List<string> quiet = Names(cfg, "quietWhile", DefaultQuietWhile);
        List<Regex> endless = Patterns(cfg, "runsUntilStopped", RunsUntilStopped);
        List<Regex> finite = Patterns(cfg, "keepsWorking", null);

        List<string> busy = new List<string>();
        List<string> left = new List<string>();
        foreach (object item in Items(ev, "background_tasks"))
        {
            Dictionary<string, object> task = item as Dictionary<string, object>;
            if (task == null) continue;
            string status = Str(task, "status").ToLowerInvariant();
            if (status == "completed" || status == "failed" || status == "killed" || status == "stopped" || status == "cancelled") continue;
            string type = Str(task, "type").ToLowerInvariant();
            string command = Str(task, "command");
            // Only shells carry a command, so an unfamiliar label that has one is a shell under another name.
            if (command.Length > 0 && Array.IndexOf(KnownTypes, type) < 0) type = "shell";
            if (!quiet.Contains(type)) continue;
            if (command.Length > 0 && Endless(command, endless, finite)) { left.Add(Short(command)); continue; }
            string name = command.Length > 0 ? type + ": " + Short(command) : type;
            if (!busy.Contains(name)) busy.Add(name);
        }
        if (Items(ev, "session_crons").Count > 0 && quiet.Contains("scheduled wakeup")) busy.Add("scheduled wakeup");
        leftRunning = left.Count == 0 ? "" : " (left running: " + string.Join("; ", left.ToArray()) + ")";
        return busy.Count == 0 ? null : string.Join(", ", busy.ToArray());
    }

    static bool Endless(string command, List<Regex> endless, List<Regex> finite)
    {
        return !Matches(command, finite) && Matches(command, endless);
    }

    static bool Matches(string text, List<Regex> patterns)
    {
        foreach (Regex r in patterns)
        {
            try { if (r.IsMatch(text)) return true; }
            catch (RegexMatchTimeoutException) { }
        }
        return false;
    }

    // The built-in patterns plus the ones chime.json adds under `key`. A pattern that does not compile is
    // logged and skipped: one typo must not silence the chime.
    static List<Regex> Patterns(Dictionary<string, object> cfg, string key, string[] builtIn)
    {
        List<string> sources = new List<string>();
        if (builtIn != null) sources.AddRange(builtIn);
        foreach (object p in Items(cfg, key)) if (p != null && p.ToString().Trim().Length > 0) sources.Add(p.ToString());
        List<Regex> list = new List<Regex>();
        foreach (string s in sources)
        {
            try { list.Add(new Regex(s, RegexOptions.IgnoreCase | RegexOptions.CultureInvariant, TimeSpan.FromMilliseconds(250))); }
            catch (ArgumentException e) { Log("config skipped a pattern in \"" + key + "\" that does not compile: " + s + "  (" + e.Message + ")"); }
        }
        return list;
    }

    static List<string> Names(Dictionary<string, object> cfg, string key, string[] fallback)
    {
        List<string> names = new List<string>();
        if (!cfg.ContainsKey(key)) { names.AddRange(fallback); return names; }
        foreach (object n in Items(cfg, key)) if (n != null) names.Add(n.ToString().Trim().ToLowerInvariant());
        return names;
    }

    static string Short(string command)
    {
        string one = Regex.Replace(command, @"\s+", " ").Trim();
        return one.Length <= 90 ? one : one.Substring(0, 87) + "...";
    }

    // chime.exe judge <command>: says, in chime.log and on stdout, whether that background command would
    // keep "done" quiet. With no command it judges each line of stdin.
    static void Judge(string[] args, Dictionary<string, object> cfg)
    {
        List<Regex> endless = Patterns(cfg, "runsUntilStopped", RunsUntilStopped);
        List<Regex> finite = Patterns(cfg, "keepsWorking", null);
        List<string> commands = new List<string>();
        if (args.Length > 1) commands.Add(string.Join(" ", args, 1, args.Length - 1));
        else foreach (string line in ReadStdin(8000).Split('\n')) if (line.Trim().Length > 0) commands.Add(line.Trim());

        StringBuilder said = new StringBuilder();
        foreach (string command in commands)
        {
            string verdict = Endless(command, endless, finite)
                ? "rings  (runs until stopped, so the chime does not wait for it)  "
                : "quiet  (work that ends, so the chime waits for it)  ";
            Log("judge  " + verdict + Short(command));
            said.AppendLine(verdict + command);
        }
        try
        {
            // Raw bytes: this is a windowless program, so it has no console to set an encoding on.
            byte[] bytes = Encoding.UTF8.GetBytes(said.ToString());
            using (Stream o = Console.OpenStandardOutput()) { o.Write(bytes, 0, bytes.Length); o.Flush(); }
        }
        catch { }
    }

    // ---- asking twice ------------------------------------------------------------------------------------

    // A question can reach here twice (when Claude asks, and again when the prompt has sat for a few seconds).
    static bool AskedJustNow(string session)
    {
        StringBuilder safe = new StringBuilder();
        foreach (char c in session) if (char.IsLetterOrDigit(c) || c == '-') safe.Append(c);
        string dir = Path.Combine(Path.GetTempPath(), "claude-chime");
        Directory.CreateDirectory(dir);
        string mark = Path.Combine(dir, safe + ".ask");
        bool recent = File.Exists(mark) && (DateTime.UtcNow - File.GetLastWriteTimeUtc(mark)).TotalSeconds < 10;
        if (!recent) File.WriteAllText(mark, "");
        return recent;
    }

    // ---- sound -------------------------------------------------------------------------------------------

    static string Play(string file, int volume)
    {
        int rc = mciSendString("open \"" + file + "\" type mpegvideo alias chime", null, 0, IntPtr.Zero);
        if (rc != 0) return "could not open (mci " + rc + ")";
        if (volume >= 0 && volume < 100) mciSendString("setaudio chime volume to " + (volume * 10), null, 0, IntPtr.Zero);
        rc = mciSendString("play chime wait", null, 0, IntPtr.Zero);
        Thread.Sleep(120);      // let the tail leave the device before the process goes
        mciSendString("close chime", null, 0, IntPtr.Zero);
        return rc != 0 ? "could not play (mci " + rc + ")" : null;
    }

    // Dictation software (Wispr Flow) turns other apps down while it listens, and Windows remembers the level
    // per program: a program that exits while turned down stays at 0% for good. Undo only that case, so a
    // level chosen on purpose in the Windows volume mixer (this shows there as "chime") is left alone.
    static string Audible()
    {
        try
        {
            IMMDeviceEnumerator devices = (IMMDeviceEnumerator)(new MMDeviceEnumeratorCom());
            IMMDevice device;
            if (devices.GetDefaultAudioEndpoint(0, 0, out device) != 0) return "";
            Guid iid = typeof(IAudioSessionManager).GUID;
            object manager;
            if (device.Activate(ref iid, 23, IntPtr.Zero, out manager) != 0) return "";
            ISimpleAudioVolume mine;
            if (((IAudioSessionManager)manager).GetSimpleAudioVolume(IntPtr.Zero, 0, out mine) != 0) return "";
            float level; bool muted;
            mine.GetMasterVolume(out level);
            mine.GetMute(out muted);
            if (level < 0.05f || muted)
            {
                Guid none = Guid.Empty;
                mine.SetMasterVolume(1f, ref none);
                mine.SetMute(false, ref none);
                return " (the mixer had chime at " + Math.Round(level * 100) + "%" + (muted ? ", muted" : "") + "; put back to 100%)";
            }
        }
        catch { }
        return "";
    }

    // ---- plumbing ----------------------------------------------------------------------------------------

    // Waits at most `patience` milliseconds for the input to end: a hook must never hang on a pipe.
    static string ReadStdin(int patience)
    {
        string text = "";
        Thread reader = new Thread(delegate()
        {
            try
            {
                using (Stream s = Console.OpenStandardInput())
                using (StreamReader r = new StreamReader(s, Encoding.UTF8))
                    text = r.ReadToEnd();
            }
            catch { }
        });
        reader.IsBackground = true;
        reader.Start();
        reader.Join(patience);
        return text;
    }

    static string ReadFile(string path)
    {
        try { return File.ReadAllText(path); } catch { return ""; }
    }

    static Dictionary<string, object> ReadJson(string text)
    {
        try
        {
            if (text != null && text.Trim().Length > 0)
            {
                JavaScriptSerializer json = new JavaScriptSerializer();
                json.MaxJsonLength = int.MaxValue;
                Dictionary<string, object> d = json.DeserializeObject(text) as Dictionary<string, object>;
                if (d != null) return d;
            }
        }
        catch { }
        return new Dictionary<string, object>();
    }

    static string Str(Dictionary<string, object> d, string key)
    {
        object v;
        return d.TryGetValue(key, out v) && v != null ? v.ToString() : "";
    }

    static IList Items(Dictionary<string, object> d, string key)
    {
        object v;
        if (d.TryGetValue(key, out v)) { IList list = v as IList; if (list != null) return list; }
        return new object[0];
    }

    static bool Flag(Dictionary<string, object> d, string key, bool fallback)
    {
        object v;
        return d.TryGetValue(key, out v) && v is bool ? (bool)v : fallback;
    }

    static int Number(Dictionary<string, object> d, string key, int fallback)
    {
        object v;
        if (d.TryGetValue(key, out v) && v != null) { try { return Convert.ToInt32(v); } catch { } }
        return fallback;
    }

    static void Log(string line)
    {
        try
        {
            string path = Path.Combine(Home, "chime.log");
            FileInfo f = new FileInfo(path);
            if (f.Exists && f.Length > 200000)
            {
                string[] all = File.ReadAllLines(path);
                string[] keep = new string[all.Length / 2];
                Array.Copy(all, all.Length - keep.Length, keep, 0, keep.Length);
                File.WriteAllLines(path, keep);
            }
            File.AppendAllText(path, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "  " + line + Environment.NewLine);
        }
        catch { }
    }

    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
    class MMDeviceEnumeratorCom { }

    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceEnumerator
    {
        [PreserveSig] int EnumAudioEndpoints(int dataFlow, int stateMask, out IntPtr devices);
        [PreserveSig] int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice device);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDevice
    {
        [PreserveSig] int Activate(ref Guid iid, int clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object iface);
    }

    [ComImport, Guid("BFA971F1-4D5E-40BB-935E-967039BFBEE4"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioSessionManager
    {
        [PreserveSig] int GetAudioSessionControl(IntPtr sessionGuid, int streamFlags, out IntPtr control);
        [PreserveSig] int GetSimpleAudioVolume(IntPtr sessionGuid, int streamFlags, out ISimpleAudioVolume volume);
    }

    [ComImport, Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface ISimpleAudioVolume
    {
        [PreserveSig] int SetMasterVolume(float level, ref Guid context);
        [PreserveSig] int GetMasterVolume(out float level);
        [PreserveSig] int SetMute([MarshalAs(UnmanagedType.Bool)] bool mute, ref Guid context);
        [PreserveSig] int GetMute([MarshalAs(UnmanagedType.Bool)] out bool mute);
    }
}
