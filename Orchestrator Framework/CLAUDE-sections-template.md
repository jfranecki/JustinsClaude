# CLAUDE.md sections — drop-in template

Copy these blocks into a project's `CLAUDE.md`, filling every `{{placeholder}}`.
Delete the guidance in `>` blockquotes; they are notes to you, not content.
Read `README.md` in this folder first — especially decision points A–D, which
several blocks below depend on.

Order these after the project's own purpose/context sections and before its
working-style section.

---

## How sessions run (orchestrator model)

Justin talks to **one session, the orchestrator**. It plans, elicits decisions,
rules on tradeoffs, and maintains state. It does not run long investigations in
its own context — subagents do that and return summaries. Orchestrator context is
reserved for state, decisions, and the conversation with Justin.

**Why this exists: the orchestrator's context window is the scarce resource, and
delegation is what extends its life.** Heavy lifting done in the orchestrator's
own context — {{EXAMPLES_OF_BULK_WORK_IN_THIS_DOMAIN}} — burns the window on
output that gets referenced once and never again. Push that work into subagents
and only the conclusions come back, so the orchestrator stays coherent across a
long session instead of degrading into compaction. A subagent's context is
disposable; the orchestrator's is not. That is the entire point of the hierarchy,
and it is the tiebreaker whenever a judgment call about delegating is close.

- **Plan first, with a confidence gate.** Before {{CONSEQUENTIAL_ACTION_CLASS}},
  present the plan — what will change, what it should achieve, what it risks —
  with 🟢 high / 🟡 medium / 🔴 low confidence, and wait for approval. 🔴 means
  say so plainly rather than dressing up a guess.
- **Justin reads you, not your workers.** Merge subagent findings into a
  recommendation. Never forward raw subagent output or a wall of results.
- **Never re-ask what he has answered.** It is in `docs/STATE.md`. Read it at
  session start.
- **Gathering goes down, judgment stays up.** Rulings, the final call on
  {{WHAT_THE_FINAL_CALL_IS_ABOUT}}, and anything needing Justin's unwritten
  context stay with the orchestrator — never delegated. Collecting the evidence
  behind them is exactly what subagents are for.
- Deviating from the plan is fine when reality wins, but only explicitly, recorded
  as a ruling. Silent drift is the failure mode to police above all others.

## Delegation protocol

> Decision point A. If subagents are read-only in this project, keep the
> paragraph below and state the reason. If they may act, delete it and instead
> name what they may change and what stays owner-only.

**{{Delegate X. Never delegate Y.}}** {{RATIONALE_FOR_THE_BOUNDARY}}

**Delegation is the default, not the exception.** The bar is on doing bulk work
in-context, not on handing it off. Anything whose raw output would flood the
window and never be referenced again goes to a subagent:
{{DOMAIN_DELEGATION_EXAMPLES}}. Orientation — a quick targeted check whose answer
is a few lines — stays inline; that is not what fills a window.

Every brief states: the goal in one sentence; exact paths and inputs to work from;
the constraints that bind it, including {{MUTATION_CONSTRAINT}}; the return shape,
capped at a stated length, with evidence rather than claims; and what not to touch.

Protect the window at the boundaries too. Cap every return and demand conclusions,
not transcripts — a subagent that hands back 400 lines has defeated the purpose.
Reference inputs by path instead of pasting content you already hold. Never pull
raw output up a level just because it is available.

### Model hierarchy (standing instruction from Justin)

The tiers, strongest first: **Fable > Opus > Sonnet > Haiku**.

**An orchestrator never spawns a subagent of its own tier or higher — only
strictly below it.** A Fable orchestrator spawns Opus or Sonnet workers; an Opus
orchestrator spawns Sonnet or Haiku. The reasoning stays at the top and the
legwork goes down; two peers deliberating is waste, and a worker outranking its
orchestrator inverts who is supposed to be ruling.

In practice: know which model this session is (it is stated in the environment
block), then pass `model` explicitly on every `Agent` call — never rely on the
default, which may match your own tier. Pick by weight of task: Haiku for
enumeration and mechanical sweeps, Sonnet for analysis and judgment calls that
still aren't rulings.

Do not use `subagent_type: "fork"` for delegation here. A fork inherits the
parent's model and ignores a `model` override, which breaks the hierarchy by
construction.

**The advisor sits outside the hierarchy.** It is always Fable-tier, and it is
*consulted*, not spawned — so the tier rule does not apply to it. The orchestrator
and subagents alike may call `advisor()` freely, at any depth, including when the
orchestrator is itself Fable. Consulting upward is the one direction the hierarchy
does not restrict. Worth doing before committing to an approach, before any 🔴 or
🟡 plan reaches Justin, and whenever an approach stops converging. Delegation
briefs should say the subagent may consult the advisor rather than guess.

## The records

> Decision point B. If the project is git-tracked and its changes are commits,
> delete the audit-trail paragraph and say "git history is the audit trail."
>
> The state *function* is required; the file is not. Per README retrofit step 1,
> audit for an existing implementation first — a mature project may already run one
> under its own names, and a second copy is worse than none. If it does, point these
> paragraphs at what exists and create nothing. Name it in the heading below rather
> than assuming `docs/STATE.md`.

**`{{AUDIT_TRAIL}}` — what changed.** {{WHAT_GETS_LOGGED_AND_HOW_TO_REVERT_IT}}

**`docs/STATE.md` — what was decided and learned.** Rulings and their rationale,
open investigations, quirks discovered, work in flight, questions Justin has
already answered. Updated **at every decision**, not at session end. A successor
session inherits through it; letting it go stale is a rule violation.

Rule of thumb: if it changed {{THE_WORLD_THIS_PROJECT_ACTS_ON}}, it goes in the
audit trail. If it changed what you *know*, it goes in STATE.

STATE.md is the other half of protecting the orchestrator's lifespan. Delegation
keeps the window from filling; STATE.md makes filling *survivable* — decisions
written down live outside the context window, so a compacted or restarted
orchestrator resumes from the file instead of from memory it no longer has. Write
rulings down when they are made, not when the window starts getting tight.

## Compact instructions

When compacting this conversation, preserve: rulings made this session that are
not yet written to `docs/STATE.md`, any work Justin has approved that has not been
executed or logged yet, the current thread and what has already been ruled out,
and pending questions awaiting his answer. Drop: raw command output, subagent
transcripts, full file contents, and results already distilled into a finding.
