# Setting up the chime

A short sound when a Claude Code session needs you, played by **`chime.exe`**, a small
Windows program built from the single C# file in this directory. This document is written so
an AI agent can perform the install for you. Open Claude Code (or any coding agent) in this
repo and say:

> Read chime-setup/CHIME_SETUP.md and perform the setup it describes.

## What it does

Three cues, each wired to a Claude Code hook:

| Cue | Plays when | Hook |
|---|---|---|
| `done` | Claude has finished and is waiting for you | `Stop` |
| `ask` | Claude asks a question, shows a plan, or needs a permission | `PreToolUse`, `Notification` |
| `fail` | the turn died on an API error | `StopFailure` |

The `done` cue is the one that needs judgment, because Claude Code fires `Stop` every time the
main loop goes idle, including when Claude is only parked and will carry on by itself:

- **It stays quiet while Claude is still working.** Background agents, workflows, monitors,
  scheduled wakeups, and a background shell doing work that ends (a render, a test run, a
  download, a wait loop) all mean Claude wakes up again without you. The chime waits for the
  stop after that.
- **It rings past anything that runs until you stop it.** A dev server, a file watcher, or a
  log tail never finishes, so Claude isn't waiting on it. If that is all that's left running,
  you get the chime. See [Server or work?](#server-or-work).

It also plays a question once (a question can reach the hooks twice, a few seconds apart),
and it repairs its own volume: dictation software turns other programs down while it listens,
and Windows remembers that level for a program that exits meanwhile, which would leave the
chime at 0% for good.

As a hook it can't get in Claude's way: it always exits 0, writes nothing to stdout, runs
`async`, and a ten-second watchdog ends it if a pipe or the sound device hangs.

## What it needs

Windows 10 or 11. Nothing to install: `build.cmd` uses the C# compiler that ships with
Windows (`%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe`), and playback goes through
Windows' own audio. It doesn't run on macOS or Linux.

## Installing

Run these in **PowerShell**, from the root of this repo.

### 1. Copy the files into `~/.claude/hooks/chime/`

```powershell
$chime = "$env:USERPROFILE\.claude\hooks\chime"
New-Item -ItemType Directory -Force $chime | Out-Null
Copy-Item chime-setup\chime.cs, chime-setup\build.cmd $chime -Force
Copy-Item chime-setup\sounds $chime -Recurse -Force
if (-not (Test-Path "$chime\chime.json")) { Copy-Item chime-setup\chime.json $chime }
```

Copy rather than pointing at the clone, so moving the repo doesn't break the hooks. The last
line leaves an existing `chime.json` alone, so running these again to update keeps your
settings.

### 2. Build it

```powershell
& "$chime\build.cmd"
```

It prints `built ...\chime.exe`. `BUILD FAILED` with a "being used by another process" error
means a session was playing a cue at that instant; run it again.

### 3. Hear it

```powershell
& "$chime\chime.exe" done
& "$chime\chime.exe" ask
& "$chime\chime.exe" fail
```

Run them one at a time: each returns at once and plays in the background. If one is silent,
read the last line of `$chime\chime.log`.

### 4. Add the hooks to `~/.claude/settings.json`

**Merge** these into the existing file. Don't replace the file, and if `hooks` already has a
`Stop`, `StopFailure`, `Notification` or `PreToolUse` list, add the entry to that list rather
than overwriting it. Replace `<you>` with the user's folder name; the path must be absolute,
with doubled backslashes.

```json
"hooks": {
  "Stop": [
    { "hooks": [ { "type": "command", "command": "C:\\Users\\<you>\\.claude\\hooks\\chime\\chime.exe", "args": ["done"], "async": true } ] }
  ],
  "StopFailure": [
    { "hooks": [ { "type": "command", "command": "C:\\Users\\<you>\\.claude\\hooks\\chime\\chime.exe", "args": ["fail"], "async": true } ] }
  ],
  "Notification": [
    {
      "matcher": "permission_prompt|elicitation_dialog|elicitation_url_dialog|agent_needs_input",
      "hooks": [ { "type": "command", "command": "C:\\Users\\<you>\\.claude\\hooks\\chime\\chime.exe", "args": ["ask"], "async": true } ]
    }
  ],
  "PreToolUse": [
    {
      "matcher": "AskUserQuestion|ExitPlanMode",
      "hooks": [ { "type": "command", "command": "C:\\Users\\<you>\\.claude\\hooks\\chime\\chime.exe", "args": ["ask"], "async": true } ]
    }
  ]
}
```

### 5. Verify

Send it three made-up `Stop` events. Use this function rather than `echo ... | chime.exe`:
the program has no console window, and a pipe from Git Bash never reaches it.

```powershell
function Send-Stop($tasks) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "$chime\chime.exe"; $psi.Arguments = "done"
  $psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true
  $p = [System.Diagnostics.Process]::Start($psi)
  $p.StandardInput.Write('{"session_id":"chime-test","cwd":"C:\\test","background_tasks":' + $tasks + ',"session_crons":[]}')
  $p.StandardInput.Close(); $p.WaitForExit()
}
Send-Stop '[{"id":"1","type":"shell","status":"running","command":"python render.py --all"}]'
Send-Stop '[{"id":"1","type":"shell","status":"running","command":"npm run dev"}]'
Send-Stop '[]'
Get-Content "$chime\chime.log" -Tail 3
```

The first is silent, the other two play, and the log ends with:

```
done   quiet, Claude carries on by itself (shell: python render.py --all)  session chime-te  in C:\test
done   played minimal/complete (left running: npm run dev)  session chime-te  in C:\test
done   played minimal/complete  session chime-te  in C:\test
```

Then tell the user the hooks take effect in their next Claude Code session.

## Settings

`chime.json`, beside the program. It's read on every call, so an edit takes effect on the next
cue with no rebuild.

| Key | Default | What it does |
|---|---|---|
| `pack` | `"minimal"` | Which folder of sounds to play from. `minimal` and `soft` ship here. |
| `cues` | `done` → `complete`, `ask` → `notification`, `fail` → `error` | Which sound file (without `.mp3`) each cue plays. |
| `soundsDir` | `""` | Where the pack folders are. Empty means the `sounds` folder beside the program. |
| `volume` | `100` | 0 to 100. |
| `quietWhileAgentsWork` | `true` | The master switch. `false` plays `done` at every stop, whatever is still running. |
| `quietWhile` | every kind | The kinds of background work that keep `done` quiet: `subagent`, `workflow`, `teammate`, `cloud session`, `shell`, `monitor`, `scheduled wakeup`. Remove one to stop waiting for it. |
| `runsUntilStopped` | `[]` | Your own patterns for commands that never finish, added to the built-in list. |
| `keepsWorking` | `[]` | Your own patterns for commands that always count as work, whatever the built-in list says. |

## Server or work?

When a stop arrives with a background shell still running, the chime reads that shell's
command line and decides which kind it is:

- **Runs until stopped**: `npm run dev`, `vite`, `uvicorn`, `flask run`, `python -m http.server`,
  anything with a `serve` subcommand, `--watch`, `tail -f`, `docker compose up`, a ComfyUI
  `main.py`, and so on. The chime doesn't wait for these.
- **Work that ends**: everything else. The chime waits.

A command made of several parts counts as a server if any part is one, because that is what
it becomes: `npm install && npm run dev` is a server. A stop with a server *and* a render
running stays quiet for the render.

The list is in `chime.cs` under `RunsUntilStopped`. It leans towards "server" on purpose:
ringing a little early is a smaller mistake than never ringing. To see how a command is
judged:

```powershell
& "$chime\chime.exe" judge npm run dev | Out-Host
```

```
rings  (runs until stopped, so the chime does not wait for it)  npm run dev
```

Keep the `| Out-Host`. Without a pipe PowerShell doesn't wait for a windowless program or
show what it prints. The verdict is written to `chime.log` either way. To judge several, pipe
them in, one per line: `"npm test", "tail -f app.log" | & "$chime\chime.exe" judge | Out-Host`.

When it gets one wrong, add a pattern to `chime.json`. Patterns are .NET regular expressions,
matched against the command line with case ignored, and in JSON each backslash is doubled:

```json
"runsUntilStopped": ["\\bmy-launcher\\.bat\\b"],
"keepsWorking": ["\\bserve-report\\b"]
```

`runsUntilStopped` is for a server of yours that the chime waited on and so never rang.
`keepsWorking` is for a job the chime took for a server and rang past. A pattern that doesn't
compile is skipped and named in the log.

## The log

`chime.log`, beside the program, has one line for every call: which cue, whether it played or
why it stayed quiet, and which session asked. It trims itself at about 200 KB.

```
done   played minimal/complete  session a1b2c3d4  in D:\work\site
done   quiet, Claude carries on by itself (workflow, shell: python tools/render.py --all)  session 9f8e7d6c  in D:\work\video
done   played minimal/complete (left running: npm run dev)  session a1b2c3d4  in D:\work\site
ask    played minimal/notification  session 5b6a7c8d  in D:\work\art
ask    quiet, already chimed for this a moment ago  session 5b6a7c8d  in D:\work\art
```

## Troubleshooting

- **No sound, and no new line in the log.** The hook isn't running. Check the path in
  `settings.json`, and start a new Claude Code session.
- **`no such sound: ...` in the log.** `pack` or a `cues` entry names a file that isn't in
  `soundsDir`.
- **Every line in the log says `done`, even for questions.** The cue isn't reaching the
  program, which falls back to `done`. Check that each hook entry in `settings.json` has its
  own `args`: `["ask"]` on the two question hooks, `["fail"]` on `StopFailure`.
- **`done` plays while a render is still going.** Run that command through `judge`. If it
  says `rings`, add a `keepsWorking` pattern. If the log line for that stop has no
  `left running`, Claude Code listed no background work for that stop, and the chime can only
  judge what it is told about: a job queued on a server with nothing waiting on it is
  invisible to it.
- **`done` never plays in a session with a server up.** `judge` the server's command, and if
  it says `quiet`, add a `runsUntilStopped` pattern. A monitor left watching the server keeps
  it quiet too: the log line says `(monitor)`, and removing `monitor` from `quietWhile` stops
  that.
- **Claude ends its turn on a plain-text question while a render is running, and nothing
  plays.** That's the rule above working as written: the `ask` cue covers permission prompts
  and question dialogs, not questions written into a reply.

## The sounds

The six files under `sounds/` come from [UI SFX](https://uisfx.com)
([romainsimon/uisfx](https://github.com/romainsimon/uisfx)) by Yuki Capital, whose audio is
dedicated to the public domain under CC0 1.0; the dedication is in
[`sounds/LICENSE-AUDIO`](sounds/LICENSE-AUDIO). The full set has twelve packs and many more
cues. To use it, clone that repo, set `soundsDir` to its `packages\uisfx\sounds` folder, and
pick a `pack`. Any folder of `.mp3` files laid out as `<soundsDir>\<pack>\<cue>.mp3` works.
