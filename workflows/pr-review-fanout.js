export const meta = {
  name: 'pr-review-fanout',
  description: 'Parallel /review-deep over a discovered set of PRs in isolated git worktrees',
  phases: [{ title: 'Review', detail: 'one subagent per PR, isolated worktree, full review-deep methodology' }],
}

// Parameterized via args (passed by the /pr-autoreview routine):
//   args.targets   = [{ n, base, jira, note, overlap:[{n,author,files:[...],t}] }]
//   args.repo      = "owner/repo"
//   args.main      = absolute path to the canonical (non-worktree) checkout
//   args.skillPath = absolute path to review-deep.md
//   args.repoNotes = optional repo-specific sharp edges every reviewer should check
let A = (typeof args !== 'undefined' && args) ? args : {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }   // Workflow may deliver args as a JSON string
const REPO = A.repo
const MAIN = A.main
const SKILL_PATH = A.skillPath
const NOTES = A.repoNotes || '(none provided)'
const PRS = Array.isArray(A.targets) ? A.targets : []

if (!REPO || !MAIN || !SKILL_PATH) {
  log('Missing required args: repo, main, and skillPath must be provided by the calling routine.')
  return { total: 0, succeeded: 0, failed: [], reviews: [], error: 'missing required args (repo, main, skillPath)' }
}

const SCHEMA = {
  type:'object', additionalProperties:false,
  required:['number','title','author','base','review_depth','recommendation','ci_status','mergeable','summary','blockers','major','minor','conflicts','questions','report_markdown','report_path'],
  properties:{
    number:{type:'integer'}, title:{type:'string'}, author:{type:'string'}, base:{type:'string'},
    review_depth:{type:'string', enum:['DEEP','STANDARD','LIGHT']},
    recommendation:{type:'string', enum:['APPROVE','REQUEST_CHANGES','NEEDS_DISCUSSION','COMMENT']},
    ci_status:{type:'string'}, mergeable:{type:'string'}, summary:{type:'string'},
    blockers:{type:'array', items:{type:'string'}}, major:{type:'array', items:{type:'string'}},
    minor:{type:'array', items:{type:'string'}}, conflicts:{type:'array', items:{type:'string'}},
    questions:{type:'array', items:{type:'string'}}, report_markdown:{type:'string'}, report_path:{type:'string'},
  },
}

function buildPrompt(pr) {
  const ov = Array.isArray(pr.overlap) ? pr.overlap : []
  const ovText = ov.length
    ? ov.map(o => `  - #${o.n} [${o.author||'?'}] "${o.t||''}" — shared files: ${(o.files||[]).join(', ')}`).join('\n')
    : '  (none — no other OPEN PR on the same base touches this PR\'s files. Still run the Phase 3 step-4 base-branch recent-churn check.)'
  const stacked = pr.stacked
    ? `\nSTACKED PR: base is a feature branch (head of #${pr.stacked}), not main. Review only the incremental diff (gh pr diff scopes it). Parent PR(s) are themselves under review — call out the required merge order and flag correctness depending on unmerged parent behavior.\n`
    : ''
  const rereview = (pr.is_rereview && pr.prior_review)
    ? `\nRE-REVIEW: I previously reviewed this PR at commit ${pr.prior_review.commit} and left ${pr.prior_review.verdict}${pr.prior_review.submitted_at ? ' on '+pr.prior_review.submitted_at : ''}. New commits have landed since. This is a FOLLOW-UP pass: in Phase 1.6, read my prior review and the inline threads, then determine for each prior blocker/concern whether the new commits resolve it, leave it open, or introduce something new. Base your verdict on the CURRENT state (if the prior blockers are fixed and nothing new is wrong, APPROVE and say what got fixed; if issues remain or regressed, be specific about what still needs doing). Diff the change since my last review with: 'gh pr diff ${pr.n}' plus 'git log --oneline ${pr.prior_review.commit}..HEAD' after checkout to see exactly what the author pushed.\n`
    : ''
  return `You are a senior engineer performing a rigorous, skeptical production PR review.

STEP 1 — Read the review methodology IN FULL and follow it exactly for every phase:
  Read the file: ${SKILL_PATH}
Internalize Phases 0 through 6. The Phase 5 structured-report format matters.

STEP 2 — Target and environment:
- Repo: ${REPO}
- You are inside a DISPOSABLE, ISOLATED GIT WORKTREE of this repo; your cwd IS the worktree root. It is safe to 'gh pr checkout ${pr.n} --detach' here. SKIP Phase 0.
- WRITE your final report to this canonical checkout so it survives worktree cleanup: ${MAIN}
- PR under review: #${pr.n}
- Base branch: ${pr.base}
- Linked Jira: ${pr.jira || 'unknown (extract from title/branch/body/commits)'}
- Reviewer context (verify it, don't just trust it): ${pr.note || '(none)'}
${stacked}${rereview}
STEP 3 — Execute Phases 1, 1.5, 1.6, 2, 3, 4, 5 fully:
- Phase 1: gh pr view (json); gh pr diff ${pr.n}; gh api repos/${REPO}/pulls/${pr.n}/comments --paginate; gh api repos/${REPO}/pulls/${pr.n}/reviews --paginate. Try 'acli jira workitem view ${pr.jira||''}' and its comments; if acli is unavailable (likely in an automated run), note it and proceed. Check out the head read-only: 'gh pr checkout ${pr.n} --detach'; establish merge-base; inspect git log/diff --stat. Run 'gh pr checks ${pr.n}' and report + identify failing checks.
- Phase 1.5: pick DEEP / STANDARD / LIGHT, justify in one line. Auth/session/crypto, DB migrations, infra/CI/IaC (incl. cron/crontab + monitoring/alert scripts), and public routes are AUTO-DEEP.
- Phase 1.6: read prior reviews + inline + issue comments; classify each thread. A standing CHANGES_REQUESTED from another reviewer is a merge blocker. Don't re-litigate settled points; surface open unanswered threads.
- Phase 2: spec alignment per acceptance criterion, logic walk-through (happy path + >=2 failure paths per non-trivial function), error handling, concurrency/state, type safety, tests.
- Phase 3 — CONFLICT DETECTION. Pre-computed open PRs (same base) sharing >=1 file with this PR; investigate each, fetch its diff with 'gh pr diff <num>', assess textual/semantic/indirect conflicts + merge order:
${ovText}
  Then Phase 3 step 4: 'git log --since="21 days ago" --oneline origin/${pr.base} -- <changed files>' for base churn. If mergeable is CONFLICTING, name files + root cause.
- Phase 4: full cross-cutting walk (security, performance, compat, migrations, observability, flags, config, docs, style, deps, i18n/a11y, dead code/debug artifacts). Repo-specific sharp edges from config (verify them in the code, don't assume): ${NOTES}

STEP 4 — Tests: run ONLY narrowly-scoped touched-file tests (e.g. 'python -m pytest tests/unit/test_<x>.py -q'). If a run takes >3 min to start producing output, stop it and note you skipped it. Report pass/fail.

HARD CONSTRAINTS:
- READ-ONLY review. Do NOT post anything to GitHub, do NOT 'gh pr review'/comment/approve/push/merge/modify any branch or remote. Posting is done later by the routine, not by you.
- Do NOT push to main or any release branch. Do NOT write into any submodule checkout under ${MAIN}.
- Local-only git ops inside your worktree (fetch, checkout --detach, log, diff) are fine.

STEP 5 — Write your complete Phase-5 structured report (EXACT skill markdown: header block, Summary, Spec alignment, Blockers, Major concerns, Minor/nits, Conflicts with other open PRs, Test coverage assessment, Cross-cutting checklist, Questions for the author, Positive notes) to:
  ${MAIN}/.claude/pr-reviews/PR-${pr.n}.md

STEP 6 — Return the StructuredOutput. Choose 'recommendation' HONESTLY (do not default to APPROVE): APPROVE only if no blockers/no standing CHANGES_REQUESTED and you'd merge as-is; REQUEST_CHANGES for must-fix blockers; NEEDS_DISCUSSION when it hinges on a human decision; COMMENT otherwise. report_markdown must equal the report on disk. Cite path:line; write "None." where empty; don't invent issues.`
}

phase('Review')
if (!PRS.length) {
  log('No targets passed — nothing to review.')
  return { total:0, succeeded:0, failed:[], reviews:[] }
}
log(`Launching ${PRS.length} parallel deep reviews in isolated worktrees: ${PRS.map(p=>'#'+p.n).join(' ')}`)

const results = await parallel(PRS.map(pr => () =>
  agent(buildPrompt(pr), {label:`review #${pr.n}`, phase:'Review', isolation:'worktree', schema:SCHEMA})
    .then(r => r ? {...r, _n: pr.n} : {_n: pr.n, _failed:true})
))

const ok = results.filter(r => r && !r._failed)
const failed = results.filter(r => !r || r._failed).map(r => r && r._n)
log(`Reviews complete: ${ok.length}/${PRS.length}. Failed: ${failed.join(', ') || 'none'}`)

return {
  total: PRS.length, succeeded: ok.length, failed,
  reviews: ok.map(r => ({
    number:r.number ?? r._n, title:r.title, author:r.author, base:r.base,
    review_depth:r.review_depth, recommendation:r.recommendation, ci_status:r.ci_status, mergeable:r.mergeable,
    summary:r.summary, blockers:r.blockers, major:r.major, minor:r.minor, conflicts:r.conflicts, questions:r.questions,
    report_path:r.report_path, report_markdown:r.report_markdown,
  })),
}
