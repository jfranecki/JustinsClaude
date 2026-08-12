---
description: Summarize the previous response and speak it aloud via ElevenLabs v3 with expressive audio tags. Length auto-scales to the response, or force it with --brief/--medium/--detailed. An optional personality argument shapes the wording and tag choice; defaults to a laid back and friendly Australian girl.
argument-hint: [--brief|--medium|--detailed] [personality — empty defaults to laid back friendly Australian girl]
allowed-tools: Write, Bash
---

# /speak-api-f — ElevenLabs v3 narration

Speak your **most recent assistant message** aloud through the computer speakers, in the voice of the personality below, using ElevenLabs v3 with expressive audio tags applied inline.

## Arguments for this run

$ARGUMENTS

Parse the arguments as an **optional leading length flag** followed by an **optional personality**:

- **Length flag** — one of `--brief`, `--medium`, `--detailed` if present (it will be the first token). Strip it before reading the personality. If **no flag** is given, the length is **auto** (Step 1 picks a tier to fit the response). Flags map to the tiers in Step 1.
- **Personality** — whatever text remains after removing any flag. If that is empty, default to **a laid back, friendly young Australian girl**: warm and unfussed, gently melodic Aussie cadence (soft rising intonation, dropped 'r' sounds), casual Aussie lexicon — *yeah*, *for ya*, *heaps*, *no worries*, *reckon*, *give us a yell*, *she'll be right*, *mate* (sparingly).

## Required setup (one-time)

Export your ElevenLabs API key in `~/.zshrc`:

```sh
export ELEVENLABS_API_KEY="sk_..."         # from https://elevenlabs.io → Profile → API Key
```

After editing `~/.zshrc`, either `source ~/.zshrc` or open a new terminal so Claude Code's bash sessions inherit the value. The voice ID is hardcoded in the bash block below — change that one line if you ever want to swap voices.

Also requires `jq` (`brew install jq` if missing). `afplay` is built into macOS.

---

## Procedure

### Step 1 — Compose the spoken text

Recall your **most recent assistant message** in this conversation (the turn immediately before `/speak-api-f` was invoked). Recast it as conversational spoken text **in the voice of the personality**. **How long it runs is set by the length tier** resolved from the arguments:

| Tier | Selected by | Target | Hard char ceiling* |
|---|---|---|---|
| **brief** | `--brief` | 2–4 sentences | 450 |
| **medium** | `--medium` | 5–9 sentences | 950 |
| **detailed** | `--detailed` | 10–16 sentences | 1800 |
| **auto** | *no flag (default)* | scales to the source — see below | 1800 |

\*The ceiling is measured on the **final tagged text** (audio tags included — ElevenLabs bills per character).

**Auto (the default):** pick the *smallest* tier that still carries **every distinct, useful point** in the source. A short or simple reply → brief. A long, information-dense reply → expand toward detailed. Let length track the content; never pad to fill a budget, and never exceed the detailed ceiling.

Rules:
- Spoken English only. No lists, no code fences, no markdown formatting characters.
- **Condense, don't amputate.** Preserve each distinct fact, decision, number, and outcome as its own beat — do **not** collapse several separate points into one just to hit a lower sentence count. This is the whole point of the tiers: dense input is *allowed* to produce a longer read.
- Strip code blocks, file paths, tool output, and other typed-only content before re-casting.
- **Stay in character.** A "laid back girl" says *"okay so I just..."*; a "gruff sailor" says *"aye, the deed's done"*; a "deadpan comic" says *"well, that happened."* Lexicon, rhythm, and word choice must reflect the personality.
- **Respect the ceiling.** If the source has more worthwhile points than fit under the tier's char ceiling, keep the highest-value ones and add a brief "there's more if you want it" rather than overflow. The bash block in Step 4 will refuse to send anything over 1800 chars.
- If the previous response was already a single conversational sentence, lightly re-cast it in the personality (brief) regardless of tier — don't pad it out.

If there is no prior assistant message (this is the first turn), reply once with `Nothing to speak yet — invoke /speak-api-f after I've responded.` and stop.

### Step 2 — Apply ElevenLabs v3 audio tags

Audio tags are the heart of an expressive v3 read — **lean on them heavily.** A summary carrying a tag in almost every sentence sounds like a *person*; one with a tag every few sentences sounds like a robot reading a memo. This step is where the quality comes from, so tag generously and deliberately.

**How v3 actually reads tags — three things decide whether a tag lands:**

1. **The vocabulary is open, not a fixed list.** v3 *interprets* the words inside `[...]` as stage directions and performs them — the bracket text is never spoken aloud. So the palette below is a launch pad, not a whitelist: if you can describe a delivery in two or three words, you can tag it — `[muttering under their breath]`, `[barely holding back a grin]`, `[suddenly serious]`, `[warming to the idea]` all work. Invent apt tags freely.
2. **Tags are voice-dependent — keep them in the persona's lane.** ElevenLabs' own guidance: *"some tags work well with certain voices while others may not,"* and the voice you pick matters more than any tag. A dry, crisp voice can `[wry]`, `[clipped]`, `[amused]`, `[conspiratorial]`; it will *not* convincingly `[sobbing]` or `[manic screaming]`. Choose tags the chosen voice would actually produce, and don't whiplash between registers unless the content truly turns.
3. **Stability sets how hard tags hit.** This script sends `stability: 0.0` = **Creative** — the most expressive setting, so tags land hard and emotion swings wide (occasionally at the cost of slight voice drift). `0.5` = **Natural** reins that in, holding the voice's identity more tightly while still performing the cues. `1.0` = **Robust** is the steadiest read but the *least responsive to tags* — never use it when tags are the point. Creative is the default here because expressive tagging is the whole point of this command; if a particular voice drifts too much, nudge the one `stability:` line in Step 4 up toward Natural.

   v3 is also most consistent on prompts longer than **~250 characters**; very short briefs read flatter and skip tags more often — an accepted trade for speed, but a reason not to over-trim.

**Density — be frequent, but make each tag earn its place.** Aim for **at least one tag in almost every sentence, often two or three**: open on a tone/emotion, punctuate the middle with a non-verbal or a pause, resolve on the closing mood. Two limits only — (a) never stack tags that fight each other (`[whispering][shouting]`), and (b) ElevenLabs **bills per character and tags count**, so a tag should change how a line *sounds*, not just decorate it; under a tight tier, spend the budget on tags that earn it.

**The palette** — inline, **lowercase**, square brackets. This is a deep menu, not a checklist: combine tags, grade them, and invent your own — compounds like `[barely holding back anger]`, `[whispers in shock]`, and `[voice trembling with emotion]` work *precisely because* the vocabulary is open.

**Emotion / tone** (the workhorse — anchor most sentences with one):
`[happy]` `[joyful]` `[cheerful]` `[delighted]` `[content]` `[optimistic]` `[hopeful]` `[grateful]` `[relieved]` `[warm]` `[affectionate]` `[tender]` `[excited]` `[eager]` `[enthusiastic]` `[giddy]` `[playful]` `[amused]` `[mischievous]` `[proud]` `[triumphant]` `[confident]` `[determined]` `[smug]` `[reassuring]` `[sincere]` `[earnest]` `[calm]` `[gentle]` `[soothing]` `[reflective]` `[wistful]` `[nostalgic]` `[bittersweet]` `[melancholic]` `[sad]` `[sorrowful]` `[lonely]` `[regretful]` `[disappointed]` `[resigned]` `[longing]` `[yearning]` `[annoyed]` `[irritated]` `[frustrated]` `[indignant]` `[angry]` `[furious]` `[bitter]` `[jealous]` `[sarcastic]` `[dry]` `[wry]` `[cynical]` `[skeptical]` `[dismissive]` `[suspicious]` `[wary]` `[uneasy]` `[tense]` `[anxious]` `[nervous]` `[worried]` `[fearful]` `[panicked]` `[shocked]` `[surprised]` `[awe]` `[amazed]` `[confused]` `[bewildered]` `[curious]` `[inquisitive]` `[intrigued]` `[thoughtful]` `[pensive]` `[contemplative]` `[serious]` `[grave]` `[solemn]` `[embarrassed]` `[sheepish]` `[ashamed]` `[guilty]` `[tired]` `[bored]` `[exasperated]`

**Intensity & compound** (grade or blend an emotion — proof the vocabulary is open; coin more like these):
`[slightly nervous]` `[barely excited]` `[quietly emotional]` `[barely holding back anger]` `[deeply sorrowful]` `[overjoyed]` `[visibly shaken]` `[masking fear]` `[forced calm]` `[bursting with excitement]` `[out of breath]` `[exhausted voice]` `[in pain]`

**Direction / manner** (adverbial stage directions v3 reads especially well — drop them mid-sentence):
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

**Accents & dialects** (one tag recolors the *whole* read — use sparingly, and only if the voice can carry it):
`[american accent]` `[british accent]` `[australian accent]` `[canadian accent]` `[irish accent]` `[scottish accent]` `[indian english]` `[southern US accent]` `[new york accent]` `[midwestern accent]` `[french accent]` `[german accent]` `[italian accent]` `[spanish accent]` `[russian accent]` `[strong X accent]` *(swap in X)* `[pirate accent]` `[medieval accent]`

**Character, age & narration voices** (these recolor the *entire* read — reserve for when the persona genuinely calls for it; they rarely fit a quick status summary):
`[childlike tone]` `[teenager tone]` `[young adult voice]` `[middle-aged tone]` `[elderly voice]` `[old man voice]` · `[heroic voice]` `[wise mentor voice]` `[villain voice]` `[evil scientist voice]` `[storyteller voice]` `[news reporter voice]` `[radio host voice]` `[teacher voice]` · `[knight voice]` `[royal voice]` `[pirate voice]` `[dragon narrator]` · `[robotic tone]` `[sci-fi AI voice]` `[hologram voice]` `[cybernetic voice]` · `[documentary narrator]` `[audiobook narrator]` `[epic narrator]` `[fantasy narrator]` `[narrating]` `[announcer voice]` `[grand narration]` `[epic cinematic tone]` · `[classic film noir]` `[thriller narrator]` `[horror whisper]` `[ominous tone]` `[dramatic reveal]` `[comedic narration]` · `[commercial voice]` `[enthusiastic ad voice]` `[luxury brand voice]` `[corporate presentation tone]` · `[singing]` `[singing softly]` · `[soft conclusion]` `[hopeful ending]` `[quiet reflection]`

**Sound effects** (v3 can render these inline — a rare flourish when the content invites it, never decoration):
`[applause]` `[clapping]` `[laughter]` `[gunshot]` `[explosion]` `[door slams]` `[footsteps]` `[phone ringing]` `[static]` `[wind]` `[thunder]`

**Punctuation & CAPS are expressive controls too — they compound with tags:**
- **Ellipses `…`** → pauses, hesitation, trailing off: *"Well… that's one way to do it."*
- **CAPITALS on a word** → emphasis / extra volume on *that word*: *"That is NOT what I expected."* (This is exactly why tags are lowercase — caps stay reserved for emphasising spoken words.)
- **Em-dash `—`** → a sharp break or self-interruption; commas and periods set the baseline rhythm.
- **`?` / `!`** → lift and intonation; don't bury an excited line under a flat period.

(Still: spoken prose only — no markdown, no lists, no code, no file paths in the spoken text.)

**Placement, in practice:**
- **Open** with a tone + energy pairing that fixes the persona: `[confident][measured]` · `[cheerful][relaxed]`.
- **Stack** adjacent, non-conflicting tags for a layered beat: `[gentle][soft] Hey, you.`
- **Break** on thought-shifts with a non-verbal or a pause — before a punchline, after a reveal, on a relief.
- **Resolve** with a tag matching the final emotion so the read doesn't flatten at the end.

*Tag reference: https://elevenlabs.io/blog/v3-audiotags · https://elevenlabs.io/docs/best-practices/prompting/eleven-v3*

**Examples** — note the density (a tag roughly every sentence or clause), the lowercase tags, and how `…` and CAPS pull extra weight:

**"stoic gruff sailor":**

> [gruff][low energy] Aye. The deed's done. [heavy sigh] [beat] Took some rough seas — [measured] but she's holdin' water. [firmly] Sing out if she lists.

**"deadpan dry comedian":**

> [deadpan][flatly] Great news. [short pause] I did the thing. [dry] [wry laugh] It worked. [beat] [skeptical] Probably.

**"laid back friendly Australian girl" (the default):**

> [cheerful][relaxed] Yeah, so — got that all sorted for ya. [giggles] [short pause] Honestly came together HEAPS cleaner than I reckoned… [content] everything's hooked up beautiful. [warmly] Just give us a yell if you wanna tweak anything, ay.

### Step 3 — Write the tagged summary to disk

Write the fully tagged summary — and **nothing else** (no preamble, no markdown, no surrounding quotes) — to `/tmp/claude_speak_api_input.txt` using the **Write** tool.

### Step 4 — Send to ElevenLabs and play

**Set the Bash tool's `timeout` parameter to `600000` on this call.** This is required, not
optional. `afplay` blocks for the full length of the audio, so the tool call must outlast
the read — and the Bash tool defaults to only **120 seconds**. At roughly 15.7 characters
of tagged text per second of speech, the tiers land like this:

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

Run this single bash block exactly as written (it reads the file from Step 3):

```bash
set -euo pipefail

: "${ELEVENLABS_API_KEY:?ELEVENLABS_API_KEY is not set. Add 'export ELEVENLABS_API_KEY=sk_...' to ~/.zshrc and source it.}"
command -v jq >/dev/null || { echo "jq is required — install with: brew install jq" >&2; exit 1; }

# Voice ID — change this single line to swap voices (browse: https://elevenlabs.io/app/voice-library).
VOICE_ID="u8ADrbquiJqufR9XMtb8"

IN=/tmp/claude_speak_api_input.txt
OUT=/tmp/claude_speak_api_output.mp3

[ -s "$IN" ] || { echo "Input file $IN is empty or missing." >&2; exit 1; }

# Hard credit backstop — ElevenLabs bills per character (audio tags count too).
# Refuse to send anything longer than the detailed-tier ceiling, regardless of tier.
ABS_MAX_CHARS=1800
CHARS=$(wc -m < "$IN" | tr -d '[:space:]')
if [ "$CHARS" -gt "$ABS_MAX_CHARS" ]; then
  echo "Refusing to send: input is ${CHARS} characters, over the ${ABS_MAX_CHARS}-char credit cap." >&2
  echo "Re-run with --brief or --medium, or raise ABS_MAX_CHARS below if this was intentional." >&2
  exit 1
fi

# Build JSON payload safely from the input text (jq -Rs handles all escaping)
PAYLOAD=$(jq -Rs '{
  text: .,
  model_id: "eleven_v3",
  voice_settings: {
    stability: 0.0,
    similarity_boost: 0.75,
    style: 0.0,
    use_speaker_boost: true
  }
}' < "$IN")

HTTP=$(curl -sS -o "$OUT" -w '%{http_code}' -X POST \
  "https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/mpeg" \
  -d "$PAYLOAD")

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
# like a silent failure.
afinfo "$OUT" 2>/dev/null | grep -i 'estimated duration' || true

afplay "$OUT"
```

### Step 5 — Confirm

After `afplay` returns, reply with **one short line** confirming playback and naming the personality voice **and the length tier** used (e.g. `Spoken as: laid back friendly girl · auto→medium.` or `Spoken as: gruff sailor · brief.`). Do **not** re-display the summary or the tagged text — the user heard it.
