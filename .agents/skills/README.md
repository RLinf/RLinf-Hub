# Project skills

This directory is the single source for RLinf-Hub's project skills. Codex, Cursor, and Gemini CLI discover `.agents/skills/` directly (and [`.gemini/settings.json`](../../.gemini/settings.json) loads [AGENTS.md](../../AGENTS.md)). Claude Code discovers the same skills through `.claude/skills -> ../.agents/skills`, and `CLAUDE.md` symlinks to [AGENTS.md](../../AGENTS.md). Edit skills only here and give each skill a folder whose name matches the `name` in its `SKILL.md`.

## Area skills and workflow skills

An area skill owns part of the repository. It tells an agent what to read before changing those files and checks the change afterwards, so the same standards apply while writing and reviewing a PR.

| Skill | Owns |
|---|---|
| [code](code/SKILL.md) | Python code, Hydra configs, shell scripts, tests, and CI: `**/*.py`, `**/*.yaml`, `**/*.yml`, `**/*.sh`, `tests/**`, `.github/**` |
| [submission](submission/SKILL.md) | Self-contained Hub submissions, dependencies, RLinf registration, catalog wiring, and artifacts: `algorithms/**`, `models/**`, `envs/**`, `robots/**`, `README.md`, `README.zh-CN.md` |
| [docs](docs/SKILL.md) | Bilingual Markdown documentation and catalog READMEs: `README.md`, `README.zh-CN.md`, `algorithms/**/*.md`, `models/**/*.md`, `envs/**/*.md`, `robots/**/*.md` |

A workflow skill acts on a pull request and calls the area skills.

| Skill | Does |
|---|---|
| [create-pr](create-pr/SKILL.md) | writes and lints a PR title and description against `.github/PULL_REQUEST_TEMPLATE.md`, after the area checks pass |
| [review-pr](review-pr/SKILL.md) | reviews a PR (or selected local diff), runs every touched area's check plus blind reproduction and docs readability passes, and posts the review after asking |

## The area skill contract

Every area skill has the same shape, so `route.py`, `create-pr`, and `review-pr` work with any of them without hardcoding area names.

- **`paths:`** in the frontmatter is a YAML block list of globs relative to the repository root. `*` matches within one directory and `**` spans directories; quote patterns that start with `*`. A file may belong to more than one area.
- **`description`** opens with the files and the action, because clients truncate long descriptions from the end.
- **Write** says what to read before editing and points to the rules by section. Each rule lives in one place: `code/patterns.md` for code, `submission/reference.md` for submission packaging and registration contracts, and `docs/rules/` for Markdown writing.
- **Check** is `check.py`, run as `python3 .agents/skills/<area>/check.py [--base REF] [--all-lines] [FILE ...]`. With no files, it checks the area's files that differ from the merge base of `--base` (default: `main` of the `RLinf/RLinf-Hub` remote), including uncommitted and untracked files. Line findings count only on lines the change adds unless `--all-lines` is passed. A checklist of judgment items follows in `SKILL.md` for what a script cannot decide.
- **Verify** (optional) covers runs that need RLinf environments, GPUs, checkpoints, simulators, or real-robot hardware.

## Findings

Every check prints one finding per line, most severe first, followed by a summary line:

```text
<severity> <path>[:<line>] <rule>: <message>
```

One severity scale holds across all checks and PR reviews:

- **critical**: wrong results, a crash, broken registration or config loading, committed secrets or huge binary artifacts, unclosed Markdown fences that swallow content, or a documented workflow that cannot be completed.
- **major**: a break with an area rule, missing required Hub files or catalog rows, unpinned or machine-specific dependencies, hardcoded local paths, missing Apache-2.0 headers, missing EN/ZH parity, unreadable/machine-translated docs, or missing verification evidence. Must change before merge.
- **minor**: a local fix such as naming, comments, or isolated wording and CJK spacing. Should change but does not block.

A check exits 1 when it reports any critical or major finding. A check that skips an optional step (such as Ruff when not installed) prints `skipped:` and the reason.

## Route a change

[route.py](route.py) maps changed files to the areas that own them and runs their checks:

```bash
python3 .agents/skills/route.py list    # touched areas, the SKILL.md to read, and their files
python3 .agents/skills/route.py check   # run each touched area's check
```

Both accept `--base REF`. Unowned files (such as `AGENTS.md` or skill definitions themselves) are listed as unrouted. The skills come from the checkout that holds `route.py`, and the repository under check is the current working directory, so a review can run the latest skills inside a worktree of any PR.

## Add a skill

Create `.agents/skills/<name>/SKILL.md` (`.claude/skills/<name>` resolves automatically through `.claude/skills -> ../.agents/skills`), add it to the tables here and in [AGENTS.md](../../AGENTS.md), and add offline unit tests in `tests/skills/`. An area skill must also declare `paths:` and ship `check.py` built on `route.check_parser`, `route.select`, and `route.report`; `route.py` refuses a skill that declares `paths:` without a check.

## If a skill is not recognized

Clients discover skills when a session starts, so restart the client after adding or renaming one. Any agent can also read a skill's `SKILL.md` by path and follow it directly.
