---
name: review-pr
description: Reviews an RLinf-Hub pull request, re-reviews its revisions, or reviews a selected local diff for correctness, self-containment, RLinf integration quality, reproducibility, and bilingual README clarity; runs every touched area's check (code, submission, docs) plus blind reproduction and docs readability passes; reports concise, deduplicated findings with evidence; and posts them as one GitHub review only when asked. Use when asked to review, re-review, check before merge, or post review comments on an RLinf-Hub PR.
---

# Review a PR

Produce one concise, deduplicated review in the step 8 format: a verdict, a two-bullet reproduction summary, the findings table, detail sections only for non-inline (`here`) findings, inline comments printed once, and a two-bullet check summary (not posted). Post to GitHub only when the user asks ([posting.md](posting.md)). For a local diff review, compare against `RLinf/RLinf-Hub:main` and stop after step 8.

RLinf-Hub maintains a lightweight merge bar compared to core `RLinf/RLinf`, while keeping every component high quality, easy to run/reproduce, and easy to understand. Area checks live in [code](../code/SKILL.md), [submission](../submission/SKILL.md), and [docs](../docs/SKILL.md). Read [code/patterns.md](../code/patterns.md), [submission/reference.md](../submission/reference.md), and [reference.md](reference.md) before step 5.

## 1. Set up

Cross-reference against `main` of `github.com/RLinf/RLinf-Hub`, never the local working tree:

```bash
N=<PR number>
REMOTE=$(git remote -v | awk '/github\.com[:\/]RLinf\/RLinf-Hub(\.git)? \(fetch\)/ {print $1; exit}')
git fetch "$REMOTE" main "pull/$N/head:pr-$N"
BASE="$REMOTE/main"; PR_HEAD="pr-$N"
SKILLS="$(git rev-parse --show-toplevel)/.agents/skills"

gh pr view "$N" --repo RLinf/RLinf-Hub --json title,body,author,headRefOid,commits,files
gh pr checks "$N" --repo RLinf/RLinf-Hub
git log --oneline "$BASE..$PR_HEAD"
git diff --stat "$BASE...$PR_HEAD"
gh api "repos/RLinf/RLinf-Hub/pulls/$N/reviews" --paginate
gh api "repos/RLinf/RLinf-Hub/issues/$N/comments" --paginate
gh api "repos/RLinf/RLinf-Hub/pulls/$N/comments" --paginate
```

Check out `$PR_HEAD` in a separate git worktree for steps 3, 6, and verification; never edit or push the PR branch. Without `gh`, inspect `<PR URL>.diff` or GitHub REST endpoints; posting requires `gh`.

On a re-review, inspect every earlier review summary, discussion comment, and inline thread first. Verify each fix in the current code (never trust commit messages alone) and check for regressions. Carry open findings forward (reply on open inline threads and mark those rows `Posted = thread`; keep earlier IDs on open main-comment findings; number new findings after the highest earlier ID), name fixed earlier findings in the verdict, and do not reopen minor preferences the author answered reasonably.

## 2. Understand the PR

Read the PR description, linked issue (such as `RLinf/RLinf#1943`), commits, and diff, and note:

- the category (`algorithms`, `models`, `envs`, `robots`, or Hub infrastructure), upstream paper/repo/checkpoint, and declared scope (e.g., training + eval vs. inference-only);
- whether the PR stays strictly self-contained inside `<category>/<project_name>/` + root catalog rows;
- the closest existing sibling on `main` (if any) and the category README contract;
- every claim in the PR description (tested RLinf version, CPU/GPU tests, Ray registration, metrics/latency/curves, hardware runs) as a hypothesis to verify against the diff and tests.

## 3. Route the change

In the PR worktree:

```bash
python3 "$SKILLS/route.py" list --base "$BASE"
```

Check every listed area in step 6; review unrouted files yourself in step 5.

## 4. Run the reproduction

When a PR adds or updates a component under `algorithms/`, `models/`, `envs/`, or `robots/`, run a blind reproduction whenever this host has a compatible RLinf environment and the required hardware/assets:

1. **Check prerequisites** from the project's `README.md` against the host (RLinf version, free GPUs via `nvidia-smi`, `ray status` — never stop another user's jobs — checkpoints, simulator assets, or robot hardware).
2. **Launch a fresh agent (never a fork)** in the background while you review, working in its own worktree at `$PR_HEAD`. Give it only the PR URL, head SHA, `<category>/<project>/README.md`, allowed hardware, and local env rules. It must follow ONLY the project README, never read the project's implementation source to fill documentation gaps, fix nothing, and report:
   - the minimal setup steps it ran;
   - the first failure (if any) and every undocumented step or workaround needed;
   - offline CPU contract tests, GPU/Ray smoke tests, and task-level benchmarks separately.
3. **If blocked**, state specifically what RLinf version, GPU, checkpoint, simulator asset, or robot hardware is missing (and note what the author's PR evidence covers vs. leaves unverified).

Never reproduce the PR yourself after reading the implementation. An undocumented dependency, env var, or working-directory assumption is a `docs` finding. Unit tests run by the reviewer and area scripts go in Check summary, not as a substitute for blind user-docs reproduction.

## 5. Review the code and submission

Work through [reference.md](reference.md) against [code/patterns.md](../code/patterns.md) and [submission/reference.md](../submission/reference.md). File each finding under one category, ordered within each severity as:

| Category | Covers |
|---|---|
| `correctness` | bugs, shape/dtype/normalization errors, broken RLinf registration or Hydra composition, silent fake outputs, resource leaks |
| `design` | self-containment, upstream wrapping vs. vendored bloat, `RLINF_EXT_MODULE` / `EnvWorker` contract, static configs, scope creep, test-driven guards |
| `reuse` | duplicated upstream/RLinf utilities that should be imported or reused directly |
| `tests` | offline CPU contract tests, gated GPU smoke tests, `requirements.txt` pins/portability, verification evidence gaps, CI |
| `docs` | docs-to-code accuracy, install/launch copy-pasteability, EN/ZH parity, catalog rows, scope honesty, broken links |
| `docs-style` | readability, conciseness, native Chinese vs. translationese, CJK hard-wrapping, Markdown syntax/tables/prompts |
| `style` | Ruff lint/format, `__init__.py`, Apache-2.0 headers, DCO sign-off, Conventional Commits, PR title/body |

- **Large PRs** (> ~15 files or ~1,000 changed lines): partition by concern (adapter/runtime code, configs & requirements, tests, EN/ZH READMEs & catalog) so late files and Chinese READMEs are never skimmed.
- **Boundary & consumer check**: inspect how RLinf actually invokes the registered component (`RLINF_EXT_MODULE` in Ray workers + driver `validate_cfg()`, `BasePolicy.predict_action_batch`, `default_forward`, Hydra `searchpath` defaults) rather than assuming from names.

## 6. Check each area

In the PR worktree, run the automated checks and follow each routed area's `SKILL.md § Check` judgment checklist:

```bash
python3 "$SKILLS/route.py" check --base "$BASE"
python3 "$SKILLS/create-pr/lint_pr.py" lint --pr "$N"
```

- **Docs readability pass (fresh agent):** `docs/check.py` catches parity, links, fences, CJK hard-wrapping, and mechanical phrasing. Delegate full EN/ZH reading to a **fresh agent (never a fork)** that sees only the changed Markdown pages and [docs/SKILL.md](../docs/SKILL.md) + `docs/rules/` — with no Python implementation context. Flag: (1) stiff English or machine-translated/literal Chinese, (2) hard-wrapped Chinese paragraphs, (3) missing working-directory context or copy-paste traps, (4) internal code tours or repeated scope disclaimers, and (5) repeated negative-contrast framing ("not A, not B, but C" / "不是……而是……").
- **Script-to-category mapping:**
  - `correctness`: `code/syntax`, `code/shell-syntax`, `code/yaml`
  - `design`: `submission/layout`, `submission/registration`, `submission/artifacts`, `code/hardcoded-path`
  - `tests`: `submission/requirements`
  - `docs`: `submission/catalog`, `docs/parity`, `docs/structure`, `docs/links`, docs-to-code accuracy, command usability
  - `docs-style`: `docs/markdown`, `docs/en-style`, `docs/zh-style`, `docs/zh-hard-wrap`, readability/conciseness
  - `style`: `code/ruff`, `code/init`, `code/license`, `code/cuda`, PR lint, DCO sign-off
- Report any skipped check (and why) in Check summary.

## 7. Verify every finding

Try to falsify each candidate before reporting it. Run cheap offline CPU checks in the PR worktree whenever possible (`ast.parse`, YAML load, `pytest` on offline tests, `route.py check`) rather than relying only on static reading.

- **confirmed**: proven by a run or a complete line-cited trace on `$PR_HEAD`.
- **unresolved**: plausible, but needs missing RLinf version, GPU, checkpoint, or hardware; state what settles it.
- **dismissed**: cannot happen or is already satisfied; drop silently (never list in the output).

Merge findings with the same root cause into one finding listing affected locations. Assign severity strictly per [README.md § Findings](../README.md#findings): `critical` requires a concrete failure path (crash, wrong result, committed binary weights, unclosed Markdown fence, broken registration, or uncompletable workflow); whole-page docs readability failures, machine-translated Chinese, missing catalog rows, unpinned/local dependencies, or hardcoded paths are `major`; isolated wording/spacing issues are `minor`. Do not block Hub PRs over core-RLinf-only bureaucracy. If nothing survives, write `No findings.` and one line on what was checked.

## 8. Report

Keep the output tight and free of repetition: print the main comment, then each inline comment once, then a two-bullet check summary (not posted). Use English for publishable GitHub text unless asked otherwise.

- **Verdict**: bold recommendation (`Ready for senior review`, `Changes requested`, or `Blocked`) + severity counts + head/base SHA, then one short sentence on what blocks merge or why it is ready.
- **Reproduction**: two short bullets (under ~300 chars each). `Result:` starts with `**Passed**`, `**Failed**`, `**Partial**`, or `**Not run**` + one-sentence functional/metric conclusion. `Setup:` names only hardware/RLinf version and command run (omit host, OS, driver, venv paths, and SHA).
- **No duplicate findings**: the table indexes every finding (`F1`, `F2`, ...), sorted by severity then category. Write a `#### F<n>` section in the main comment **only for `Posted = here` findings**. `inline` findings live once in `### Inline comments`, and carried-forward replies on existing threads use `Posted = thread` (with no `####` section or new `comments[]` entry).
- **No trailing noise**: no `Dismissed:` list, no restated Goal/Idea/Changes/Risk bullets, and no tables of passing files.

````markdown
**<Recommendation>** · <n critical, n major, n minor, or no findings> · head `<sha7>` · base `main@<sha7>`

<One short sentence: what blocks merge, or why it is ready.>

### Reproduction

- Result: **<Passed | Failed | Partial | Not run>** — <one short sentence: CPU/GPU/benchmark outcome, or first blocker / what is missing>
- Setup: <hardware, RLinf version, and command run; or what a run needs if not run>

### Findings

| ID | Severity | Category | Location | Summary | Status | Posted |
|---|---|---|---|---|---|---|
| F1 | critical | correctness | `models/foo/foo/adapter.py:42` | <one line> | confirmed | inline |
| F2 | major | docs | `models/foo/README.zh-CN.md` | <one line> | confirmed | here |

#### F2 · major · docs: <plain title>

`models/foo/README.zh-CN.md`

<Problem and impact in 1–3 plain sentences.>

Suggested fix: <one sentence, plus code block if code changes.>

Code walkthrough:

<Quoted snippets under `path:line` lines, then input-to-failure steps. Omit when not about code.>

Evidence: <one line: command and result, or trace; for unresolved, what settles it.>
````

````markdown
### Inline comments (posted on diff lines)

`models/foo/foo/adapter.py:42`

**F1 · critical · correctness: <plain title>**

<Problem (1–3 sentences), `Suggested fix:` + verified `suggestion`/code block, and one-line `Evidence:`.>
````

````markdown
## Check summary (not posted)

- Checks: `route.py check` (<result>) · `lint_pr` (<result>) · tests (<command, hardware, result; or skipped + why>)
- Context: compared with <closest sibling or category README>; <any skipped check and why>
````

## 9. Post only when asked

Stop after step 8; never post by default. Skip this step for local diff reviews. When the user asks to post, update, or reply on GitHub, read [posting.md](posting.md) and run `lint_review.py lint` before posting. Approve only when explicitly asked.
