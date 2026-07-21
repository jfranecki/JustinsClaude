---
description: End-of-session close-out — verify the goal is met, audit git state, clean up worktrees and branches, then confirm it's safe to close
disable-model-invocation: true
---

# /bye — Safe session close-out

You are closing out this Claude Code session. Answer one question: **"Are we safe to close?"**

Work in three phases. Phase 1 is strictly read-only. Nothing state-changing happens until the user approves in Phase 2. Do not drift into new work — even fixing blocking items requires the user to choose that path.

## Phase 0 — Establish context

From this session's conversation, identify:
- The goal(s) the session was working toward
- Repos touched and worktrees created
- PRs opened/merged, and any work items tracked in an external system (issue tracker, project board, team docs)

If the session did no substantive work (pure Q&A — no files, branches, or work items touched): report "Nothing to close out — safe to close" and stop.

## Phase 1 — Audit (read-only)

Check every dimension below and gather evidence. Do not fix anything yet.

### 1. Goal completion
- Is the stated goal actually delivered? Verify with evidence — never claim "done" without checking.
- If tests are applicable: do they exist and pass? (Running the test suite is allowed here.)
- List remaining work, half-finished pieces, and known follow-ups.

### 2. Git state — for every repo touched this session
- `git status` — uncommitted changes, especially in shared checkouts.
- Unpushed commits (`git log @{u}..`, or a branch with no upstream).
- Is a shared checkout left sitting on a feature branch?
- `git worktree list` — worktrees created this session; for each, is the branch **confirmed merged**? Use `gh pr view <branch>` (state MERGED) when `gh` is available; otherwise `git fetch origin` and confirm the merge commit is on `origin/<default-branch>`.
- Is the local default branch behind its remote following a confirmed merge?

### 3. External state (if applicable)
If this session's work is tracked outside the repo — an issue tracker, a project board, team documentation — check whether that system still reflects reality after this session:
- Does the item's status match the actual state of the work (in progress / in review / merged / shipped)?
- **Merge ≠ deploy.** If merged code hasn't shipped yet, don't mark the item done.
- Did the work make any team documentation stale?

If you have no tool access to those systems, list the needed updates as manual to-dos in the report rather than skipping them silently.

## Phase 2 — Report and decide

Present one report grouped by severity:

- **Blocking** — goal not met, failing or missing tests, uncommitted/unpushed work required to finish the task
- **Housekeeping** — merged worktrees and branches to remove, default branch to pull, shared checkout to return to it
- **External state** — tracker updates or doc edits needed (or manual to-dos, if no tool access)

For every proposed action, show exactly what will run: the git commands, the status change and comment text, the doc edit summary. Report faithfully — surface failures, skipped checks, and uncertainty plainly.

Then ask the user (AskUserQuestion) how to proceed:
1. **Finish remaining work** — continue the session on the blocking items first
2. **Housekeep & sync, then close** — execute the approved cleanup and external updates
3. **Close anyway** — bypass; if work remains, write a handoff note first (see Phase 3)

If nothing is blocking, offer only the last two. If every check is clean, skip the question: report "All clear — safe to close."

## Phase 3 — Execute (approved actions only)

### Git guardrails
- Pull the latest default branch only once the merge is confirmed remotely.
- Remove worktrees and delete local branches (and the remote branch, if not auto-deleted) **only for confirmed-merged branches**. Never force-delete (`-D`) unmerged work.
- Return the shared checkout to the default branch; stash or otherwise preserve uncommitted work first — never discard.

### External-state guardrails
- Never close a tracked work item without a comment stating: **why** it's closing (what resolved it), **who** decided and **when**, and **links** to the superseding item/PR/decision.
- Merged-but-not-shipped work stays open (or in a "ready to deploy"-style state if your tracker has one) — never "done".

### Handoff note (bypass path)
If the user chose "Close anyway" with work remaining: before ending, record the open threads durably — in your Claude memory, a notes file, or a comment on the tracked item — listing what's left, its current state, and where artifacts live, so the next session doesn't start cold.

## Final report

- Confirm each executed action with evidence (command output, resulting status, updated doc).
- Report anything that failed or was skipped — do not smooth it over.
- End with a clear verdict: **"Safe to close"**, or exactly what still stands in the way.
