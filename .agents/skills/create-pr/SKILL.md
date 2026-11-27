---
name: create-pr
description: Open a GitHub pull request for RLinf-Hub, or fix an existing one — checks the PR title against Conventional Commits, writes a precise description following .github/PULL_REQUEST_TEMPLATE.md, checks DCO sign-off and area checks, and lints title and body before pushing. Use when asked to create, open, or submit a PR, write or rewrite a PR description, or fix a PR title or body.
---

# Create a PR

Write the title and description, then **run the linter before creating or updating the PR**:

```bash
python3 .agents/skills/create-pr/lint_pr.py lint \
    --title "feat(models): add smolvla inference adapter" \
    --body-file /tmp/pr-body.md
```

Exit code 1 means at least one ERROR — fix it and re-run. The same script checks an already-open PR:

```bash
python3 .agents/skills/create-pr/lint_pr.py lint --pr 2
```

## 1. Gather the facts before writing

Read the actual diff and commit log against `RLinf/RLinf-Hub:main`:

```bash
REMOTE=$(git remote -v | awk '/github\.com[:\/]RLinf\/RLinf-Hub(\.git)? \(fetch\)/ {print $1; exit}')
REMOTE=${REMOTE:-origin}
git fetch "$REMOTE" main
git log --oneline "$REMOTE/main..HEAD"
git diff --stat "$REMOTE/main...HEAD"
```

Verify:

- **Every commit carries a DCO sign-off** (`git commit -s` -> `Signed-off-by:`), which `.github/workflows/commit_check.yml` requires.
- **All area checks pass** (or explain in the PR body why a finding remains):

```bash
python3 .agents/skills/route.py check --base "$REMOTE/main"
```

- **Concrete facts for the body:** category and project path, upstream paper/repo/checkpoint link, tested `rlinf` version, exact commands run and outcomes (separating CPU contract tests, GPU smoke tests, and task-level benchmarks), explicit scope/limitations, and whether an AI assistant was used.

## 2. Title

```text
<type>(<scope>): <description>
```

- **type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`, `revert` (lowercase).
- **scope**: component or category touched — `algorithms`, `models`, `envs`, `robots`, `docs`, `skills`, `ci`, or the project name (`smolvla`). Lowercase `[a-z0-9_-]` only; optional — drop it rather than using a vague word like `new` or `misc`.
- **description**: **≤ 72 characters** after `: `, starts with a lowercase `a-z`, imperative mood (`add`, `fix`, `update`), no trailing period, plain ASCII, and no trailing `(#123)`.

## 3. Body

Start from the skeleton so all four template sections stay in order:

```bash
python3 .agents/skills/create-pr/lint_pr.py template > /tmp/pr-body.md
```

Fill every section, keeping all four `##` headings in order:

| Section | What goes in it |
|---|---|
| `## Description` | What changed, category/project path, upstream paper/repo/checkpoint link, linked issue (e.g., `Ref: RLinf/RLinf#1943`), and whether an AI assistant was used. ≤ 250 words, ≤ 12 bullets. Required. |
| `## Verification Evidence` | Tested `rlinf` version, hardware/environment, exact commands run (`route.py check`, `pytest`, GPU/Ray smoke, benchmarks), and outcomes. Separate CPU contract tests, GPU smoke tests, and task-level curves/demos. Warns if empty unless `--docs-only`. |
| `## Scope and Limitations` | What is supported today and what is explicitly out of scope (e.g., inference-only, required hardware/assets). |
| `## Checklist` | Tick every applicable box from `.github/PULL_REQUEST_TEMPLATE.md`. Required. |

Style rules enforced by `lint_pr.py`:

- **No uniform leading indentation** on headings, prose, or table rows.
- **Delete `<!-- ... -->` hints** once each section is written.
- **Nothing above the first `##` heading** — put intro text inside `## Description`.
- **One line per paragraph** so GitHub does not render unwanted line breaks.
- **Balanced fenced code blocks.**

Follow [docs/rules/english.md](../docs/rules/english.md) for direct, hype-free prose.

## 4. Lint, then create

```bash
python3 .agents/skills/create-pr/lint_pr.py lint \
    --title "$TITLE" --body-file /tmp/pr-body.md
```

Pass `--docs-only` for documentation-only PRs to skip the empty-verification warning, and `--quiet` to omit fix suggestions. Once it exits 0 and the user has approved creating the PR:

```bash
gh pr create --repo RLinf/RLinf-Hub --base main --title "$TITLE" --body-file /tmp/pr-body.md
```

## 5. Fixing an open PR

```bash
python3 .agents/skills/create-pr/lint_pr.py lint --pr 2
python3 .agents/skills/create-pr/lint_pr.py fix --pr 2 --unwrap > /tmp/fixed.md
python3 .agents/skills/create-pr/lint_pr.py lint --body-file /tmp/fixed.md
```

Inspect `/tmp/fixed.md` before posting it with `gh pr edit 2 --repo RLinf/RLinf-Hub --body-file /tmp/fixed.md`.

## Gotchas

- `template` intentionally fails its own lint until at least one checkbox in `## Checklist` is ticked.
- `###` subheadings stay inside their parent `##` section (for example `### Linux A100` inside `## Verification Evidence`). Renaming a top-level template heading triggers `section-missing`.
- `lint --pr N` uses `gh pr view` and is strictly read-only.
