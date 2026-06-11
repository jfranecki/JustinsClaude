---
description: Deeply onboard onto the module/codebase the current session was started in, including submodules
argument-hint: "[optional: path or area to focus on, e.g. 'the auth layer']"
allowed-tools: Bash(pwd:*), Bash(git:*), Bash(ls:*), Bash(find:*), Bash(wc:*), Bash(head:*), Bash(cat:*), Bash(tree:*), Bash(echo:*), Read, Glob, Grep
---

# /onboard — Deep Session Onboarding

You are starting fresh in this codebase and your job is to build a **thorough, load-bearing mental model** of it before doing any work. Treat this as the most important task of the session: everything you do later depends on getting this right. **ultrathink** about what you find — do not skim, do not pattern-match to "a typical project of this kind," and do not assume conventions you have not verified in the actual files.

Optional focus from the user (may be empty): **$ARGUMENTS**
If a focus is given, still map the whole module first, then go deeper on that area.

## Pre-loaded context

Current location and orientation:

- Working directory: !`pwd`
- Repo root (if any): !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Current branch & status: !`git status -sb 2>/dev/null | head -20`
- Recent history: !`git log --oneline -15 2>/dev/null`
- Submodules declared: !`git config --file .gitmodules --get-regexp path 2>/dev/null || echo "none"`
- Top-level contents: !`ls -la`
- Rough size: !`git ls-files 2>/dev/null | wc -l` tracked files

Use this as a starting point, not the whole picture. Read the real files.

---

## Discovery protocol

Work through these phases **in order**. Use parallel tool calls within a phase wherever possible (e.g. read README, manifest, and config files together). Prefer `Glob` and `Grep` for breadth, then `Read` whole files for the pieces that matter. Read entire key files — do not read the first 50 lines and guess the rest.

### Phase 0 — Orient

Establish the basics before going deep:
- What *is* this module? One or two sentences in your own words, derived from the README and the code, not from the directory name.
- Is the session rooted in the whole project, a single module, or one package of a monorepo? Where does the boundary sit?
- What language(s), runtime(s), and ecosystem(s) are in play? Confirm from manifests, not file extensions alone.

### Phase 1 — Structure & boundaries

Map the shape of the thing:
- Build the real directory tree (depth ~3) and identify the meaningful directories vs. noise (vendored deps, build output, caches).
- Read every manifest / project file you can find: `package.json`, `pyproject.toml`, `setup.py`, `requirements*.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`, `*.csproj`, etc.
- **Submodules and workspaces are first-class here.** For each git submodule, monorepo workspace (npm/pnpm/yarn workspaces, Cargo workspace, Nx/Turborepo, Lerna, Go multi-module), or local package, recurse: identify what it is, what it exposes, and how the parent depends on it. Do not treat a submodule as a black box.
- Note the boundary between *this* module and the rest of the world: what it imports, what imports it.

### Phase 2 — Entry points & execution flow

Find how it actually runs:
- Locate entry points: `main`, CLI definitions, server bootstrap, `__main__`, exported package index, scripts in the manifest, framework conventions (e.g. route files, handlers).
- Trace at least one representative path from entry → core logic → exit/response. Name the actual functions/files in the chain.
- Identify the primary abstractions and where they live (the 5–10 files a maintainer would say "you have to understand these").

### Phase 3 — Dependencies & coupling

- External dependencies: which ones are load-bearing vs. incidental? Flag anything unusual, pinned oddly, or deprecated.
- Internal coupling: how do the submodules/packages depend on each other? Sketch the dependency direction. Watch for cycles.
- Integration points: databases, queues, external APIs, env vars, secrets/config files, service boundaries.

### Phase 4 — Conventions, tooling & quality gates

- Code style and conventions *as practiced in this repo* (naming, structure, error handling patterns). Cite a couple of real examples.
- Tooling: linters, formatters, type checkers, pre-commit hooks, configured in which files.
- Tests: framework, where they live, how to run them, rough coverage of what matters. Read a couple of tests to learn the expected behavior of core pieces.
- CI/CD: read `.github/workflows`, `.gitlab-ci.yml`, etc. What must pass before merge?
- Read `CLAUDE.md`, `CONTRIBUTING.md`, `AGENTS.md`, `/docs`, ADRs — any existing guidance for contributors or agents. Honor it.

### Phase 5 — Domain & data model

- What problem does this solve, in domain terms? What are the core nouns/entities?
- Where is state held and how does it move? Schemas, models, types, migrations.

### Phase 6 — State of the code

- Recent direction: what do the last ~30 commits suggest is being actively worked on?
- Rough edges: `TODO`/`FIXME`/`HACK` markers, obviously stale code, areas with no tests.
- Anything surprising, risky, or that contradicts the README.

---

## Output

After discovery, **ultrathink** to synthesize everything into a single onboarding briefing. Do not just dump file lists — explain how the pieces fit together. Structure it as:

1. **What this is** — purpose and scope in 2–3 sentences.
2. **Architecture map** — the module and its submodules/packages, how they relate, with a simple dependency sketch.
3. **Key files to know** — the handful that carry the most weight, each with one line on why.
4. **How it runs** — entry points, the main execution path, how to build/run/test.
5. **Conventions & gates** — the rules a contributor must follow and what CI enforces.
6. **Current state & watch-outs** — active work, risks, gaps, anything surprising.
7. **Open questions** — things you could not determine from the code that you'd want a human to confirm.

Keep claims grounded in files you actually read; if you're inferring, say so. Calibrate confidence honestly.

Finally, ask the user whether they'd like this briefing persisted (e.g. appended to `CLAUDE.md` or saved to a notes file) so future sessions start with it, and whether they want to go deeper on any particular area.
