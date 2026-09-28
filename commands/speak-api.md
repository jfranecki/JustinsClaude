---
description: Summarize the previous response and speak it aloud via ElevenLabs v4, directed with expressive audio tags. Requires a voice flag (--m or --f). Length auto-scales to the response, or force it with --brief/--medium/--detailed. An optional personality argument shapes the wording and tag choice.
argument-hint: --m|--f [--brief|--medium|--detailed] [personality — empty uses the flag's default persona]
allowed-tools: Write, Bash
---

# /speak-api — ElevenLabs v4 narration

Speak your **most recent assistant message** aloud through the computer speakers, in the voice of the personality below, using ElevenLabs v4 with expressive audio tags applied inline.

## Arguments for this run

$ARGUMENTS

Parse the arguments as a **required voice flag**, an **optional length flag**, and an **optional personality** — the two flags may appear in either order, but both must precede the personality text.

### Voice flag — required

| Flag | Voice | Default persona |
|---|---|---|
| `--f` (also `--female`, `-f`) | female, Australian | a laid back, friendly young Australian girl |
| `--m` (also `--male`, `-m`) | male, British | a young, intelligent, professional British male — "Q" from James Bond |

Match these as **exact tokens** — there is no prefix matching, so `--m` is always the *male voice* and `--medium` is always the *length tier*. They can be combined freely (`/speak-api --m --medium`).

**If no voice flag is present**, reply once with exactly:

`/speak-api needs a voice: --f (female AU) or --m (male UK). Example: /speak-api --m --brief`

…and stop. Do not guess a voice, do not call ElevenLabs, and do not write any file.

### Length flag — optional

One of `--brief`, `--medium`, `--detailed`. If **no length flag** is given, the length is **auto** (Step 1 picks a tier to fit the response). Flags map to the tiers in Step 1.

### Personality — optional

Whatever text remains after removing both flags. If that is empty, use the default persona for the resolved voice flag:

- **`--f` default** — **a laid back, friendly young Australian girl**: warm and unfussed, gently melodic Aussie cadence (soft rising intonation, dropped 'r' sounds), casual Aussie lexicon — *yeah*, *for ya*, *heaps*, *no worries*, *reckon*, *give us a yell*, *she'll be right*, *mate* (sparingly).
- **`--m` default** — **a young, intelligent, professional British male — think "Q" from James Bond**: crisp received-pronunciation diction, dry wit, understated confidence, brisk-but-measured rhythm, occasional clipped Britishisms like *right then*, *rather*, *do call*, *indeed*.

An explicit personality **overrides** the default persona but never the voice — the flag still decides which vocal cords deliver it. Keep the personality plausible for the chosen voice (see Step 2, point 2).

### Worked parse examples

Strip **every** leading flag before reading the personality — the most common mistake is stripping only the first and leaving the second glued to the personality text.

| Input | Voice | Tier | Personality |
|---|---|---|---|
| `--m --medium gruff sailor` | male | medium | `gruff sailor` |
| `--medium --m gruff sailor` | male | medium | `gruff sailor` |
| `--f` | female | auto | *(default Aussie girl)* |
| `--m --brief` | male | brief | *(default "Q")* |
| `--f deadpan comedian` | female | auto | `deadpan comedian` |
| `--medium gruff sailor` | — | — | **error: no voice flag** |

Note rows 1–2: `--m` and `--medium` are *both* consumed as flags and neither leaks into the personality.

## Required setup (one-time)

Set your ElevenLabs API key — from https://elevenlabs.io → Profile → API Key — as an environment variable Claude Code's shell sessions will inherit:

**macOS / Linux** — add to `~/.zshrc` (or `~/.bashrc`), then `source` it or open a new terminal:

```sh
export ELEVENLABS_API_KEY="sk_..."
```

**Windows** — set it as a persistent user variable, then start a **new** Claude Code session (already-running sessions keep their old environment):

```powershell
[Environment]::SetEnvironmentVariable('ELEVENLABS_API_KEY', 'sk_...', 'User')
```

Also requires **`jq`** (`brew install jq` · `apt install jq` · `winget install jqlang.jq`) and an **audio player** — `afplay` is built into macOS; elsewhere the Step 4 block auto-detects `ffplay`, `mpv`, `mpg123`, or `cvlc`, and falls back to PowerShell on Windows. The two voice IDs and the model are set in the bash block below — change those lines to swap them.

---

## Procedure

### Step 1 — Compose the spoken text

Recall your **most recent assistant message** in this conversation (the turn immediately before `/speak-api` was invoked). Recast it as conversational spoken text **in the voice of the personality**. **How long it runs is set by the length tier** resolved from the arguments:

| Tier | Selected by | Target | Hard char ceiling* |
|---|---|---|---|
| **brief** | `--brief` | 2–4 sentences | 450 |
| **medium** | `--medium` | 5–9 sentences | 950 |
| **detailed** | `--detailed` | 10–16 sentences | 1800 |
| **auto** | *no length flag (default)* | scales to the source — see below | 1800 |

\*The ceiling is measured on the **final tagged text** (audio tags included — ElevenLabs bills per character).

**Auto (the default):** pick the *smallest* tier that still carries **every distinct, useful point** in the source. A short or simple reply → brief. A long, information-dense reply → expand toward detailed. Let length track the content; never pad to fill a budget, and never exceed the detailed ceiling.

Rules:
- Spoken English only. No lists, no code fences, no markdown formatting characters.
- **Condense, don't amputate.** Preserve each distinct fact, decision, number, and outcome as its own beat — do **not** collapse several separate points into one just to hit a lower sentence count. This is the whole point of the tiers: dense input is *allowed* to produce a longer read.
- Strip code blocks, file paths, tool output, and other typed-only content before re-casting.
- **Stay in character.** A "laid back girl" says *"okay so I just..."*; a "gruff sailor" says *"aye, the deed's done"*; a "deadpan comic" says *"well, that happened."* Lexicon, rhythm, and word choice must reflect the personality.
- **Respect the ceiling.** If the source has more worthwhile points than fit under the tier's char ceiling, keep the highest-value ones and add a brief "there's more if you want it" rather than overflow. The bash block in Step 4 will refuse to send anything over 1800 chars.
- If the previous response was already a single conversational sentence, lightly re-cast it in the personality (brief) regardless of tier — don't pad it out.

If there is no prior assistant message (this is the first turn), reply once with `Nothing to speak yet — invoke /speak-api after I've responded.` and stop.

### Step 2 — Direct the read with v4 audio tags

Audio tags are how you direct the performance, and v4 takes direction far better than v3 did: it follows each tag, and each run of tags, closely enough that **the delivery you describe is the delivery you get.** That cuts both ways. A vague tag gets a generic read, and a tag on every clause risks an over-acted one. Direct like a voice director: say exactly how a line should land, at the moments that matter, and let the writing carry the rest.

**How v4 reads a script — four things decide whether a read lands:**

1. **Tags are natural-language direction, not a fixed list.** v4 *interprets* whatever is inside `[...]` as a stage direction and performs it; the bracket text is never spoken aloud. One word works (`[sighs]`, `[whispers]`), but v4's real strength is a short phrase that says precisely how the line should land: `[dry, quietly pleased with himself]`, `[said slowly, like explaining it to a child]`, `[barely holding back a laugh]`, `[warming to the idea]`. ElevenLabs' own examples go as far as `[said angrily in French accent]`. When the difference matters, prefer the specific phrase over the generic emotion word (`[relieved, but trying to play it cool]` over `[relieved]`). Keep phrases to a clause, not a paragraph: they're billed like everything else.
2. **v4 reads the words, not just the tags.** It infers emotion from the text around a tag (word choice, punctuation, what came before) and is most reliable when tag and line agree. So write lines that already carry their mood (*"Oh, it actually WORKED."* needs no `[surprised]`), and spend tags on what the words can't say: a laugh, a sigh, a pause, a shift in energy, a change of intent. A tag that fights its line loses; `[whispering]` on a line written as a shout won't land.
3. **Tags are voice-dependent — keep them in the persona's lane.** ElevenLabs' own guidance: *"some tags work well with certain voices while others may not,"* and the voice you pick matters more than any tag. A dry, crisp voice can do `[wry]`, `[clipped]`, `[amused]`, `[conspiratorially]`; it will *not* convincingly do `[sobbing]` or `[manic screaming]`. Choose tags the chosen voice would actually produce, and don't whiplash between registers unless the content truly turns. This applies doubly here: the `--m` and `--f` voices have different ranges, so tag for the one the flag selected.
4. **There are only two dials, and no SSML.** v4 takes just **Stability** and **Similarity**. It has no Style or Speed setting, and SSML such as `<break time="1s"/>` isn't supported, so pace and pauses come from tags and punctuation (`[slows down]`, `[rapid-fire]`, `[pause]`, `…`). The Step 4 block sends `STABILITY=0.0`, the most expressive end: tags hit hardest and emotion swings widest, occasionally at the cost of slight voice drift. If a particular voice drifts, nudge that one line up toward `0.5`, which holds the voice's identity tighter while v4 still follows the tags; near `1.0` the read is steady but least responsive to direction, so never go there when tags are the point. `similarity_boost` (0.75) sets how closely the output sticks to the chosen voice.

**Density — direct the turns, don't decorate every clause.** Because v4 performs every tag it's given, the v3 habit of two or three tags per sentence now tends to over-act. Tag where the performance *changes*:

- **Open** with one tag, often a phrase, that fixes the persona's tone and energy: `[relaxed and cheerful]` · `[crisp, measured]`.
- **Turn** with a tag at each shift: a punchline, a reveal, a relief, bad news after good. A non-verbal or a pause usually does it.
- **Land** the close with a tag matching the final emotion, so the read doesn't flatten at the end.

That works out to about a tag every sentence or two. A line whose words already carry its mood can go untagged. ElevenLabs **bills per character and tags count**, so every tag should change how a line *sounds*; under a tight tier, spend the budget on the ones that earn it.

**Sequences choreograph a beat.** v4 follows adjacent tags in order, so two or three can stage a small moment: `[sighs] [short pause] [warmly] Right, here's the good bit.` Never stack tags that fight each other (`[whispering][shouting]`).

**The palette** — inline, **lowercase**, square brackets. This is a deep menu, not a checklist and not a whitelist: combine tags, grade them, and coin your own. Every category below also works as the seed of a phrase: `[sighs]` becomes `[sighs, half amused]`, `[slowly]` becomes `[slowly, savouring it]`.

**Phrase directions** (v4's headline: describe the delivery in a few words, and it's followed closely):
`[said with a grin]` `[dry, quietly pleased with himself]` `[relieved, but trying to play it cool]` `[barely holding back a laugh]` `[warming to the idea]` `[mock-serious]` `[said slowly, like explaining it to a child]` `[half to herself]` `[leaning in, conspiratorial]` `[suddenly all business]` `[with exaggerated patience]` `[like it's the best news all week]` `[trying not to sound smug]` `[matter-of-fact, then a small laugh]`

**Emotion / tone** (the workhorse — anchor the opening and each turn with one):
`[happy]` `[joyful]` `[cheerful]` `[delighted]` `[content]` `[optimistic]` `[hopeful]` `[grateful]` `[relieved]` `[warm]` `[affectionate]` `[tender]` `[excited]` `[eager]` `[enthusiastic]` `[giddy]` `[playful]` `[amused]` `[mischievous]` `[proud]` `[triumphant]` `[confident]` `[determined]` `[smug]` `[reassuring]` `[sincere]` `[earnest]` `[calm]` `[gentle]` `[soothing]` `[reflective]` `[wistful]` `[nostalgic]` `[bittersweet]` `[melancholic]` `[sad]` `[sorrowful]` `[lonely]` `[regretful]` `[disappointed]` `[resigned]` `[longing]` `[yearning]` `[annoyed]` `[irritated]` `[frustrated]` `[indignant]` `[angry]` `[furious]` `[bitter]` `[jealous]` `[sarcastic]` `[dry]` `[wry]` `[cynical]` `[skeptical]` `[dismissive]` `[suspicious]` `[wary]` `[uneasy]` `[tense]` `[anxious]` `[nervous]` `[worried]` `[fearful]` `[panicked]` `[shocked]` `[surprised]` `[awe]` `[amazed]` `[confused]` `[bewildered]` `[curious]` `[inquisitive]` `[intrigued]` `[thoughtful]` `[pensive]` `[contemplative]` `[serious]` `[grave]` `[solemn]` `[embarrassed]` `[sheepish]` `[ashamed]` `[guilty]` `[tired]` `[bored]` `[exasperated]`

**Intensity & compound** (grade or blend an emotion — proof the vocabulary is open; coin more like these):
`[slightly nervous]` `[barely excited]` `[quietly emotional]` `[barely holding back anger]` `[deeply sorrowful]` `[overjoyed]` `[visibly shaken]` `[masking fear]` `[forced calm]` `[bursting with excitement]` `[out of breath]` `[exhausted voice]` `[in pain]`

**Direction / manner** (adverbial stage directions — drop them mid-sentence):
`[cheerfully]` `[warmly]` `[gently]` `[softly]` `[quietly]` `[tenderly]` `[playfully]` `[teasingly]` `[mischievously]` `[slyly]` `[conspiratorially]` `[knowingly]` `[matter-of-factly]` `[flatly]` `[deadpan]` `[dryly]` `[dry tone]` `[understated]` `[sarcastically]` `[reluctantly]` `[hesitantly]` `[nervously]` `[cautiously]` `[politely]` `[firmly]` `[assertively]` `[commanding tone]` `[emphatically]` `[earnestly]` `[convincingly]` `[passionately]` `[urgently]` `[breathlessly]` `[wistfully]` `[grimly]` `[coldly]` `[sharply]` `[curtly]` `[brightly]` `[excitedly]` `[reassuringly]` `[apologetically]` `[proudly]` `[smugly]` `[suddenly serious]` `[trailing off]`

**Word emphasis** (pairs with CAPS on the spoken word):
`[emphasized]` `[strong emphasis]` `[soft emphasis]` `[stress on next word]` `[repeats for emphasis]`

**Non-verbal reactions** (the voice's punctuation — one at a natural break beats three in a row):
`[laughs]` `[laughs softly]` `[laughs loudly]` `[laughs harder]` `[starts laughing]` `[giggles]` `[chuckles]` `[light chuckle]` `[wry laugh]` `[nervous laugh]` `[snorts]` `[cackles]` `[scoffs]` `[sighs]` `[heavy sigh]` `[sigh of relief]` `[exhales]` `[deep breath]` `[sharp inhale]` `[exhale slowly]` `[nervous breath]` `[breath catches]` `[breath trembles]` `[breathing heavily]` `[gasps]` `[gasps in disbelief]` `[taken aback]` `[gulps]` `[swallows]` `[clears throat]` `[lips smack]` `[clicks tongue]` `[sniffs]` `[hums]` `[groans]` `[grunts]` `[growls]` `[whimpers]` `[mutters]` `[yawns]` `[crying]` `[choking up]` `[hmm]` `[mhm]` `[uh-huh]` `[aha]` `[ooh]` `[ohh]` `[ahh]` `[oh]` `[uh-oh]` `[pfft]` `[tsk]` `[whistles]`

**Volume / energy**:
`[natural tone]` `[casual tone]` `[conversational tone]` `[whispering]` `[whispers]` `[intimate whisper]` `[breathy]` `[soft]` `[quiet]` `[hushed tone]` `[muttering]` `[murmuring]` `[mumbling]` `[subdued]` `[mellow]` `[low energy]` `[relaxed]` `[measured]` `[normal]` `[clear]` `[projected]` `[animated]` `[energetic]` `[energetically]` `[high energy]` `[loud]` `[loudly]` `[calling out]` `[raised voice]` `[shouting]` `[yelling]` `[booming]` `[intense]` `[forceful]` `[emphatic]` `[hoarse]` `[gruff]` `[strained]`

**Voice modulation & shifts** (mid-line changes — powerful; use one right at the turn):
`[voice rising]` `[voice lowering]` `[voice softens]` `[voice cracks]` `[voice trembling]` `[voice trembling with emotion]` `[breaking emotionally]` `[voice close to microphone]` `[suddenly excited]` `[tone darkens]` `[anger building]` `[becoming emotional]` `[realization dawning]`

**Pace / rhythm / pauses**:
`[slowly]` `[slow and deliberate]` `[drawn out]` `[leisurely]` `[measured]` `[deliberate]` `[steady]` `[slows down]` `[picks up pace]` `[pause]` `[brief pause]` `[short pause]` `[long pause]` `[after a moment]` `[after a long pause]` `[beat]` `[dramatic pause]` `[awkward silence]` `[stunned silence]` `[hesitates]` `[stammers]` `[stutters]` `[stumbling over words]` `[rushed]` `[hurried]` `[quickly]` `[rapid-fire]` `[speaks between breaths]` `[interrupting]` `[cuts in]` `[overlapping]` `[cuts off]` `[cuts sentence short]` `[trails off]` `[staccato]`

**Conversational realism** (thinking and self-talk — great for an unscripted, human feel):
`[thinking]` `[muttering to self]` `[searching for words]` `[hesitates nervously]` `[leans closer]` `[steps back slightly]`

**Accents & dialects** (v4 holds an accent much harder than v3 did while keeping the voice's identity under it, so one tag at the top recolors the *whole* read. Use one only when the personality asks for an accent the voice doesn't already have. Never add one for the default personas: their voices already carry the accent, and a tag only exaggerates it):
`[american accent]` `[british accent]` `[australian accent]` `[canadian accent]` `[irish accent]` `[scottish accent]` `[indian english]` `[southern US accent]` `[new york accent]` `[midwestern accent]` `[french accent]` `[german accent]` `[italian accent]` `[spanish accent]` `[russian accent]` `[strong X accent]` *(swap in X)* `[pirate accent]` `[medieval accent]`

**Character, age & narration voices** (these recolor the *entire* read — reserve for when the persona genuinely calls for it; they rarely fit a quick status summary):
`[childlike tone]` `[teenager tone]` `[young adult voice]` `[middle-aged tone]` `[elderly voice]` `[old man voice]` · `[heroic voice]` `[wise mentor voice]` `[villain voice]` `[evil scientist voice]` `[storyteller voice]` `[news reporter voice]` `[radio host voice]` `[teacher voice]` · `[knight voice]` `[royal voice]` `[pirate voice]` `[dragon narrator]` · `[robotic tone]` `[sci-fi AI voice]` `[hologram voice]` `[cybernetic voice]` · `[documentary narrator]` `[audiobook narrator]` `[epic narrator]` `[fantasy narrator]` `[narrating]` `[announcer voice]` `[grand narration]` `[epic cinematic tone]` · `[classic film noir]` `[thriller narrator]` `[horror whisper]` `[ominous tone]` `[dramatic reveal]` `[comedic narration]` · `[commercial voice]` `[enthusiastic ad voice]` `[luxury brand voice]` `[corporate presentation tone]` · `[singing]` `[singing softly]` · `[soft conclusion]` `[hopeful ending]` `[quiet reflection]`

**Sound effects** (v4 renders these inline and follows them more reliably than v3 did — still a rare flourish when the content invites it, never decoration; one per read at most):
`[applause]` `[clapping]` `[laughter]` `[gunshot]` `[explosion]` `[door slams]` `[footsteps]` `[phone ringing]` `[phone buzzing]` `[static]` `[wind]` `[light rain]` `[thunder]`

**Punctuation & CAPS are expressive controls too — they compound with tags:**
- **Ellipses `…`** → pauses, hesitation, trailing off: *"Well… that's one way to do it."*
- **CAPITALS on a word** → emphasis / extra volume on *that word*: *"That is NOT what I expected."* (This is exactly why tags are lowercase — caps stay reserved for emphasising spoken words.)
- **Em-dash `—`** → a sharp break or self-interruption; commas and periods set the baseline rhythm.
- **`?` / `!`** → lift and intonation; don't bury an excited line under a flat period.

(Still: spoken prose only — no markdown, no lists, no code, no file paths in the spoken text.)

*Tag reference: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4 · https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices*

**Examples** — note where the tags sit (the open, each turn, the close), the phrase directions doing work a single word can't, the lines left untagged because their words already carry the mood, and how `…` and CAPS pull extra weight:

**"stoic gruff sailor":**

> [gruff, low and unhurried] Aye. The deed's done. [heavy sigh] Took some rough seas getting her there… [firmly] but she's holdin' water. Sing out if she lists.

**"deadpan dry comedian":**

> [deadpan] Great news. I did the thing. [beat] It worked. [pause] [flatly, not remotely convinced] Probably.

**`--f` default — "laid back friendly Australian girl":**

> [relaxed and cheerful] Yeah, so — got that all sorted for ya. [giggles] Honestly came together HEAPS cleaner than I reckoned… everything's hooked up beautiful. [warmly] Just give us a yell if you wanna tweak anything, yeah?

**`--m` default — "Q from James Bond":**

> [crisp, quietly pleased with himself] Right then. The kit's wired and humming along nicely. [short pause] Cleaner integration than I'd anticipated, in fact — rather pleased with it. [dryly] Do call if anything wants tweaking. [amused] Mm.

### Step 3 — Write the tagged summary to disk

Write the fully tagged summary — and **nothing else** (no preamble, no markdown, no surrounding quotes) — to the temp file below using the **Write** tool. The Write tool needs a **platform-absolute** path:

| Platform | Path to write |
|---|---|
| macOS / Linux | `/tmp/claude_speak_api_input.txt` |
| Windows | `%LOCALAPPDATA%\Temp\claude_speak_api_input.txt` — expand it, e.g. `C:\Users\<you>\AppData\Local\Temp\claude_speak_api_input.txt` |

On Windows that path is the *same file* Git Bash sees as `/tmp/claude_speak_api_input.txt` (confirm with `cygpath -w /tmp` if your setup differs). Step 4 resolves it either way.

### Step 4 — Send to ElevenLabs and play

**Set the Bash tool's `timeout` parameter to `600000` on this call.** This is required, not
optional. Every player in the fallback chain below blocks for the full length of the audio
— `afplay`, `ffplay`, `mpv`, `mpg123`, `cvlc`, and the PowerShell fallback all wait out the
read — so the tool call must outlast it, and the Bash tool defaults to only **120 seconds**.
At roughly 15.7 characters of tagged text per second of speech, the tiers land like this:

| Tier | Char cap | Audio length | Margin under the 120s default |
|---|---|---|---|
| `--brief` | 450 | ~30s | comfortable |
| `--medium` | 950 | ~60s | comfortable |
| `--detailed` | 1800 | ~115s | **~5 seconds — razor thin** |

A `--detailed` read sits within a few seconds of the default, so ordinary variance cuts it
off mid-sentence — and the audio is generated and billed in full before playback truncates,
so you pay for seconds you never hear. More importantly, if `ABS_MAX_CHARS` or the tier
caps are ever raised, the default starts silently truncating every long read. `600000` is
the tool's maximum and covers any ceiling this command could reasonably use.

Replace `UNSET` on the marked `VOICE=` line with `f` or `m` to match the flag resolved in Step 1, then run the block as written. There is deliberately **no default** — left as `UNSET` the block aborts rather than guessing a voice:

```bash
set -euo pipefail

# ── Replace UNSET with f or m to match the flag from Step 1 ─────────────
VOICE=UNSET
# ── Left as UNSET this block aborts by design — never guess a voice. ────
# Voice IDs — change these to swap voices (browse: https://elevenlabs.io/app/voice-library).
VOICE_ID_F="u8ADrbquiJqufR9XMtb8"   # laid back friendly Australian girl
VOICE_ID_M="lF0PpOQjCl3K89rt0U83"   # young professional British male ("Q")

# Model — eleven_v4 is the most expressive. eleven_v4_turbo is faster and costs about half
# the credits per character, with less range.
MODEL_ID="eleven_v4"
# Lower is more expressive and follows tags hardest; 0.5 holds the voice tighter if a read drifts.
STABILITY=0.0

case "$VOICE" in
  f) VOICE_ID="$VOICE_ID_F" ;;
  m) VOICE_ID="$VOICE_ID_M" ;;
  *) echo "VOICE must be 'f' or 'm' (got '$VOICE')." >&2; exit 1 ;;
esac

: "${ELEVENLABS_API_KEY:?ELEVENLABS_API_KEY is not set — see 'Required setup' in this command. On Windows, set it for the User scope and start a NEW Claude Code session.}"
command -v jq >/dev/null || { echo "jq is required — brew install jq / apt install jq / winget install jqlang.jq" >&2; exit 1; }

# Resolve the input file written in Step 3 (Windows temp differs from /tmp on some setups).
IN=/tmp/claude_speak_api_input.txt
if [ ! -s "$IN" ] && [ -n "${LOCALAPPDATA:-}" ]; then
  ALT="$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || echo "")/Temp/claude_speak_api_input.txt"
  if [ -s "$ALT" ]; then IN="$ALT"; fi
fi
OUT="$(dirname "$IN")/claude_speak_api_output.mp3"

[ -s "$IN" ] || { echo "Input file $IN is empty or missing — did Step 3 write it?" >&2; exit 1; }

# Hard credit backstop — ElevenLabs bills per character (audio tags count too).
# Refuse to send anything longer than the detailed-tier ceiling, regardless of tier.
ABS_MAX_CHARS=1800
CHARS=$(wc -m < "$IN" | tr -d '[:space:]')
if [ "$CHARS" -gt "$ABS_MAX_CHARS" ]; then
  echo "Refusing to send: input is ${CHARS} characters, over the ${ABS_MAX_CHARS}-char credit cap." >&2
  echo "Re-run with --brief or --medium, or raise ABS_MAX_CHARS below if this was intentional." >&2
  exit 1
fi

# Build the JSON payload from the input text (jq -Rs handles all escaping) and send it
# through stdin with non-ASCII escaped (jq -a). Passed as a curl argument instead, an
# em-dash or ellipsis reaches ElevenLabs as invalid UTF-8 on Windows (HTTP 400).
# v4 takes only stability and similarity_boost; it has no style or speed setting.
HTTP=$(jq -a -Rs --arg model "$MODEL_ID" --argjson stab "$STABILITY" '{
  text: .,
  model_id: $model,
  voice_settings: {
    stability: $stab,
    similarity_boost: 0.75
  }
}' < "$IN" | curl -sS -o "$OUT" -w '%{http_code}' -X POST \
  "https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/mpeg" \
  --data-binary @-)

if [ "$HTTP" != "200" ]; then
  echo "ElevenLabs returned HTTP $HTTP. Body:" >&2
  cat "$OUT" >&2
  exit 1
fi

if ! file "$OUT" | grep -qiE 'audio|mpeg|mp3'; then
  echo "Response was not audio. Body:" >&2
  cat "$OUT" >&2
  exit 1
fi

# Print the read length before blocking on it. If playback ever is cut short, this line
# makes it obvious from the transcript (audio longer than the call) instead of looking
# like a silent failure. Non-fatal on any platform that has neither tool.
afinfo "$OUT" 2>/dev/null | grep -i 'estimated duration' \
  || ffprobe -v error -show_entries format=duration -of default=nw=1 "$OUT" 2>/dev/null \
  || true

# Play it — first available player wins (macOS → cross-platform → Windows fallback).
if command -v afplay >/dev/null 2>&1; then
  afplay "$OUT"
elif command -v ffplay >/dev/null 2>&1; then
  ffplay -nodisp -autoexit -loglevel error "$OUT"
elif command -v mpv >/dev/null 2>&1; then
  mpv --really-quiet --no-video "$OUT"
elif command -v mpg123 >/dev/null 2>&1; then
  mpg123 -q "$OUT"
elif command -v cvlc >/dev/null 2>&1; then
  cvlc --play-and-exit --intf dummy "$OUT" >/dev/null 2>&1
elif command -v powershell.exe >/dev/null 2>&1; then
  WIN_OUT="$(cygpath -w "$OUT" 2>/dev/null || echo "$OUT")"
  powershell.exe -NoProfile -Command "
    Add-Type -AssemblyName presentationCore
    \$p = New-Object System.Windows.Media.MediaPlayer
    \$p.Open([uri]'$WIN_OUT'); Start-Sleep -Milliseconds 700
    \$d = \$p.NaturalDuration; if (\$d.HasTimeSpan) { \$p.Play(); Start-Sleep -Seconds ([int]\$d.TimeSpan.TotalSeconds + 1) }
    \$p.Close()"
else
  echo "No audio player found. Install ffmpeg (ffplay), mpv, or mpg123. Audio saved at: $OUT" >&2
  exit 1
fi
```

### Step 5 — Confirm

After playback returns, reply with **one short line** confirming playback and naming the personality voice **and the length tier** used (e.g. `Spoken as: Q from James Bond · auto→medium.` or `Spoken as: laid back friendly girl · brief.`). Do **not** re-display the summary or the tagged text — the user heard it.
