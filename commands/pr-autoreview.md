# /pr-autoreview — automated PR review + post routine

You are running the **PR auto-review routine**. It finds every open PR in the configured repository that needs my review, runs the full `/review-deep` methodology on each in parallel isolated worktrees, then auto-posts a human-voiced review on each. It is designed to run unattended on a schedule (e.g. hourly during working hours) and also to be run by hand.

This is an AUTOMATED run. Work through the steps in order, top to bottom, without stopping to ask me questions. If a step legitimately cannot proceed (e.g. `gh` not authenticated), stop and say why.

## Config (current policy)

```
REPO       = {{GITHUB_REPO}}
MAIN       = {{MAIN_CHECKOUT}}
SKILL      = {{HOME}}/.claude/commands/review-deep.md
ME         = {{GITHUB_USERNAME}}
JIRA_KEY   = {{JIRA_PROJECT_KEY}}   # Jira project prefix used to spot ticket keys in titles/branches; XXXX if Jira is not used
REPO_NOTES = {{REPO_NOTES}}         # optional repo-specific sharp edges handed to every reviewer subagent; "(none provided)" if empty
POST_MODE  = auto-post-all      # approve / comment / request-changes all posted in human voice
MAX_PER_RUN = 15                # safety cap; if more new PRs than this, review the oldest 15 and log the rest as deferred
REVIEW_WF  = {{HOME}}/.claude/workflows/pr-review-fanout.js
DRAFT_WF   = {{HOME}}/.claude/workflows/pr-draft-fanout.js
LEDGER     = <MAIN>/.claude/pr-reviews/.review-ledger.json
```

## Hard constraints (always)

- The review phase is strictly READ-ONLY. Subagents must not write to GitHub. Posting happens only in Step 7 of THIS routine, after drafting + linting.
- Never push to `main` or any release branch. Never write into any submodule checkout under `<MAIN>`. Never modify a PR branch.
- Idempotency is HEAD-AWARE: skip a PR only if my latest review (as ME = `{{GITHUB_USERNAME}}`) was submitted against the PR's CURRENT head commit (`commit_id == headRefOid`). If new commits have landed since my last review, RE-REVIEW it as a follow-up pass and post an updated review. Each head SHA is reviewed at most once, so overlapping sweeps never double-post the same version, but an author pushing fixes does get re-checked.
- Always run Step 6 (worktree cleanup) even if earlier steps partially fail, so worktrees don't accumulate.

## Step 0 — Use the Workflow tool

This routine uses the Workflow tool for the parallel fan-outs. That is intended and pre-authorized by this command. Treat both fan-outs as opt-in workflows.

## Step 1 — Locate the repo

`cd <MAIN>`; confirm `gh repo view --json nameWithOwner -q .nameWithOwner` == `<REPO>` and `gh auth status` is logged in. If not, stop and report.

## Step 2 — Discover scope (idempotent)

Run this discovery script. It selects open + non-draft + not-mine PRs, drops any that already carry a review from ME, builds the Phase-3 same-base overlap map, applies MAX_PER_RUN (oldest first), and writes the Workflow args to `/tmp/pr_auto_targets.json`.

```bash
cd <MAIN>
TOKEN=$(gh auth token)
gh pr list --state open --limit 200 --json number,author,isDraft,baseRefName,title,headRefName,headRefOid,files,createdAt > /tmp/pr_auto_allopen.json
python3 - "$TOKEN" <<'PY'
import json, sys, urllib.request, concurrent.futures, re
token=sys.argv[1]
ME="{{GITHUB_USERNAME}}"; REPO="{{GITHUB_REPO}}"; MAX_PER_RUN=15
allopen=json.load(open("/tmp/pr_auto_allopen.json"))
cands=[p for p in allopen if not p["isDraft"] and (p.get("author") or {}).get("login")!=ME]
def my_latest_review(n):
    url=f"https://api.github.com/repos/{REPO}/pulls/{n}/reviews?per_page=100"
    req=urllib.request.Request(url, headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","User-Agent":"pr-autoreview"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r: data=json.load(r)
        mine=[rv for rv in data if (rv.get("user") or {}).get("login")==ME]
        if not mine: return n, None
        last=mine[-1]
        return n, {"commit_id":last.get("commit_id"),"state":last.get("state"),"submitted_at":last.get("submitted_at")}
    except Exception:
        return n, {"commit_id":"__ERROR__","state":"ERROR"}  # API error -> treat as up-to-date (skip), never risk a double-post
revmap={}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    for n,info in ex.map(my_latest_review, [p["number"] for p in cands]): revmap[n]=info
def head_moved(p):
    info=revmap[p["number"]]
    if info is None: return True                          # never reviewed
    if info.get("commit_id")=="__ERROR__": return False   # API error -> skip this sweep
    return info.get("commit_id") != p.get("headRefOid")   # head differs from my last-reviewed commit
def last_commit_after_my_review(n):
    # Guard against rebase/dismiss artifacts: only re-review if there's a commit dated AFTER my last review.
    info=revmap.get(n)
    if info is None: return True
    my_when=info.get("submitted_at")
    try:
        url=f"https://api.github.com/repos/{REPO}/pulls/{n}/commits?per_page=100"
        req=urllib.request.Request(url, headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","User-Agent":"pr-autoreview"})
        with urllib.request.urlopen(req, timeout=25) as r: commits=json.load(r)
        lc=commits[-1]["commit"]["committer"]["date"] if commits else None
        return bool(lc and my_when and lc > my_when)
    except Exception:
        return False
flagged=[p for p in cands if head_moved(p)]
todo=[p for p in flagged if (revmap.get(p["number"]) is None or last_commit_after_my_review(p["number"]))]  # never-reviewed, or genuinely updated
todo.sort(key=lambda p: p.get("createdAt") or "")          # oldest first
deferred=[p["number"] for p in todo[MAX_PER_RUN:]]
todo=todo[:MAX_PER_RUN]
by={p["number"]:p for p in allopen}
def files(p): return set(f["path"] for f in (p.get("files") or []))
targets=[]
for p in todo:
    n=p["number"]; tf=files(p); base=p["baseRefName"]
    text=" ".join([p.get("title") or "", p.get("headRefName") or ""])
    m=re.search(r'{{JIRA_PROJECT_KEY}}-\d+', text, re.I); jira=m.group(0).upper() if m else "unknown"
    ov=[]
    for q in allopen:
        if q["number"]==n or q.get("baseRefName")!=base: continue
        common=sorted(tf & files(q))
        if common: ov.append({"n":q["number"],"author":(q.get("author") or {}).get("login"),"files":common,"t":q.get("title")})
    ov.sort(key=lambda x:-len(x["files"]))
    info=revmap[n]; prior=None; is_re=False
    if info and info.get("commit_id") not in (None,"__ERROR__"):
        prior={"commit":info["commit_id"],"verdict":info["state"],"submitted_at":info.get("submitted_at")}; is_re=True
    targets.append({"n":n,"base":base,"jira":jira,"note":p.get("title") or "","overlap":ov[:12],
                    "head":p.get("headRefOid"),"is_rereview":is_re,"prior_review":prior})
out={"repo":REPO,"main":"<MAIN>","skillPath":"<SKILL>","targets":targets,"deferred":deferred,
     "candidate_count":len(cands),"todo_count":len(todo),
     "rereviews":[t["n"] for t in targets if t["is_rereview"]]}
json.dump(out, open("/tmp/pr_auto_targets.json","w"), indent=1)
print(f"candidates={len(cands)} to_review={len(todo)} (re-reviews={out['rereviews']}) deferred={deferred}")
print("targets:", " ".join("#"+str(t['n'])+("*" if t['is_rereview'] else "") for t in targets))
PY
```

Substitute the literal `<MAIN>` and `<SKILL>` values from Config in the script before running (they are placeholders).

## Step 3 — Short-circuit if nothing new

Read `/tmp/pr_auto_targets.json`. If `todo_count` is 0: this is the common case on a quiet sweep. Do NOT notify (a "nothing new" ping every sweep is noise). Append a one-line entry to `<MAIN>/.claude/pr-reviews/.sweep-log.txt` (timestamp + "0 new") and stop here.

If `deferred` is non-empty, remember it for the final summary (you reviewed the oldest MAX_PER_RUN; the rest will be picked up next sweep).

## Step 4 — Run the review fan-out (parallel, isolated worktrees)

Read `/tmp/pr_auto_targets.json`, parse it, add `repoNotes: <REPO_NOTES from Config>` to the parsed object, and pass it as the Workflow `args`:

> Workflow({ scriptPath: REVIEW_WF, args: <parsed contents of /tmp/pr_auto_targets.json, plus repoNotes> })

This runs one subagent per PR in its own worktree, each executing the full `/review-deep` (Phases 1–5), writing its report to `<MAIN>/.claude/pr-reviews/PR-<n>.md`, and returning a structured verdict. Wait for completion.

## Step 5 — Parse verdicts

From the workflow result, build the PR→verb mapping for posting:
- recommendation `APPROVE` → `approve`
- recommendation `REQUEST_CHANGES` → `request-changes`
- recommendation `NEEDS_DISCUSSION` or `COMMENT` → `comment`

Keep each PR's number, author, verdict, and a one-line summary for the roll-up.

## Step 6 — Clean up worktrees (ALWAYS run)

```bash
cd <MAIN>
git worktree list --porcelain | awk '/^worktree /{print $2}' | grep -E '\.claude/worktrees/wf_' | while read -r wt; do git worktree remove --force "$wt" 2>/dev/null && echo "removed $wt"; done
git worktree prune
git rev-parse HEAD            # sanity check that HEAD didn't move; report drift, do not act on it
git status --porcelain | grep -vE '^\?\?' || echo "(no tracked changes — clean)"
```

## Step 7 — Draft + lint + auto-post

1. **Draft** human-voiced bodies. Build `args.prs = [{n, type, author, is_rereview, prior_verdict, clusterNote?}]` from Step 5 (type = the verb; `is_rereview`/`prior_verdict` come from the target's `is_rereview`/`prior_review.verdict`). For a re-review, the draft should read as a follow-up ("came back to this after your latest push") that says whether the earlier concerns are now resolved, not a fresh first-look. If several PRs are clearly one author's coherent cluster (shared ticket family / stacked / shared files), pass a short `clusterNote` so merge-order asks are coordinated. Then:
   > Workflow({ scriptPath: DRAFT_WF, args: { main: MAIN, skillPath: SKILL, prs: [...] } })
2. **Lint** every returned body for bot-tells before posting. Reject (and re-draft once, or downgrade to a minimal safe body) any body containing: an em-dash `—` or en-dash `–`; a parenthetical citation footnote matching `(file.ext:NN)` or `(verified via …)`; `LGTM`, `✅`, `🚀`, `👍`; or a `Net:` / `TL;DR:` / `Summary:` / `Result:` label. Also require `self_check_passed == true` and a non-empty body. Save each passing body to `/tmp/pr_auto_bodies/PR-<n>.md`.
3. **Post** each, with a retry on transient TLS failures:
   ```bash
   for each (n, verb): gh pr review "$n" --"$verb" --body-file /tmp/pr_auto_bodies/PR-$n.md   # retry once after `sleep 3` on failure
   ```
   Skip (do not post) any PR whose body failed the lint and could not be repaired — log it for the summary instead.
4. **Verify**: re-query each PR's latest review state from ME and confirm it matches the intended verb (APPROVED / CHANGES_REQUESTED / COMMENTED).

## Step 8 — Roll-up + ledger + notify

1. Write `<MAIN>/.claude/pr-reviews/ROLLUP-<YYYY-MM-DD-HHMM>.md`: the verdict table, cross-PR conflicts/merge-order, and any deferred PRs.
2. Update `<LEDGER>` (create if missing): for each PR reviewed this run, record `{ "<n>": {"head": "<headSHA>", "verdict": "...", "posted": true/false, "at": "<iso>"} }`.
3. Append a line to `<MAIN>/.claude/pr-reviews/.sweep-log.txt`: timestamp, counts, verdicts, deferred.
4. **Notify** with PushNotification ONLY because something was posted this run (never on an empty sweep). One line, e.g.: `PR sweep: posted N reviews (#a approve, #b changes, #c comment)<, M deferred>`. Then end with a short text summary of the verdict table.

## Notes for whoever maintains this

- Idempotency rests on comparing my latest review's `commit_id` to the PR's current `headRefOid` in Step 2. A given head SHA is reviewed at most once, so overlapping sweeps never double-post the same version. But when the author pushes new commits (or rebases/force-pushes), the next sweep RE-REVIEWS the updated PR as a follow-up and posts a fresh review, so a `request-changes` or `needs-discussion` PR gets re-checked once the author responds with code. If you switch POST_MODE to notify-only, the GitHub `commit_id` signal disappears for un-posted reviews, so Step 2 must consult the LEDGER (by head SHA) instead.
- Re-review cadence is bounded: at most one re-review per distinct head SHA, so a PR pushed N times in a day gets at most N follow-ups (and only when its head actually changed between sweeps). To force a re-review without new commits, dismiss the existing GitHub review or run `/review-deep <n>` by hand.
- If a schedule is used, note that an in-session cron auto-expires after 7 days. Re-arm by asking Claude to "re-arm the PR sweep cron."
