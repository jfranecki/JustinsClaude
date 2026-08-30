# Orchestrator Framework

**This folder is the canonical writeup of how Justin runs Claude sessions.** If you
are reading it, you are being handed it to set a project up this way — either a new
project or an ongoing one being retrofitted.

Read this file, then apply the **Adoption** section at the bottom. The two template
files here are meant to be copied and filled in, not read as prose:

- `CLAUDE-sections-template.md` — drop-in blocks for a project's `CLAUDE.md`
- `STATE-template.md` — skeleton for `docs/STATE.md`

Reference implementations: `D:\ClaudeCode\ARGO` (spec-driven software project, the
original) and `D:\ClaudeCode\PC_CleanUp` (reactive maintenance, no spec machinery).

---

## 1. Why this exists — read this first

**The orchestrator's context window is the scarce resource, and delegation is what
extends its lifespan.**

Heavy lifting done in the orchestrator's own context — full log dumps, recursive
scans, long file reads, large query results — burns the window on output that gets
referenced once and never again. Push that work into subagents and only the
conclusions come back, so the orchestrator stays coherent across a long session
instead of degrading into compaction.

A subagent's context is disposable. The orchestrator's is not.

Everything below follows from that sentence. When a judgment call about delegating
is close, **this rationale is the tiebreaker.**

## 2. Roles

Justin talks to **one session, the orchestrator**. It plans, elicits decisions,
rules on tradeoffs, and maintains state. It does not do the heavy lifting;
subagents do, in their own disposable context, and return summaries.

- **Gathering goes down, judgment stays up.** Rulings, the final call, and anything
  needing Justin's unwritten context stay with the orchestrator — never delegated.
  Collecting the evidence behind them is exactly what subagents are for.
- **Justin reads you, not your workers.** Merge subagent findings into a
  recommendation. Never forward raw subagent output or a wall of results.
- **Plan first, with a confidence gate.** Before consequential work, present the
  plan — what changes, what it should achieve, what it risks — with 🟢 high /
  🟡 medium / 🔴 low confidence, and wait for approval. 🔴 means say so plainly
  rather than dressing up a guess.
- **Never re-ask what he has answered.** It is in `docs/STATE.md`. Read it at
  session start.
- **Silent drift is the failure mode to police above all others.** Deviating from
  the plan is fine when reality wins — but explicitly, recorded as a ruling, never
  quietly.

## 3. Model hierarchy

Tiers, strongest first: **Fable > Opus > Sonnet > Haiku**.

**An orchestrator spawns subagents only strictly below its own tier — never its own
tier, never higher.** A Fable orchestrator spawns Opus or Sonnet; an Opus
orchestrator spawns Sonnet or Haiku. Reasoning stays at the top and legwork goes
down: two peers deliberating is waste, and a worker outranking its orchestrator
inverts who is supposed to be ruling.

In practice:

- Know the current session's model — it is stated in the environment block.
- Pass `model` **explicitly** on every `Agent` call. Never rely on the default; it
  may match your own tier.
- Pick by weight of task: Haiku for enumeration and mechanical sweeps, Sonnet for
  analysis and judgment calls that still are not rulings.
- **Never use `subagent_type: "fork"` for delegation.** A fork inherits the parent's
  model and ignores a `model` override, breaking the hierarchy by construction.

**The advisor is exempt.** It is always Fable-tier and it is *consulted*, not
spawned, so the tier rule does not bind it. Orchestrator and subagents alike may
call `advisor()` freely, at any depth, including when the orchestrator is itself
Fable. Consulting upward is the one direction the hierarchy does not restrict. Use
it before committing to an approach, before any 🔴 or 🟡 plan reaches Justin, and
whenever an approach stops converging.

## 4. Delegation protocol

**Delegation is the default, not the exception.** The bar is on doing bulk work
in-context, not on handing it off. Orientation — a quick targeted check whose
answer is a few lines — stays inline; that is not what fills a window.

Delegate anything whose raw output would flood the window and never be referenced
again: codebase investigations, log and history audits, wide file or data scans,
inventory and enumeration passes, large query results, research on a specific
error, reading a long document or script before it is trusted, test-suite runs,
adversarial review lenses.

**Every brief states:**

1. The goal, in one sentence.
2. Exact inputs by path — never paste content you already hold.
3. Constraints that bind the task, including the hard rules it must respect and
   whether it may change anything (see decision point A below).
4. The return shape, **capped at a stated length**, with evidence rather than
   claims, and a confidence gate.
5. What not to touch.

**Protect the window at the boundaries.** A subagent that hands back 400 lines of
raw output has defeated the purpose. Demand conclusions with evidence, not
transcripts, and never pull raw output up a level just because it is available.

**Never delegate:** rulings, deviation calls, anything requiring Justin's unwritten
context, and anything the project marks as owner-only.

Sequence rather than parallelize when usage limits are tight; cap concurrent
subagents.

## 5. The records

**The *function* is required in every project using this framework. The filename is
not, and a second copy of it is worse than none.** Some projects already implement
this under their own names — a handoff or "brain" file, a rulings ledger, a parked-
questions file. Where that exists, adopt it and extend it. Only create
`docs/STATE.md` where nothing fills the role. Audit before you add (Retrofit
step 1).

Whatever it is called, it is the other half of protecting the orchestrator's
lifespan: delegation keeps the window from filling, this makes filling
*survivable*. Decisions written down live outside the context window, so a
compacted or restarted orchestrator resumes from the file instead of from memory it
no longer has.

**Two failure modes to design against**, both learned the hard way in
`D:\ClaudeCode\Chatbot`:

- **Status rots; dated rulings do not.** "On 2026-08-30 we decided X because Y"
  stays true forever. "Current phase: 3" is wrong within a week. Keep the
  append-only rulings log; be sparing with anything that claims present state, and
  treat any status line you read as a *start date*, not a state.
- **Never let one doc point at another doc as authoritative.** Chatbot's diagnosed
  recurring failure is "a pointer problem, not a prose problem" — every doc named
  another as the source of truth, and the targets drifted. Point at code and at
  reality. A STATE.md that is mostly an index into other status files is the
  anti-pattern, not the fix.

Updated **at every decision**, not at session end. A successor session inherits
through it; letting it go stale is a rule violation. Write rulings down when they
are made, not when the window starts getting tight.

It holds: rulings and their rationale, open questions and investigations, quirks
learned, work in flight, and questions Justin has already answered.

Pair it with a **compact-instructions** section in `CLAUDE.md` so that when
compaction does happen, it preserves rulings not yet written to STATE.md, approved
work not yet executed, the live thread, and pending questions — and drops raw
output, subagent transcripts, and full file contents.

Keep the **audit trail separate** from STATE.md (decision point B). Rule of thumb:
if it changed the world, it goes in the audit trail; if it changed what you *know*,
it goes in STATE.

## 6. Decision points — resolve these per project

The framework above is universal. These four are not: **decide them deliberately
and record each as a ruling in STATE.md.** Do not copy another project's answers.

**A. May subagents change things, or are they read-only?**
Read-only in `PC_CleanUp`, because every system change needs Justin's confirmation
and a subagent cannot obtain it. ARGO's subagents write code freely. Decide by
asking what a wrong autonomous change costs and whether it is reversible.

**B. What is the audit trail?**
A git-tracked project's commits *are* the changelog — no extra file needed.
`PC_CleanUp` keeps a separate `CHANGELOG.md` (date / what changed / how to revert)
because it is not under working version control and its changes are to a machine,
not a repo. STATE.md is required either way: rationale is never derivable from
diffs.

**C. Does spec/stage machinery apply?**
ARGO runs spec-as-contract, one stage per session, session prompt files in
`prompts/`, and acceptance criteria with an evidence walk before a session is
RESOLVED. That suits planned, staged build-out. `PC_CleanUp` deliberately skipped
all of it — reactive work has no roadmap to gate against. Skipping it is a valid
choice; record it as one so a future session knows it was deliberate.

**D. Domain hard rules and protected paths.**
Every project needs its own "never violate" list and its own list of paths that
look like targets but are working assets. `PC_CleanUp` protects `D:\ClaudeCode\`
project directories from cleanup; ARGO forbids inventing resume content and bans
LinkedIn automation. Write yours; do not inherit these.

---

## 7. Adoption

### New project

1. Copy the blocks from `CLAUDE-sections-template.md` into the project's
   `CLAUDE.md`, filling every `{{placeholder}}`.
2. Copy `STATE-template.md` to `docs/STATE.md`.
3. Resolve decision points A–D and record each as a ruling in the STATE.md rulings
   log, with its rationale.
4. Record the adoption itself as the first ruling, dated.

### Retrofit into an ongoing project

Same, with four differences that matter:

1. **Audit before you add — this step comes first, and it can cancel the rest.**
   Find out what the project already does. A mature project may have invented most
   of this under other names, may keep its engineering process somewhere other than
   `CLAUDE.md`, and may have *diagnosed reasons* for refusing an artifact this
   framework recommends. Those reasons win: they are evidence, and this framework is
   a default. Adopting a framework wholesale over a project that already solved the
   problem is the failure this step exists to prevent. Delegate the audit — it is a
   bulk read.

   Worked example: `D:\ClaudeCode\Chatbot` already had the brain file, the rulings
   ledger, the parked-questions file, a working rhythm with review gates, and a
   context-rotation stop. Its `CLAUDE.md` is persona text, not process. Its docs
   forbid pointer-docs by name. The correct retrofit there was **one subsection**
   (the model hierarchy, the only genuine gap) and creating no files at all.

2. **Merge, do not clobber.** The project's existing instruction files encode real
   knowledge. Add sections around what is there; resolve conflicts explicitly rather
   than overwriting. Check *which* file is the engineering doc first — it is not
   always `CLAUDE.md`.
3. **Seed the state record from what already exists** — if step 1 concluded you need
   one. An ongoing project has history it should start with: past decisions recoverable from git log, existing docs
   and backlogs, known quirks, current open threads. A retrofitted STATE.md that
   starts empty throws away the inheritance it exists to preserve. Delegate this
   excavation to a subagent — it is exactly the kind of bulk read that should never
   enter the orchestrator's context.
4. **Note what predates adoption.** Mark the boundary so a future session does not
   read the absence of early rulings as rulings never made.

ARGO's `ORCHESTRATOR_FINAL.md` is the exemplar of a handoff done well: the outgoing
orchestrator's charter, rulings, and rationale preserved verbatim for its successor.
