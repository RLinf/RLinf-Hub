# AGENTS.md

This file tells coding agents how to add, test, and review contributions in RLinf-Hub. `CLAUDE.md` is a symlink to it, and [`.gemini/settings.json`](.gemini/settings.json) loads it for Gemini CLI. It holds only rules that apply across the repository; area guidance and checks live in skills under [`.agents/skills/`](.agents/skills/README.md). When this file disagrees with the repository layout or workflows, fix this file in the same change.

RLinf-Hub is the official community collection of embodied and agentic AI works built on [RLinf](https://github.com/RLinf/RLinf). Each contribution lives in a self-contained folder under `algorithms/<name>/`, `models/<name>/`, `envs/<name>/`, or `robots/<name>/`, integrates with RLinf through `RLINF_EXT_MODULE` (or a custom `EnvWorker` / launch script for simulators and agentic environments), and adds a row to the root catalog tables in `README.md` and `README.zh-CN.md`.

## Working with a human submitter

- A human submits and answers for every change. Push, open or edit PRs and issues, and post review comments only when the user asks for that action and has seen the content.
- Before starting a new integration or fix, check open PRs and issues in `RLinf/RLinf-Hub` and [RLinf/RLinf#1943](https://github.com/RLinf/RLinf/issues/1943) for overlap and tell the user.
- When a requirement is ambiguous or hardware/assets block verification, stop and ask. Do not leave `TODO(agent)` or placeholder commands in code or READMEs; record known limits in the PR description and the project README.
- Report results as they are: exact commands, hardware, RLinf version, and what passed, failed, or was skipped. Keep offline contract tests, GPU smoke tests, and task-level benchmarks distinct, and state in the PR description that an AI assistant was used.

## Repository map

- `algorithms/<name>/` – RL and post-training algorithms registered via `RLINF_EXT_MODULE` (`register_advantage`, `register_policy_loss`, `register_reward`).
- `models/<name>/` – VLA policies, World Action Models, world models, LLMs/VLMs, and reward/value models registered via `RLINF_EXT_MODULE` (`register_model`, `SupportedModel.register`).
- `envs/<name>/` – Simulators, manipulation/humanoid benchmarks, embodied-agent suites, and agentic RL environments (custom `EnvWorker` or launch script, plus `RLINF_EXT_MODULE` for companion modules).
- `robots/<name>/` – Real-world robot drivers, dexterous hands, and teleoperation interfaces registered via `RLINF_EXT_MODULE`.
- `README.md`, `README.zh-CN.md` – Root catalog tables indexing every accepted project in English and Chinese.
- `.agents/skills/` – Area and workflow skills, routing (`route.py`), and checks; `.claude/skills` symlinks here.
- `tests/skills/` – Offline CPU unit tests for the skill scripts.

## Commands

Run the area checks for all files changed against `RLinf/RLinf-Hub:main`:

```bash
python3 .agents/skills/route.py list
python3 .agents/skills/route.py check
```

Run the skill unit tests (offline CPU):

```bash
pytest tests/skills -v
```

Run a project's own offline tests from the repository root (example):

```bash
PYTHONPATH="$PWD/<category>/<name>" pytest -q <category>/<name>/tests
```

## Rules reviewers and CI enforce

- **Self-containment.** Keep each project completely inside `<category>/<project_name>/`, touching root files only to add its catalog row in `README.md` and `README.zh-CN.md`. Do not modify another project's folder or commit checkpoints, logs, outputs, or large media (`outputs/`, `logs/`, `wandb/`, `.pt`, `.safetensors`, `.ckpt`).
- **Standard project layout.** Every project folder provides `README.md`, `README.zh-CN.md`, `requirements.txt`, `configs/` (Hydra YAML configs or model fragments), and its Python package/entry script (`<module>/`), plus `tests/` when offline checks apply.
- **Dependencies and reproducibility.** `requirements.txt` layers only dependencies beyond `rlinf`, records the tested `rlinf` release or commit, pins any git dependency (`@<rev>`), and contains no local filesystem paths (`file://`, `/home/...`) or machine-specific wheel pins.
- **RLinf registration.** Out-of-tree algorithms, models, and robots register per process through `RLINF_EXT_MODULE` (exporting an idempotent `register()` function or registering on import) so every Ray worker sees them, without requiring edits to core `RLinf/RLinf`. Do not copy upstream model or simulator codebases when the upstream package can be installed and wrapped cleanly.
- **Accelerators and portability.** Prefer `Worker.torch_platform`, `self.torch_platform`, or `tensor.device` over hardcoded `torch.cuda` / `.cuda()` in runtime code. Never hardcode user home paths, GPU ordinals, hostnames, or credentials in code, configs, or scripts.
- **Headers and DCO.** Every new Python file starts with the Apache-2.0 header `# Copyright <year> The RLinf Authors.` (vendored files keep their upstream header). Every commit carries a `Signed-off-by:` trailer (`git commit -s`), enforced by `.github/workflows/commit_check.yml`.
- **Optional dependencies.** Import heavy or vendor-specific packages inside the function or branch that uses them when possible so registration, config loading, and offline CPU tests work cleanly.
- **Bilingual Markdown docs.** Every project ships paired `README.md` and `README.zh-CN.md` with install steps, registration/launch commands, tested RLinf version, scope/limitations, and expected outputs or results. Write Chinese natively rather than translating English sentence by sentence, and do not hard-wrap Chinese paragraphs.

## Quality bar for RLinf-Hub

RLinf-Hub keeps a lightweight merge bar compared to core `RLinf/RLinf`, while ensuring every component is:

- **High quality:** clean adapter code, static Hydra configs, explicit failure modes (raise `NotImplementedError` rather than silently fabricating metrics or logprobs), and offline contract tests that fail without the code.
- **Easy to run and reproduce:** copy-pasteable install and launch commands from a clean RLinf environment, pinned dependency versions, and honest verification evidence separating CPU contract checks, GPU smoke checks, and task-level curves or real-robot demos.
- **Easy to understand:** concise, direct English and native Chinese READMEs focused on what the user installs, configures, runs, and expects to see.

## Commits, PRs, and writing

- Commit subjects follow Conventional Commits (`<type>(<scope>): <description>`, imperative, e.g. `feat(models): add SmolVLA inference adapter`) and include `Signed-off-by:` (`git commit -s`).
- PR titles keep the description after `: ` at most 72 characters, starting with a lowercase letter, imperative mood, plain ASCII, no trailing period. Use `create-pr` to fill `.github/PULL_REQUEST_TEMPLATE.md` and run `python3 .agents/skills/create-pr/lint_pr.py lint --title "<title>" --body-file <body.md>`.
- All project writing—READMEs, PR descriptions, review comments, and commit messages—follows [english.md](.agents/skills/docs/rules/english.md) and [chinese.md](.agents/skills/docs/rules/chinese.md).

## Skills

Skills live in `.agents/skills/<name>/SKILL.md` ([.agents/skills/README.md](.agents/skills/README.md)). An area skill owns part of the repository: read it before editing files it owns, even when that edit is part of a larger change.

| Files | Skill |
|---|---|
| Python code, Hydra configs, shell scripts, tests, CI: `**/*.py`, `**/*.yaml`, `**/*.yml`, `**/*.sh`, `tests/**`, `.github/**` | `code` |
| Self-contained Hub submissions, dependencies, registration, catalog wiring: `algorithms/**`, `models/**`, `envs/**`, `robots/**`, `README.md`, `README.zh-CN.md` | `submission` |
| Documentation and READMEs: `README.md`, `README.zh-CN.md`, `algorithms/**/*.md`, `models/**/*.md`, `envs/**/*.md`, `robots/**/*.md` | `docs` |

| Task | Skill |
|---|---|
| Open a PR, or fix a PR title or description | `create-pr` |
| Review a PR (or local diff), or post review comments on it | `review-pr` |

Before reporting a change as done, run `python3 .agents/skills/route.py check`. Fix every critical or major finding, or explain to the user why it remains.

## Maintaining agent instructions

- Keep this file under 200 lines; put area-specific rules in `.agents/skills/`.
- Edit skills only under `.agents/skills/`; `.claude/skills` symlinks to it, `CLAUDE.md` symlinks to `AGENTS.md`, and `.gemini/settings.json` loads `AGENTS.md`.
- Every area skill declares `paths:` in its `SKILL.md` frontmatter and ships a `check.py` built on `route.py`, with offline tests in `tests/skills/`.
