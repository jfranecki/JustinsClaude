# STATE.md — living orchestrator state

> Copy this to `docs/STATE.md` in the adopting project and fill it in. Delete this
> blockquote and the `>` guidance notes under each heading once seeded.
>
> **First check whether you should use this file at all.** Per README retrofit
> step 1, a project may already run this function under its own names — a handoff or
> "brain" file, a rulings ledger, a parked-questions file. If so, extend what exists
> and do not copy this template; a competing state surface is worse than none.

> Standing instruction (recorded {{DATE}}): updated **at every decision**, not at
> session end. It exists so a successor session inherits rulings, open questions,
> quirks, and in-flight work without loss. Keeping it current is part of every
> ruling made here.
>
> This file is memory. {{AUDIT_TRAIL_POINTER}} is the audit trail — what actually
> changed. Keep them separate.

Last updated: {{DATE}} ({{ONE_LINE_STATUS_AND_WHAT_IS_NEXT}})

---

## Roadmap position

> Where the work stands and what comes next. In a staged project this is the
> stage list; in a reactive one it is the current focus and standing threads.
> Delete this section if the project genuinely has no forward shape.

## Rulings log (what was decided and why)

> The core of the file. One entry per decision, dated, **with its rationale** —
> the "why" is what a successor cannot recover from the code or the history.
> Record decisions to *not* do something too; a skipped option looks like an
> oversight later unless it is written down as a choice.
>
> Seed with the four framework decision points (A: may subagents mutate;
> B: what the audit trail is; C: spec/stage machinery or not; D: domain hard
> rules and protected paths) plus the adoption itself.

- **{{DATE}} — Orchestrator framework adopted.** Per
  `{{ORCHESTRATOR_FRAMEWORK_PATH}}`. {{PORTED_VS_LEFT_OUT}}
- **{{DATE}} — Model hierarchy**: an orchestrator spawns only strictly
  below its own tier. Fable > Opus > Sonnet > Haiku. Delegate through the tier-named
  worker agents (`sonnet-worker`, `haiku-worker`, `opus-worker` in `~/.claude/agents/`)
  and omit `model` — their frontmatter pins it, and the type name is what the agent
  panel renders, so the tier stays visible on screen. Where they are not installed,
  pass `model` explicitly and prefix the description with the tier. Never `fork` (it
  inherits the parent's model). The advisor is exempt — always Fable, consulted rather
  than spawned, callable at any depth.
- **{{DATE}} — Rationale for the whole pattern**: the orchestrator's
  context window is the scarce resource. Delegating heavy lifting keeps the window
  from filling with output referenced once and never again, which extends how long
  the orchestrator stays coherent. Delegation is therefore the **default**, and
  this rationale is the tiebreaker on close calls.

## Open decisions / investigations

> Questions awaiting the owner's answer, and threads that are open but not in flight.
> An empty list is fine; a stale one is not.

## In-flight work

> What is mid-execution right now, and its exact position — what is approved, what
> is done, what remains. This is what a session picks up from after an
> interruption.

## Quirks and hard-won facts

> Things learned the hard way that are not recoverable from the code, the docs, or
> the history: tooling that lies, environment constraints, footguns already
> stepped on. Each one here is a mistake a future session does not have to repeat.

## About the owner (operational facts)

> Preferences, constraints, and context they have stated that shape how work is
> done — so they are never asked twice. Deeper personal context belongs in the
> global memory files, not here.

## Predates adoption

> Retrofits only. Note the boundary: what history exists from before the framework
> was adopted, and where it lives (git log, older docs, prior session logs), so a
> future session does not read the absence of early rulings as rulings never made.
> Delete this section in a new project.
