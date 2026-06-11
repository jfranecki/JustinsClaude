export const meta = {
  name: 'pr-draft-fanout',
  description: 'Draft human-voiced GitHub review bodies for a set of reviewed PRs',
  phases: [{ title: 'Draft', detail: 'one agent per PR, reads its report, writes a natural review body' }],
}

// Parameterized via args:
//   args.prs       = [{ n, type: 'approve'|'comment'|'request-changes', author, clusterNote? }]
//   args.main      = absolute path to the canonical checkout
//   args.skillPath = absolute path to review-deep.md
let A = (typeof args !== 'undefined' && args) ? args : {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }   // Workflow may deliver args as a JSON string
const MAIN = A.main
const SKILL_PATH = A.skillPath
const PRS = Array.isArray(A.prs) ? A.prs : []

if (!MAIN || !SKILL_PATH) {
  log('Missing required args: main and skillPath must be provided by the calling routine.')
  return { total: 0, succeeded: 0, failed: [], drafts: [], error: 'missing required args (main, skillPath)' }
}

const SCHEMA = {
  type:'object', additionalProperties:false,
  required:['number','review_type','body','self_check_passed'],
  properties:{
    number:{type:'integer'},
    review_type:{type:'string', enum:['approve','comment','request-changes']},
    body:{type:'string'},
    self_check_passed:{type:'boolean'},
  },
}

function prompt(pr) {
  let verbGuide
  if (pr.type === 'approve') {
    verbGuide = `This posts as an APPROVE. The PR is genuinely clean. Keep it short (a few sentences), say plainly what you checked that gave you confidence, and you may mention 1-2 non-blocking minors as "while you're around" notes without making them sound like conditions. Don't manufacture concerns.`
  } else if (pr.type === 'request-changes') {
    verbGuide = `This posts as a REQUEST-CHANGES review. Lead with the single most important must-fix, stay collegial and specific, and be clear about what has to change before merge. Acknowledge what's genuinely good first so it doesn't read as a pile-on.`
  } else {
    verbGuide = `This posts as a COMMENT review (verdict was NEEDS_DISCUSSION — it hinges on a human decision/coordination, not a code defect). Lead with the decision that's needed. Note the code is in good shape if it is, then lay out the sequencing or reconciliation ask and any specific things worth fixing while they're in there.`
  }
  const cluster = pr.clusterNote ? `\nCross-PR context to weave in only where it actually bears (don't dump it everywhere): ${pr.clusterNote}\n` : ''
  const followup = pr.is_rereview ? `\nThis is a FOLLOW-UP review (I already reviewed an earlier version of this PR and left ${pr.prior_verdict || 'feedback'}). Write it as a human coming back after the author's latest push: briefly acknowledge the update, say plainly whether the earlier concerns are now addressed, and only raise what still stands or what's newly broken. Do not re-explain the whole PR from scratch or repeat points already settled.\n` : ''
  return `You are writing the GitHub review comment a human senior engineer would leave on PR #${pr.n} (author: ${pr.author||'the author'}). The deep analysis is already done; your only job is to turn it into a natural, human-sounding review body.

STEP 1 — Read the Phase 6 "Writing the GitHub comment" voice rules and follow them strictly:
  Read ${SKILL_PATH}
STEP 2 — Read the full structured report you are condensing:
  Read ${MAIN}/.claude/pr-reviews/PR-${pr.n}.md

STEP 3 — Write the review body. ${verbGuide}${cluster}${followup}
Hard voice rules (non-negotiable; the body is rejected and rewritten if it breaks them):
- First person, conversational ("I traced", "I ran", "I think"). Contractions fine.
- NO em-dashes anywhere. Use a period, comma, or parentheses.
- NO parenthetical citation footnotes like "(services.py:3826)" or "(verified via grep)". Weave locations into the sentence.
- NO status-report / build-log cadence ("14 checks pass, 16/16 tests, 0 conflicts"). Say it like a person.
- NO "Net:", "TL;DR:", "Summary:", "Result:" labels; no bullet-list-of-metrics ending.
- Don't enumerate every category you checked. Mention the one or two things that matter.
- Prose for short points; a few plain-sentence bullets only when there are genuinely separate items.
- Be accurate to the report and fair. Don't soften an approve into a block, and don't harden a comment into a teardown.
- Length matches substance. A clean approve is short; a findings comment is tight with maybe 1-3 concrete notes.

Would a teammate recognize this as something you'd actually type, or does it smell like a bot? If the latter, rewrite before returning.

STEP 4 — Return StructuredOutput: number=${pr.n}, review_type="${pr.type}", body=<final text, GH markdown ok>, self_check_passed=true ONLY if you re-read it and it has no em-dashes, no "(file:line)" footnotes, no metrics-cadence, no "Net:/TL;DR:" labels.`
}

phase('Draft')
if (!PRS.length) { log('No PRs to draft.'); return { total:0, succeeded:0, failed:[], drafts:[] } }
log(`Drafting ${PRS.length} human-voiced review bodies`)

const drafts = await parallel(PRS.map(pr => () =>
  agent(prompt(pr), {label:`draft #${pr.n}`, phase:'Draft', schema:SCHEMA})
    .then(r => r ? {...r, _n:pr.n, _type:pr.type} : {_n:pr.n, _type:pr.type, _failed:true})
))
const ok = drafts.filter(d => d && !d._failed)
const failed = drafts.filter(d => !d || d._failed).map(d => d && d._n)
log(`Drafts done: ${ok.length}/${PRS.length}. Failed: ${failed.join(', ') || 'none'}`)
return { total:PRS.length, succeeded:ok.length, failed,
  drafts: ok.map(d => ({number:d.number ?? d._n, review_type:d.review_type ?? d._type, body:d.body, self_check_passed:d.self_check_passed})) }
